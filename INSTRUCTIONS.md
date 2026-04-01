# Umi-OCR AI Development Notes

This file captures the project-specific decisions that matter most for future AI-assisted edits.

## Release Packaging

- Build command: `python build_release.py`
- Version source of truth: `UmiOCR-data/about.json`
- Release artifact name is derived from `about.json`, not a hardcoded version string.
- Release package must include root `LICENSE`.
- Release package must not ship local `.settings` or `.pre_settings`.
- Release package must not ship `temp_doc`, logs, docs, or dev-only files.
- Release plugin whitelist is intentionally narrow. Only package:
  - `UmiOCR-data/plugins/AIOCR`
  - `UmiOCR-data/plugins/win7_x64_PaddleOCR-json_PP-OCRv5`
- If a new release should include different plugins, update the whitelist in `build_release.py` instead of copying the whole `plugins/` directory.

## Default OCR Behavior

- Global default OCR interface is configured in `UmiOCR-data/qt_res/qml/ApiManager/OcrManager.qml`.
- Current default OCR key: `win7_x64_PaddleOCR-json_PP-OCRv5`.
- UI label for that plugin comes from `UmiOCR-data/plugins/win7_x64_PaddleOCR-json_PP-OCRv5/paddleocr_config.py`.

## Default Settings Sources

- AIOCR local defaults live in `UmiOCR-data/plugins/AIOCR/ai_ocr_config.py`.
- Screenshot page defaults live in `UmiOCR-data/qt_res/qml/TabPages/ScreenshotOCR/ScreenshotOcrConfigs.qml`.
- Startup pre-config defaults live in `UmiOCR-data/py_src/utils/pre_configs.py`.
- Do not rely on `.settings` for first-run defaults. Those files are user-local and are excluded from release packages.

## AIOCR Markdown Notes

- Markdown-capable logic is implemented in `UmiOCR-data/plugins/AIOCR/ai_ocr.py`.
- `markdown_output = True` means AI OCR returns Markdown-oriented output.
- `markdown_inline_images = True` rewrites images to `data:` URIs for VS Code preview.
- `markdown_inline_images = False` rewrites images to local `file:///` paths, which is better for local Markdown tools.
- Runtime image output uses `UmiOCR-data/temp_doc/`, not repo-root `temp_doc/`.
- Local PP-StructureV3 now lives under AIOCR as provider key `pp_structure_v3_local`.
- The local provider reuses the existing AIOCR markdown parsing and image materialization path by returning online-style `layoutParsingResults[*].markdown` data from `pp_structure_v3_local_runner.py`.
- The local provider currently depends on a Python environment that already has `paddlepaddle` and `paddleocr[doc-parser]` installed. The override path is `pp_structure_v3_local_python_path`.
- The current repository implementation is validated for local/dev use. Release packaging does not yet bundle the PP-StructureV3 runtime into the distributable build.
- Local validation entry point: `temp_doc/validate_pp_structure_v3_local.py`.

## Screenshot History Notes

- Startup retention of screenshot history and `temp_doc` is controlled by `screenshot_persist_history` in `pre_configs.py`.
- Historical screenshot OCR records also persist image files under `temp_doc/screenshot_history`.

## Verification Checklist

- After changing defaults, verify the source default files rather than local `.settings`.
- After changing release logic, run `python build_release.py` and check:
  - output folder name matches `about.json`
  - `LICENSE` exists in release root
  - only `AIOCR` and `win7_x64_PaddleOCR-json_PP-OCRv5` exist under release `plugins/`
  - `.settings` and `.pre_settings` are absent from the release package
- If packaging fails or required assets are missing, `build_release.py` should surface a Windows popup.

## Editing Guidance

- Keep edits minimal and preserve existing QML/Python style.
- Prefer changing the actual default-source files over patching runtime-generated config.
- When changing release contents, fix the packaging logic at the root cause instead of deleting files after the build.