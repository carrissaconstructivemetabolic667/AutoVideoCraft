# 🎬 AutoVideoCraft

**AI 驱动的开源短视频自动生成工具** · Automated Short Video Generator Powered by AI

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org)
[![Gradio](https://img.shields.io/badge/UI-Gradio%204.x-orange?logo=gradio)](https://gradio.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/yourusername/AutoVideoCraft/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/AutoVideoCraft/actions)

---

**输入一个主题，自动生成带字幕的竖版短视频。** 无需命令行，浏览器网页操作，一键完成。

> 灵感来自 [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)，聚焦于开箱即用体验：**用户只需配置大模型 API，其余依赖（FFmpeg 等）全自动安装。**

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 📝 **AI 文案生成** | 接入 DeepSeek / OpenAI / 通义千问 / 智谱 GLM / Moonshot 等所有兼容 OpenAI 格式的大模型 |
| 🎙️ **免费 TTS 配音** | 使用微软 Edge TTS，30+ 种语音，无需额外 API Key |
| 🎬 **免版权素材** | 自动从 Pexels / Pixabay 搜索并下载匹配的视频素材 |
| 📑 **自动字幕** | Edge TTS 输出字幕时间戳，FFmpeg 精确压制，无需 Whisper |
| ⚙️ **自动安装 FFmpeg** | 使用 `imageio-ffmpeg`，跨平台自动配置，无需手动操作 |
| 🖥️ **Web UI** | 基于 Gradio，本地运行，无需任何服务器 |
| 📦 **一键启动** | 双击 `start.bat` / `start.sh`，自动安装依赖并打开浏览器 |

---

## 🖼️ 界面预览

```
┌──────────────────────────────────────────────────────┐
│  🎬 AutoVideoCraft                                   │
│  ┌────────────┬──────────┬─────────┬──────┬───────┐  │
│  │ 🎬 生成视频│🤖 大模型 │🎵 素材  │⚙️ 质量│ℹ️ 关于│  │
│  └────────────┴──────────┴─────────┴──────┴───────┘  │
│                                                      │
│  视频主题: [为什么天空是蓝色的        ]              │
│  时长: [───●──────] 30s  语言: [中文 ▼]              │
│                                                      │
│  [ ⚡ 一键生成视频 ]                                 │
│                                                      │
│  ┌──────────────────────┐  ┌───────────────────────┐ │
│  │  [视频播放器]        │  │ 标题：天空为什么是蓝的│ │
│  │  output_video.mp4    │  │ 文案：天空之所以是蓝色│ │
│  │  [⬇️ 下载视频]       │  │ 的，是因为瑞利散射...  │ │
│  └──────────────────────┘  └───────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 环境要求
- **Python 3.9+**（[下载](https://www.python.org/downloads/)，安装时勾选"Add to PATH"）
- 稳定的网络连接（用于下载素材和调用 API）

### Windows 用户

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/AutoVideoCraft.git
cd AutoVideoCraft

# 2. 双击启动（自动安装依赖 + 打开浏览器）
start.bat
```

### macOS / Linux 用户

```bash
git clone https://github.com/yourusername/AutoVideoCraft.git
cd AutoVideoCraft
chmod +x start.sh
./start.sh
```

### 手动安装（进阶）

```bash
git clone https://github.com/yourusername/AutoVideoCraft.git
cd AutoVideoCraft
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m autovideocraft.app
```

浏览器访问 **http://127.0.0.1:7860**

---

## ⚙️ 配置指南

### 第一步：配置大模型（必须）

打开 **[🤖 大模型设置]** 标签页：

| 服务商 | 推荐原因 | 获取 Key |
|--------|---------|---------|
| **DeepSeek** | 价格极低，效果出色 | [platform.deepseek.com](https://platform.deepseek.com) |
| **通义千问** | 国内访问稳定 | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) |
| **智谱 GLM** | 有免费额度 | [open.bigmodel.cn](https://open.bigmodel.cn) |
| **OpenAI** | 效果最好，较贵 | [platform.openai.com](https://platform.openai.com) |
| **自定义** | 支持任意 OpenAI 兼容接口 | - |

### 第二步：配置视频素材 API（必须）

打开 **[🎵 素材 & 配音]** 标签页：

- **Pexels API**（推荐）：免费注册 → [pexels.com/api](https://www.pexels.com/api/)
- **Pixabay API**：免费注册 → [pixabay.com/api/docs](https://pixabay.com/api/docs/)

### 第三步：一键生成

在 **[🎬 生成视频]** 标签页输入主题，点击 **⚡ 一键生成视频**。

---

## 🏗️ 项目架构

```
AutoVideoCraft/
├── src/
│   └── autovideocraft/
│       ├── app.py              # Gradio Web UI 主入口
│       ├── pipeline.py         # 视频生成流水线（编排各引擎）
│       ├── config.py           # 配置管理（加载/保存/校验）
│       ├── init_env.py         # 环境自动初始化（FFmpeg 等）
│       └── engines/
│           ├── llm_engine.py   # 大模型文案生成
│           ├── tts_engine.py   # Edge TTS 语音合成 + 字幕生成
│           ├── media_engine.py # Pexels/Pixabay 素材下载
│           └── video_engine.py # MoviePy + FFmpeg 视频合成
├── tests/                      # 单元测试
├── outputs/                    # 生成的视频（自动创建）
├── temp/                       # 临时工作目录（自动清理）
├── requirements.txt
├── start.bat                   # Windows 一键启动
├── start.sh                    # Linux/macOS 一键启动
└── pyproject.toml
```

### 工作流程

```
用户输入主题
    ↓
LLMEngine  →  生成文案 + 英文搜索关键词（JSON 格式）
    ↓
TTSEngine  →  Edge TTS 合成 MP3 音频 + VTT/SRT 字幕
    ↓
MediaEngine →  Pexels/Pixabay 搜索并下载 MP4 素材片段
    ↓
VideoEngine →  MoviePy 拼接裁剪 + FFmpeg 压制字幕
    ↓
输出 MP4 文件（存入 outputs/ 目录）
```

---

## 🔧 高级配置

### 环境变量（可选）

创建 `.env` 文件（不会被 git 追踪）：

```env
# 可选：通过环境变量预设配置（会被界面设置覆盖）
OPENAI_API_KEY=sk-xxx
PEXELS_API_KEY=xxx
```

### 自定义视频质量

在 **[⚙️ 视频质量]** 标签页调整：
- 分辨率：1080x1920（竖版）/ 1920x1080（横版）
- 字幕字号、颜色、位置

### 使用本地/私有大模型

选择 **"自定义"** 服务商，填入你的 Ollama / LocalAI / 任意 OpenAI 兼容接口地址：
```
Base URL: http://localhost:11434/v1
API Key:  ollama（随意填写）
Model:    llama3.2
```

---

## 🛣️ Roadmap

- [x] MVP：主题 → 文案 → TTS → 素材 → 视频合成
- [x] 自动 FFmpeg 安装（imageio-ffmpeg）
- [x] 字幕精确时间轴（Edge TTS SubMaker）
- [x] 多服务商大模型支持
- [ ] 背景音乐混入
- [ ] 批量生成（多主题队列）
- [ ] Whisper 语音识别字幕（替代方案）
- [ ] 多语言字幕翻译
- [ ] 视频模板系统
- [ ] Docker 一键部署

---

## 🤝 贡献指南

欢迎任何形式的贡献！

```bash
# Fork & Clone
git clone https://github.com/yourusername/AutoVideoCraft.git

# 创建功能分支
git checkout -b feature/my-feature

# 安装开发依赖
pip install -r requirements.txt
pip install pytest ruff

# 运行测试
pytest tests/ -v

# 提交 PR
```

代码规范：使用 `ruff check src/` 检查后再提交。

---

## ❓ 常见问题

**Q: 首次运行很慢？**  
A: 第一次运行需要安装 Python 依赖和下载 FFmpeg 二进制文件（约 50-100MB），之后会缓存。

**Q: 素材下载失败？**  
A: 检查 Pexels/Pixabay API Key 是否正确，以及网络是否能访问这些网站。

**Q: 生成的视频没有字幕？**  
A: 在 [⚙️ 视频质量] 中确认"启用字幕"已勾选，并确保 FFmpeg 已正确安装（查看启动日志）。

**Q: 支持哪些大模型？**  
A: 所有兼容 OpenAI Chat API 格式的模型均支持，包括国内外主流服务商。

**Q: 可以离线使用吗？**  
A: 大模型调用和素材下载需要网络。若使用本地大模型（Ollama）+ 本地素材，可实现完全离线。

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE)。

---

## 🌟 致谢

- [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) — 核心灵感来源
- [Gradio](https://gradio.app) — Web UI 框架
- [edge-tts](https://github.com/rany2/edge-tts) — 免费 TTS 引擎
- [MoviePy](https://zulko.github.io/moviepy/) — 视频处理库
- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) — 跨平台 FFmpeg 自动配置
- [Pexels](https://www.pexels.com) / [Pixabay](https://pixabay.com) — 免版权素材库

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

</div>
