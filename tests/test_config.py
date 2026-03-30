"""Tests for configuration management."""
import sys
import os
import json
import tempfile
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from autovideocraft.config import (
    DEFAULT_CONFIG,
    _deep_merge,
    validate_llm_config,
    validate_media_config,
    get_provider_preset,
    PROVIDER_PRESETS,
)


def test_deep_merge_basic():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99}}
    result = _deep_merge(base, override)
    assert result["a"] == 1
    assert result["b"]["c"] == 99
    assert result["b"]["d"] == 3


def test_deep_merge_new_key():
    base = {"a": 1}
    override = {"b": 2}
    result = _deep_merge(base, override)
    assert result["a"] == 1
    assert result["b"] == 2


def test_validate_llm_config_missing_key():
    config = {"llm": {"api_key": "", "base_url": "https://api.test.com/v1", "model": "test"}}
    ok, err = validate_llm_config(config)
    assert not ok
    assert "API Key" in err


def test_validate_llm_config_missing_url():
    config = {"llm": {"api_key": "sk-test", "base_url": "", "model": "test"}}
    ok, err = validate_llm_config(config)
    assert not ok
    assert "Base URL" in err


def test_validate_llm_config_valid():
    config = {"llm": {"api_key": "sk-test", "base_url": "https://api.test.com/v1", "model": "test"}}
    ok, err = validate_llm_config(config)
    assert ok
    assert err == ""


def test_validate_media_config_no_key():
    config = {"media": {"preferred_source": "pexels", "pexels_api_key": ""}}
    ok, err = validate_media_config(config)
    assert not ok
    assert "Pexels" in err


def test_validate_media_config_valid():
    config = {"media": {"preferred_source": "pexels", "pexels_api_key": "test_key"}}
    ok, err = validate_media_config(config)
    assert ok


def test_provider_presets_have_required_fields():
    for name, preset in PROVIDER_PRESETS.items():
        assert "base_url" in preset, f"Provider '{name}' missing base_url"
        assert "default_model" in preset, f"Provider '{name}' missing default_model"


def test_default_config_structure():
    for key in ["llm", "media", "tts", "video"]:
        assert key in DEFAULT_CONFIG, f"Default config missing section: {key}"
