"""
AutoVideoCraft - Configuration Management
Handles loading, saving, and validating user configuration.
"""

import json
import os
from pathlib import Path
from typing import Optional
from loguru import logger

# Config file lives next to the project root
_BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_FILE = _BASE_DIR / "config.json"

# Provider presets (base_url -> OpenAI-compatible endpoint)
PROVIDER_PRESETS = {
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "智谱 GLM (Zhipu)": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
    },
    "阿里云百炼 (Qwen)": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-turbo",
    },
    "Moonshot (Kimi)": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
    },
    "字节豆包 (Doubao)": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-pro-4k",
    },
    "自定义 (Custom)": {
        "base_url": "",
        "default_model": "",
    },
}

# TTS Voice options
TTS_VOICES = {
    "晓晓 (zh-CN, 女声)": "zh-CN-XiaoxiaoNeural",
    "云希 (zh-CN, 男声)": "zh-CN-YunxiNeural",
    "晓伊 (zh-CN, 女声)": "zh-CN-XiaoyiNeural",
    "云健 (zh-CN, 男声)": "zh-CN-YunjianNeural",
    "HsiaoChen (zh-TW, 女声)": "zh-TW-HsiaoChenNeural",
    "Jenny (en-US, Female)": "en-US-JennyNeural",
    "Guy (en-US, Male)": "en-US-GuyNeural",
}

DEFAULT_CONFIG = {
    "llm": {
        "provider": "DeepSeek",
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "media": {
        "pexels_api_key": "",
        "pixabay_api_key": "",
        "preferred_source": "pexels",
        "video_orientation": "portrait",  # portrait | landscape
    },
    "tts": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "+0%",
        "volume": "+0%",
    },
    "video": {
        "fps": 24,
        "resolution": "1080x1920",  # portrait 9:16
        "subtitle_enabled": True,
        "subtitle_font_size": 48,
        "subtitle_color": "white",
        "subtitle_stroke_color": "black",
        "subtitle_stroke_width": 2,
        "subtitle_position": "bottom",
        "bg_music_enabled": False,
        "bg_music_volume": 0.15,
    },
}


def load_config() -> dict:
    """Load configuration from disk, merging with defaults."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Deep merge: defaults as base, saved values override
            merged = _deep_merge(DEFAULT_CONFIG, saved)
            return merged
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Config file corrupted, using defaults: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> bool:
    """Persist configuration to disk."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info("Configuration saved.")
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def update_config_section(section: str, updates: dict) -> dict:
    """Update a specific section of the config and save."""
    config = load_config()
    if section in config:
        config[section].update(updates)
    else:
        config[section] = updates
    save_config(config)
    return config


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_provider_preset(provider: str) -> dict:
    """Get preset config for a provider."""
    return PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["自定义 (Custom)"])


def validate_llm_config(config: dict) -> tuple[bool, str]:
    """Validate LLM configuration. Returns (is_valid, error_message)."""
    llm = config.get("llm", {})
    if not llm.get("api_key"):
        return False, "请先在【大模型设置】中填写 API Key"
    if not llm.get("base_url"):
        return False, "请先在【大模型设置】中填写 Base URL"
    if not llm.get("model"):
        return False, "请先在【大模型设置】中填写模型名称"
    return True, ""


def validate_media_config(config: dict) -> tuple[bool, str]:
    """Validate media API configuration."""
    media = config.get("media", {})
    source = media.get("preferred_source", "pexels")
    if source == "pexels" and not media.get("pexels_api_key"):
        return False, "请在【素材设置】中填写 Pexels API Key（免费申请）"
    if source == "pixabay" and not media.get("pixabay_api_key"):
        return False, "请在【素材设置】中填写 Pixabay API Key（免费申请）"
    return True, ""
