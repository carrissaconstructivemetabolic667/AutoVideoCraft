# Changelog

All notable changes to AutoVideoCraft will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] - 2024-03-30

### Added
- Initial release 🎉
- Full video generation pipeline: LLM → TTS → Stock Media → Video composition
- Gradio Web UI with 5 tabs: Generate, LLM Settings, Media & TTS, Video Quality, About
- Support for 6+ LLM providers (DeepSeek, OpenAI, Zhipu, Qwen, Moonshot, Doubao, Custom)
- Microsoft Edge TTS integration — free, no API key required, 30+ voices
- Subtitle generation via Edge TTS SubMaker (word-level timestamps, no Whisper needed)
- FFmpeg auto-configuration using `imageio-ffmpeg` (cross-platform, no manual install)
- Pexels and Pixabay stock video API integration
- Smart video crop/resize to fit target resolution (portrait 9:16 default)
- One-click launchers: `start.bat` (Windows), `start.sh` (macOS/Linux)
- Unit tests for config and TTS utilities
- GitHub Actions CI workflow
- MIT License
