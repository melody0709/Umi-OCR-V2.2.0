# -*- coding: utf-8 -*-

import base64
import json
import os
import sys
import tempfile
import traceback
from io import BytesIO

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("PYTHONUTF8", "1")

PROTOCOL_OUT = sys.__stdout__
sys.stdout = sys.stderr

from PIL import Image
from paddleocr import PPStructureV3


def write_protocol(message):
    PROTOCOL_OUT.write(message + "\n")
    PROTOCOL_OUT.flush()


def decode_image(image_base64):
    payload = image_base64.strip()
    if payload.startswith("data:"):
        comma_index = payload.find(",")
        if comma_index < 0:
            raise ValueError("data URL 缺少分隔符")
        payload = payload[comma_index + 1 :]
    return base64.b64decode(payload)


def image_to_base64(image):
    buffer = BytesIO()
    if image.mode not in ("RGB", "RGBA", "L"):
        image = image.convert("RGBA")
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def materialize_input_image(image_base64):
    raw_bytes = decode_image(image_base64)
    image = Image.open(BytesIO(raw_bytes))
    fd, temp_path = tempfile.mkstemp(prefix="umi_pps_", suffix=".png")
    os.close(fd)
    image.save(temp_path, format="PNG")
    return temp_path


class LocalPPStructureRunner:
    def __init__(self):
        self.pipeline = None
        self.pipeline_signature = None

    def ensure_pipeline(self, init_options):
        signature = json.dumps(init_options, ensure_ascii=False, sort_keys=True)
        if self.pipeline is not None and self.pipeline_signature == signature:
            return

        self.pipeline = PPStructureV3(**init_options)
        self.pipeline_signature = signature

    def _to_markdown_result(self, item, pretty_markdown=True, show_formula_number=False):
        markdown_info = item._to_markdown(
            pretty=pretty_markdown,
            show_formula_number=show_formula_number,
        )

        markdown_images = {}
        for image_key, image_value in markdown_info.get("markdown_images", {}).items():
            if image_value is None:
                continue
            markdown_images[image_key] = image_to_base64(image_value)

        page_flags = markdown_info.get("page_continuation_flags") or (True, True)

        pruned_result = {}
        try:
            item_json = getattr(item, "json", None)
            if isinstance(item_json, dict):
                pruned_result = item_json.get("res") or {}
        except Exception:
            pruned_result = {}

        return {
            "prunedResult": pruned_result,
            "markdown": {
                "text": markdown_info.get("markdown_texts", ""),
                "images": markdown_images,
                "isStart": bool(page_flags[0]) if len(page_flags) >= 1 else True,
                "isEnd": bool(page_flags[1]) if len(page_flags) >= 2 else True,
            },
            "outputImages": None,
            "inputImage": None,
        }

    def infer(self, request):
        pipeline_init = dict(request.get("pipeline_init") or {})
        predict_options = dict(request.get("predict_options") or {})
        render_options = dict(request.get("render_options") or {})

        self.ensure_pipeline(pipeline_init)

        temp_path = materialize_input_image(request["image_base64"])
        try:
            output = self.pipeline.predict(temp_path, **predict_options)
            layout_parsing_results = []
            for item in output:
                layout_parsing_results.append(
                    self._to_markdown_result(
                        item,
                        pretty_markdown=render_options.get("prettify_markdown", True),
                        show_formula_number=render_options.get("show_formula_number", False),
                    )
                )
            return {
                "errorCode": 0,
                "errorMsg": "Success",
                "result": {
                    "layoutParsingResults": layout_parsing_results,
                },
            }
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass


def main():
    runner = LocalPPStructureRunner()
    write_protocol("PPSTRUCTURE_LOCAL_READY")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        request_id = "unknown"
        try:
            request = json.loads(line)
            request_id = request.get("request_id", request_id)
            command = request.get("cmd")

            if command == "shutdown":
                write_protocol(
                    json.dumps(
                        {"ok": True, "request_id": request_id, "result": {"status": "bye"}},
                        ensure_ascii=False,
                    )
                )
                break

            if command != "infer":
                raise ValueError(f"不支持的命令：{command}")

            result = runner.infer(request)
            write_protocol(
                json.dumps(
                    {"ok": True, "request_id": request_id, "result": result},
                    ensure_ascii=False,
                )
            )
        except Exception as exc:
            write_protocol(
                json.dumps(
                    {
                        "ok": False,
                        "request_id": request_id,
                        "error": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                    ensure_ascii=False,
                )
            )


if __name__ == "__main__":
    main()