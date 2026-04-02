<p align="left">
    <span>
        <b>中文</b>
    </span>
    <span> • </span>
    <a href="README_en.md">
        English
    </a>
</p>

<p align="center">
  <a href="https://github.com/melody0709/Umi-OCRV2.1.6">
    <img width="200" height="128" src="https://tupian.li/images/2022/10/27/icon---256.png" alt="Umi-OCR">
  </a>
</p>

<h1 align="center">Umi-OCR 文字识别工具（改版）</h1>

<p align="center">
  <a href="https://github.com/melody0709/Umi-OCRV2.1.6/releases/latest">
    <img src="https://img.shields.io/github/v/release/melody0709/Umi-OCRV2.1.6?style=flat-square" alt="Release">
  </a>
  <a href="#下载">
    <img src="https://img.shields.io/github/downloads/melody0709/Umi-OCRV2.1.6/total?style=flat-square" alt="Downloads">
  </a>
</p>

<div align="center">
  <h3>
    <a href="#本版本特色功能">
      特色功能
    </a>
    <span> • </span>
    <a href="#核心功能">
      核心功能
    </a>
    <span> • </span>
    <a href="#下载">
      下载地址
    </a>
    <span> • </span>
    <a href="#调用接口">
      接口文档
    </a>
  </h3>
</div>
<br>

