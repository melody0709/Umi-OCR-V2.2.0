# diff.md — v2.2.0 源码修改说明

## v2.2.0 修改文件清单

### 1. Markdown 图片 HTTP 前缀

#### 1.1 `UmiOCR-data/plugins/AIOCR/ai_ocr_config.py`

**新增**：任务级设置 `markdown_http_server`

```python
"markdown_http_server": {
    "title": tr("Markdown 图片 HTTP 前缀"),
    "default": "http://127.0.0.1:28080?path=",
    "type": "text",
}
```

作用：当 `markdown_inline_images` 关闭时，可将 Markdown 图片链接改写为 `HTTP 前缀 + 绝对路径`；留空则保持 `file:///`。

#### 1.2 `UmiOCR-data/plugins/AIOCR/ai_ocr.py`

**新增**：HTTP 图片链接生成逻辑。

- `_get_markdown_http_server(config)`：读取并校验任务配置中的 HTTP 前缀。
- `_to_http_image_uri(abs_path, server_prefix)`：把本地绝对路径转成 HTTP 图片链接。
- `_materialize_markdown_images(...)`：在 `markdown_inline_images = False` 时，根据是否填写 HTTP 前缀决定输出 `file:///` 或 HTTP 链接。

#### 1.3 `UmiOCR-data/plugins/AIOCR/i18n.csv`

**新增**：`Markdown 图片 HTTP 前缀` 的多语言文案。

---

### 2. 自动托管轻量 HTTP 服务进程

#### 2.1 `UmiOCR-data/py_src/server/super_light_server_process.py`

**新增**：`SuperLightServerProcess` 进程管理器。

功能：

- 启动 `UmiOCR-data/bin/super_light_server.exe`
- Windows 下隐藏启动，不弹控制台窗口
- 退出时自动 `terminate` / `kill` 回收进程
- 缺失 exe 或非 Windows 平台时自动跳过

#### 2.2 `UmiOCR-data/py_src/run.py`

**修改**：在主程序生命周期中接入轻量 HTTP 服务。

```python
super_light_server = SuperLightServerProcess()
super_light_server.start()
try:
    runQml(engineAddImportPath)
finally:
    super_light_server.stop()
```

作用：Umi-OCR 启动时自动拉起后台 HTTP 服务，退出时自动关闭。

---

## 旧版说明（v2.1.9）

### 1. 截图历史保留开关与启动清理逻辑

#### 1.1 `UmiOCR-data/py_src/utils/pre_configs.py`

**新增**：`screenshot_persist_history` 预配置项

```python
"screenshot_persist_history": False,  # 截图历史记录与 temp_doc 保留
```

**兼容性修改**：读取旧版 `.pre_settings` 时，缺失的新键将自动保留默认值，不再抛出异常。

#### 1.2 `UmiOCR-data/py_src/utils/global_configs_connector.py`

**新增**：两个桥接接口，用于让 QML 全局设置与启动级预配置同步。

```python
@Slot(result=bool)
def getScreenshotPersistHistory(self):
    return bool(pre_configs.getValue("screenshot_persist_history"))

@Slot(bool)
def setScreenshotPersistHistory(self, flag):
    pre_configs.setValue("screenshot_persist_history", bool(flag))
```

#### 1.3 `UmiOCR-data/py_src/server/doc_server.py`

**修改**：启动文档服务时，不再无条件清空 `temp_doc`。

```python
if os.path.exists(UPLOAD_DIR):
    if not pre_configs.getValue("screenshot_persist_history"):
        shutil.rmtree(UPLOAD_DIR)
        os.makedirs(UPLOAD_DIR)
else:
    os.makedirs(UPLOAD_DIR)
```

#### 1.4 `UmiOCR-data/qt_res/qml/Configs/GlobalConfigs.qml`

**新增**：全局设置项 `screenshot.persistHistory`

```javascript
"persistHistory": {
    "title": qsTr("保留截图历史记录"),
    "default": globalConfigConn.getScreenshotPersistHistory(),
    "toolTip": qsTr("启用后，重启软件时保留截图页记录，并且启动时不清空 temp_doc；关闭后恢复现有逻辑，下次启动时清空。"),
}
```

---

### 2. 截图 OCR 历史记录持久化

#### 2.1 `UmiOCR-data/qt_res/qml/TabPages/ScreenshotOCR/ScreenshotOcrConfigs.qml`

**新增**：隐藏配置项 `historyRecords`，用于将截图页历史记录写入 `.settings`。

```javascript
"historyRecords": {
    "type": "var",
    "default": [],
},
```

