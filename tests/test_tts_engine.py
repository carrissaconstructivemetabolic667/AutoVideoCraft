"""Tests for TTS engine (subtitle conversion utilities)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from autovideocraft.utils import vtt_to_srt as _vtt_to_srt


def test_vtt_to_srt_basic():
    vtt = """WEBVTT

00:00:00.000 --> 00:00:02.500
Hello world

00:00:02.500 --> 00:00:05.000
This is a test
"""
    srt = _vtt_to_srt(vtt)
    assert "1\n" in srt
    assert "00:00:00,000 --> 00:00:02,500" in srt
    assert "Hello world" in srt
    assert "2\n" in srt
    assert "This is a test" in srt


def test_vtt_to_srt_replaces_dots_with_commas():
    vtt = "WEBVTT\n\n00:01:23.456 --> 00:01:25.789\nTest\n"
    srt = _vtt_to_srt(vtt)
    assert "00:01:23,456" in srt
    assert "00:01:25,789" in srt
    assert "." not in srt.split("-->")[0].split("\n")[-1]  # timestamp line uses commas