> 📌 **当前定制版最新版本为 v2.2.0**，基于原版 v2.1.5 持续修改，在保留原有核心功能的基础上，新增多项实用特性。
> 
> 🔗 **原版仓库**：[hiroi-sora/Umi-OCR](https://github.com/hiroi-sora/Umi-OCR) | [原版使用说明](https://github.com/hiroi-sora/Umi-OCR#readme)

---

## 本版本特色功能

### 🌐 Markdown 图片 HTTP 服务（v2.2.0）

- **新增任务级设置 `Markdown 图片 HTTP 前缀`**：默认预设为 `http://127.0.0.1:28080?path=`
- **Markdown 图片可改写为 HTTP 链接**：当关闭“Markdown 图片内嵌”且前缀非空时，图片链接会改写为 `HTTP 前缀 + 绝对路径`
- **内置轻量 HTTP 服务自动托管**：打包版自带 `UmiOCR-data/bin/super_light_server.exe`，软件启动时自动后台启动，退出时自动回收

### 📸 截图历史记录（v2.1.9）

- **全局设置「保留截图历史记录」开关**：
  - 开启后，重启软件时保留截图页 OCR 历史记录，启动时不再清空 `temp_doc`
  - 关闭后，恢复原有逻辑；下次启动时清空截图历史和 `temp_doc`
- **截图文件同步保存**：
  - 截图图片将保存到 `UmiOCR-data/temp_doc/screenshot_history/`
  - 点击历史 OCR 记录时，左侧预览窗口会自动切换到对应截图，并恢复该条记录的 OCR 文本框

### 📝 Markdown 图片内嵌与保留（v2.1.8）

保留并落地在线版面解析返回的图片（支持 PaddleOCR-VL / PaddleOCR-VL-1.5 / PP-StructureV3）。

- 图片保存至 `UmiOCR-data/temp_doc/ai_ocr_markdown/<请求目录>/page_xxxx/...`
- **Markdown 图片内嵌开关**（任务级设置）：
  - **开启**：将图片改写为 base64 data URI（兼容 VSCode Markdown Preview Enhanced）
  - **关闭**：HTTP 前缀留空时使用本地 `file:///` 链接；填写 `Markdown 图片 HTTP 前缀` 后改写为 HTTP 链接
- 修复了在线 API 返回的 Markdown 图片在复制/快速识别路径中丢失的问题

### 🤖 双AI服务商 + 备用快捷键（v2.1.7）

支持同时配置两个不同的AI服务商，分别绑定独立快捷键。

- 全局设置新增「第二AI服务商 (备用快捷键)」选项
- 新增快捷键 `Win+Alt+X`（备用截图识别）和 `Win+Alt+B`（备用粘贴识别）
- 两个服务商各自独立初始化，可同时运行互不干扰

### 🎯 截图编辑模式（v2.1.6）

截图后不会立即识别，而是保留选区框，允许微调后再确认。

- **八角拖拽手柄**：选区四角和四边中点均可拖拽调整大小
- **选区移动**：拖拽选区内部可移动整个选区位置
- **确认方式**：双击选区内部 或 按 `Enter` 键
- **取消方式**：按 `Esc` 键 或 右键点击

该功能可有效避免因选区不精确而需要重新截图的问题。

---

## 默认集成与引擎说明

### 默认集成插件

本版本默认集成 **`win7_x64_PaddleOCR-json_PP-OCRv5`** 插件，开箱即用，无需额外配置。

### PP-StructureV3 本地运行说明

- 已在本地 Python 3.12 环境中跑通 **PP-StructureV3（CPU 版本）**
- 由于 runtime 集成尝试失败，该引擎 **未打包进 release 版本**
- 如需使用 PP-StructureV3，请自行配置本地 Python 3.12 运行环境

---

## 工程结构

```
Umi-OCR
├─ Umi-OCR.exe                    # 主程序入口
└─ UmiOCR-data/
   ├─ main.py                     # Python 主入口
   ├─ version.py                  # 版本信息
   ├─ .pre_settings               # 启动预配置
   ├─ .settings                   # 用户设置
   ├─ runtime/                    # Python 3.8 运行环境（Win7 x64）
   ├─ py_src/                     # Python 源码
   ├─ qt_res/                     # Qt 资源文件（图标、QML 等）
   ├─ plugins/                    # OCR 插件目录
   │  ├─ win7_x64_PaddleOCR-json_PP-OCRv5/  # 默认集成插件（开箱即用）
   │  └─ AIOCR/                   # AI OCR 在线服务插件
   ├─ i18n/                       # 多语言翻译文件
   ├─ themes.json                 # 主题配置
   └─ temp_doc/                   # 临时文档目录
      ├─ screenshot_history/      # 截图历史记录
      └─ ai_ocr_markdown/         # AI OCR Markdown 图片
```

支持的离线 OCR 引擎：

- [PaddleOCR-json](https://github.com/hiroi-sora/PaddleOCR-json)
- [RapidOCR-json](https://github.com/hiroi-sora/RapidOCR-json)

---

## 默认集成与引擎说明

### 默认集成插件

本版本默认集成 **`win7_x64_PaddleOCR-json_PP-OCRv5`** 插件，开箱即用，无需额外配置。

### PP-StructureV3 本地运行说明

- 已在本地 Python 3.12 环境中跑通 **PP-StructureV3（CPU 版本）**
- 由于 runtime 集成尝试失败，该引擎 **未打包进 release 版本**
- 如需使用 PP-StructureV3，请自行配置本地 Python 3.12 运行环境

---

## 核心功能

> 以下功能继承自原版 Umi-OCR，更多详细说明请查看 [原版文档](https://github.com/hiroi-sora/Umi-OCR#readme)。

### 截图OCR

- 快捷键截图，识别图中的文字
- 左侧图片预览栏可直接鼠标划选复制
- 右侧识别记录栏可编辑文字，允许划选多个记录复制
- 支持粘贴图片进行识别
- 支持 [公式识别](https://github.com/hiroi-sora/Umi-OCR/issues/254)

#### 文本后处理

OCR 结果排版解析方案，使文本更适合阅读：

- `多栏-按自然段换行`：适合大部分情景
- `多栏-总是换行` / `多栏-无换行`
- `单栏-按自然段换行` / `总是换行` / `无换行`
- `单栏-保留缩进`：适用于代码截图
- `不做处理`：OCR 引擎原始输出

所有方案均支持横排和竖排（从右到左）排版。

---

### 批量OCR

- 支持格式：`jpg, jpe, jpeg, jfif, png, webp, bmp, tif, tiff`
- 输出格式：`txt, jsonl, md, csv(Excel)`
- 支持 `文本后处理` 功能
- 无数量上限，支持任务完成后自动关机/待机
- 支持 `忽略区域` 功能，排除图片中不想要的文字（如水印）

---

### 文档识别

- 支持格式：`pdf, xps, epub, mobi, fb2, cbz`
- 对扫描件进行 OCR，或提取原有文本
- 可输出为 **双层可搜索 PDF**
- 支持设定忽略区域，排除页眉页脚文字

---

### 二维码

**扫码**：
- 截图/粘贴/拖入本地图片，读取二维码、条形码
- 支持一图多码，19种协议

**生成码**：
- 输入文本，生成二维码图片
- 支持 19 种协议和纠错等级等参数

---

### 全局设置

- 添加快捷方式 / 开机自启
- 切换界面 **语言**（繁中、英语、日语等）
- 切换界面 **主题**（多个亮/暗主题）
- 调整文字大小和字体
- 切换 OCR 插件
- 渲染器调整（解决截屏闪烁、UI 错位等问题）

---

## 下载

### 本版本

- **GitHub Releases**：https://github.com/melody0709/Umi-OCRV2.1.6/releases/latest

### 原版 Umi-OCR

如需原版或其他版本，请访问：

- **原版仓库**：https://github.com/hiroi-sora/Umi-OCR/releases/latest

---


## 更新日志

详细更新内容请查看 [CHANGE_LOG.md](CHANGE_LOG.md)

### 近期版本

- **v2.2.0** `2026.4.2` - Markdown 图片 HTTP 前缀、内置轻量 HTTP 服务自动启停
- **v2.1.9** `2026.4.1` - 截图历史记录、保留截图历史开关
- **v2.1.8** `2026.4.1` - Markdown 图片内嵌与保留
- **v2.1.7** `2026.4.1` - 双AI服务商 + 备用快捷键
- **v2.1.6** `2026.3.31` - 截图编辑模式

---


## 关于原版

原版 Umi-OCR 由 [hiroi-sora](https://github.com/hiroi-sora) 开发和维护，是一款免费、开源、可批量的离线 OCR 软件。

- [原版仓库](https://github.com/hiroi-sora/Umi-OCR)
- [原版赞助](https://afdian.com/a/hiroi-sora)
