# diff.md — v2.1.7 源码修改说明

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