#### 2.2 `UmiOCR-data/qt_res/qml/Widgets/ResultLayout/ResultsTableView.qml`

**新增**：历史记录的持久化读写能力。

- 初始化时从 `historyRecords` 读取已保存的 OCR 记录。
- 新增、编辑、删除记录时，会自动同步回配置。
- 写入采用 500ms 防抖，避免每次按键都直接落盘。

核心接口：

```javascript
function initPersistedHistory(configs, key, enabled)
function updatePersistHistory(enabled)
function savePersistedHistory()
function loadPersistedHistory()
```

#### 2.3 `UmiOCR-data/qt_res/qml/TabPages/ScreenshotOCR/ScreenshotOCR.qml`

**新增**：页面初始化时恢复历史记录，并在全局开关变化时同步切换持久化行为。

---

### 3. 截图文件历史与点击回显

#### 3.1 `UmiOCR-data/py_src/image_controller/image_provider.py`

**新增**：`saveImageToHistory()`

```python
def saveImageToHistory(fromPath, subdir="screenshot_history"):
    history_dir = os.path.abspath(os.path.join(".", "temp_doc", subdir))
    os.makedirs(history_dir, exist_ok=True)
    filename = f"{time.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.png"
    save_path = os.path.join(history_dir, filename)
```

作用：将内存中的截图保存到 `UmiOCR-data/temp_doc/screenshot_history/`，并返回规范化后的本地路径。

#### 3.2 `UmiOCR-data/py_src/image_controller/image_connector.py`

**新增**：QML 可调用接口 `saveImageToHistory()`。

#### 3.3 `UmiOCR-data/qt_res/qml/ImageManager/ImageManager.qml`

**新增**：对外暴露 `saveImageToHistory` 方法。

#### 3.4 `UmiOCR-data/qt_res/qml/Widgets/ResultLayout/ResultsTableView.qml`

**新增**：`itemActivated` 回调和 `activateItem()`。

记录面板中单击某条记录时，会把当前记录对象回传给页面层，而不仅仅是处理复制/选区逻辑。

#### 3.5 `UmiOCR-data/qt_res/qml/TabPages/ScreenshotOCR/ScreenshotOCR.qml`

**新增**：

- `resolveHistoryImagePath(imgID, imgPath)`：在新截图 OCR 完成时，将截图保存到历史目录。
- `showHistoryRecord(item)`：点击历史记录时，从 `source` 中解析 `historyImagePath`，并在左侧图片窗口展示对应截图与 OCR 文本框。

数据写入方式：

```javascript
res.imgPath = imgPath || ""
res.historyImagePath = resolveHistoryImagePath(imgID, imgPath)
```

---

## 旧版说明（v2.1.7）

## 修改文件清单

### 1. `UmiOCR-data/plugins/AIOCR/ai_ocr_config.py`

**位置**：`globalOptions` 字典，`a_provider` 之后、`a_timeout` 之前

**新增**：`a_provider2` 配置项（第二AI服务商下拉选择）

```python
"a_provider2": {
    "title": tr("第二AI服务商 (备用快捷键)"),
    "default": "openai",
    "optionsList": [ ... ],  # 与 a_provider 相同的 18 个服务商列表
    "toolTip": tr("选择备用AI服务商。配合第二快捷键使用，可与主服务商同时运行。"),
},
```

> 使用 `a_provider2` 作为键名是为了在 UI 中排序在 `a_timeout` 之前（QMap 按字母排序）。复用已有各服务商的 `api_key` / `model` / `api_base` 字段（如 `openai_api_key`），无需新增密钥配置项。

---

### 2. `UmiOCR-data/plugins/AIOCR/ai_ocr.py`

#### 2.1 `BaseProvider.__init__`（约第 31 行）

**修改**：新增 `self.provider_name = "unknown"` 属性

```python
def __init__(self, api_key, api_base=None, model=None, timeout=30, proxy_url=None):
    ...
    self.provider_name = "unknown"  # 新增：标识服务商名称
```

#### 2.2 `ProviderFactory.create_provider`（约第 1144 行）

**修改**：创建实例后设置 `provider_name`

```python
instance = provider_class(api_key, api_base, model, timeout, proxy_url)
instance.provider_name = provider_name  # 新增
return instance
```

#### 2.3 `Api.__init__`（约第 1395 行）

**新增**：`self.provider2 = None`

```python
def __init__(self, globalArgd):
    self.provider = None
    self.provider2 = None  # 新增：第二 provider 实例
    self.http_client = None
```

#### 2.4 `Api.start()`（约第 1457 行）

**新增**：初始化第二 provider 实例

