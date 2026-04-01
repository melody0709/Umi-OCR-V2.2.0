# -*- coding: utf-8 -*-

import atexit
import json
import os
import subprocess
import time
import uuid
from collections import deque
from sys import platform as sysPlatform
import threading


READY_SENTINEL = "PPSTRUCTURE_LOCAL_READY"


class PPStructureV3LocalClient:
    def __init__(self, python_executable, runner_script, startup_timeout=600):
        self.python_executable = os.path.abspath(python_executable)
        self.runner_script = os.path.abspath(runner_script)
        self.startup_timeout = startup_timeout
        self.process = None
        self._stderr_buffer = deque(maxlen=200)
        self._stderr_thread = None
        self._io_lock = threading.Lock()

    def start(self):
        if self.process is not None and self.process.poll() is None:
            return

        if not os.path.isfile(self.python_executable):
            raise RuntimeError(f"未找到本地 PP-StructureV3 Python：{self.python_executable}")
        if not os.path.isfile(self.runner_script):
            raise RuntimeError(f"未找到本地 PP-StructureV3 runner：{self.runner_script}")

        self.stop()

        startupinfo = None
        creationflags = 0
        if "win32" in str(sysPlatform).lower():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        env.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

        self.process = subprocess.Popen(
            [self.python_executable, self.runner_script],
            cwd=os.path.dirname(self.runner_script),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            creationflags=creationflags,
            env=env,
        )
        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_thread.start()

        deadline = time.time() + self.startup_timeout
        while True:
            if self.process.poll() is not None:
                stderr_tail = self.get_stderr_tail()
                raise RuntimeError(
                    "本地 PP-StructureV3 runner 启动失败。"
                    + (f"\n{stderr_tail}" if stderr_tail else "")
                )

            line = self.process.stdout.readline()
            if not line:
                if time.time() > deadline:
                    stderr_tail = self.get_stderr_tail()
                    self.stop()
                    raise RuntimeError(
                        "等待本地 PP-StructureV3 runner 启动超时。"
                        + (f"\n{stderr_tail}" if stderr_tail else "")
                    )
                time.sleep(0.05)
                continue

            if line.strip() == READY_SENTINEL:
                break

        atexit.register(self.stop)

    def _drain_stderr(self):
        if not self.process or not self.process.stderr:
            return
        try:
            for line in self.process.stderr:
                text = line.rstrip()
                if text:
                    self._stderr_buffer.append(text)
        except Exception:
            pass

    def get_stderr_tail(self, max_lines=30):
        if not self._stderr_buffer:
            return ""
        return "\n".join(list(self._stderr_buffer)[-max_lines:])

    def infer(self, image_base64, pipeline_init=None, predict_options=None, render_options=None):
        self.start()
        request_id = uuid.uuid4().hex
        payload = {
            "cmd": "infer",
            "request_id": request_id,
            "image_base64": image_base64,
            "pipeline_init": pipeline_init or {},
            "predict_options": predict_options or {},
            "render_options": render_options or {},
        }

        with self._io_lock:
            try:
                self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
                self.process.stdin.flush()
            except Exception as exc:
                stderr_tail = self.get_stderr_tail()
                self.stop()
                raise RuntimeError(
                    f"向本地 PP-StructureV3 runner 发送请求失败：{exc}"
                    + (f"\n{stderr_tail}" if stderr_tail else "")
                )

            line = self.process.stdout.readline()

        if not line:
            stderr_tail = self.get_stderr_tail()
            self.stop()
            raise RuntimeError(
                "本地 PP-StructureV3 runner 未返回结果。"
                + (f"\n{stderr_tail}" if stderr_tail else "")
            )

        try:
            response = json.loads(line)
        except Exception as exc:
            stderr_tail = self.get_stderr_tail()
            raise RuntimeError(
                f"解析本地 PP-StructureV3 runner 响应失败：{exc}"
                + (f"\n原始响应：{line.strip()}" if line.strip() else "")
                + (f"\n{stderr_tail}" if stderr_tail else "")
            )

        if response.get("request_id") != request_id:
            raise RuntimeError("本地 PP-StructureV3 runner 返回了不匹配的请求 ID。")

        if not response.get("ok"):
            stderr_tail = self.get_stderr_tail()
            message = response.get("error") or "本地 PP-StructureV3 推理失败。"
            if stderr_tail:
                message += f"\n{stderr_tail}"
            raise RuntimeError(message)

        return response.get("result")

    def stop(self):
        if self.process is None:
            return

        try:
            if self.process.poll() is None and self.process.stdin:
                try:
                    self.process.stdin.write(
                        json.dumps({"cmd": "shutdown", "request_id": "shutdown"}, ensure_ascii=False)
                        + "\n"
                    )
                    self.process.stdin.flush()
                except Exception:
                    pass
                try:
                    self.process.wait(timeout=2)
                except Exception:
                    self.process.kill()
        finally:
            self.process = None
            self._stderr_thread = None
            try:
                atexit.unregister(self.stop)
            except Exception:
                pass
