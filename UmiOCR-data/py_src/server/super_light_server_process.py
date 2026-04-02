# -*- coding: utf-8 -*-

import atexit
import importlib
import os
import subprocess
from sys import platform as sysPlatform

logger = importlib.import_module("umi_log").logger


class SuperLightServerProcess:
    """托管 super_light_server.exe 的生命周期。"""

    def __init__(self, executable_path=None, startup_check_timeout=0.2):
        self.executable_path = os.path.abspath(
            executable_path or os.path.join(".", "bin", "super_light_server.exe")
        )
        self.startup_check_timeout = startup_check_timeout
        self.process = None

    def start(self):
        if self.process is not None and self.process.poll() is None:
            return True

        if "win32" not in str(sysPlatform).lower():
            logger.debug("当前平台不是 Windows，跳过 super_light_server 自动启动。")
            return False

        if not os.path.isfile(self.executable_path):
            logger.debug(
                f"未找到 super_light_server 程序，跳过自动启动：{self.executable_path}"
            )
            return False

        self.stop()

        startupinfo = None
        creationflags = 0
        if "win32" in str(sysPlatform).lower():
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            self.process = subprocess.Popen(
                [self.executable_path],
                cwd=os.path.dirname(self.executable_path),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        except Exception:
            logger.error(
                f"启动 super_light_server 失败：{self.executable_path}",
                exc_info=True,
                stack_info=True,
            )
            self.process = None
            return False

        try:
            self.process.wait(timeout=self.startup_check_timeout)
        except subprocess.TimeoutExpired:
            atexit.register(self.stop)
            logger.info(f"已启动 Markdown 图片 HTTP 服务：{self.executable_path}")
            return True

        exit_code = self.process.returncode
        self.process = None
        logger.warning(
            f"Markdown 图片 HTTP 服务启动后立即退出。退出码：{exit_code}"
        )
        return False

    def stop(self):
        if self.process is None:
            return

        process = self.process
        self.process = None
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except Exception:
                    process.kill()
                    try:
                        process.wait(timeout=1)
                    except Exception:
                        pass
                logger.info("已停止 Markdown 图片 HTTP 服务。")
            else:
                logger.debug(
                    f"Markdown 图片 HTTP 服务已退出。退出码：{process.returncode}"
                )
        except Exception:
            logger.error("停止 super_light_server 失败。", exc_info=True, stack_info=True)
        finally:
            try:
                atexit.unregister(self.stop)
            except Exception:
                pass