```python
# 创建第二个Provider（备用快捷键用）
provider2_name = self.global_config.get("a_provider2", "openai")
api_key2 = self.global_config.get(f"{provider2_name}_api_key", "")
model2 = self.global_config.get(f"{provider2_name}_model", "")
api_base2 = self.global_config.get(f"{provider2_name}_api_base", "")

self.provider2 = None
if provider2_name and api_key2 and model2:
    try:
        self.provider2 = ProviderFactory.create_provider(
            provider2_name, api_key2, api_base2 if api_base2 else None, model2, timeout, proxy_url
        )
        print(f"AIOCR 备用服务商初始化完成: {provider2_name}")
    except Exception as e:
        print(f"AIOCR 备用服务商初始化失败: {e}")
```

#### 2.5 `Api.runBase64()`（约第 1970 行）

**修改**：根据 `use_provider2` 标识切换 provider

```python
def runBase64(self, imageBase64):
    original_provider = self.provider
    try:
        use_provider2 = self.local_config.get('use_provider2', False)
        if use_provider2 and self.provider2:
            self.provider = self.provider2
        # ... 原有逻辑不变 ...
    finally:
        self.provider = original_provider  # 恢复
```

#### 2.6 `Api._send_request()`（约第 2133 行）

**修复**：`provider_name` 从实例属性读取（修复备用快捷键 URL 构建错误）

```python
# 修复前（错误）：
provider_name = self.global_config.get("a_provider", ...)  # 始终读主服务商

# 修复后（正确）：
provider_name = getattr(self.provider, 'provider_name', 'unknown')  # 读实际实例
```

#### 2.7 `HTTPClient.post()` 异常信息增强（约第 1386 行）

**修改**：输出错误类型和详细信息

```python
except Exception as e:
    error_type = type(e).__name__
    error_msg = str(e) if str(e) else repr(e)
    raise Exception(f"HTTP请求失败 [{error_type}]: {error_msg}")
```

---

### 3. `UmiOCR-data/qt_res/qml/TabPages/ScreenshotOCR/ScreenshotOcrConfigs.qml`

**位置**：`"hotkey"` 组内，`reScreenshot` 之后

**新增**：两个备用快捷键配置

```javascript
"screenshot_alt": {
    "title": qsTr("屏幕截图 (备用AI)"),
    "toolTip": qsTr("使用第二AI服务商进行识别"),
    "type": "hotkey",
    "default": UmiAbout.app.system==="win32" ? "win+alt+x" : "alt+x",
    "eventTitle": "<<screenshot_alt>>",
},
"paste_alt": {
    "title": qsTr("粘贴图片 (备用AI)"),
    "toolTip": qsTr("使用第二AI服务商进行识别"),
    "type": "hotkey",
    "default": UmiAbout.app.system==="win32" ? "win+alt+b" : "alt+b",
    "eventTitle": "<<paste_alt>>",
},
```

---

### 4. `UmiOCR-data/qt_res/qml/TabPages/ScreenshotOCR/ScreenshotOCR.qml`

#### 4.1 `eventSub()`（约第 209 行）

**新增**：订阅备用快捷键事件

```javascript
qmlapp.pubSub.subscribeGroup("<<screenshot_alt>>", this, "screenshotAlt", ctrlKey)
qmlapp.pubSub.subscribeGroup("<<paste_alt>>", this, "pasteAlt", ctrlKey)
```

#### 4.2 新增函数

| 函数 | 作用 |
|------|------|
| `screenshotAlt()` | 备用截图，注入 `configDict["ocr.AIOCR.use_provider2"] = true` |
| `pasteAlt()` | 备用粘贴，注入 `configDict["ocr.AIOCR.use_provider2"] = true` |
| `ocrPathsAlt()` | 备用批量路径，注入 `configDict["ocr.AIOCR.use_provider2"] = true` |

---

### 5. `.gitignore`

**新增**：防止 API 密钥泄露

```
# 用户配置文件（含API密钥，不应提交到仓库）
UmiOCR-data/.settings
```

---

## 数据流

```
用户按下 Win+Alt+X
  → PubSub 发布 <<screenshot_alt>>
    → QML screenshotAlt()
      → configDict["ocr.AIOCR.use_provider2"] = true
        → Python ScreenshotOCR.ocrImgID(configDict)
          → MissionOCR.addMissionList(configDict)
            → AIOCR Api.start() 初始化双 provider
              → AIOCR Api.runBase64() 检测 use_provider2=true
                → self.provider = self.provider2
                  → _send_request() 从 provider.provider_name 读取第二服务商名
                    → 构建完整 URL 并发送请求
```
