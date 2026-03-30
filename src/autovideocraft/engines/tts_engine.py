"""
AutoVideoCraft - TTS Engine
Converts script text to speech using Microsoft Edge TTS (free, no API key required).
Also generates subtitle data (word-level timestamps) for accurate subtitle sync.
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Optional
from loguru import logger

import edge_tts
from edge_tts import SubMaker
from autovideocraft.utils import vtt_to_srt as _vtt_to_srt


class TTSEngine:
    """
    Text-to-speech engine using Microsoft Edge TTS.
    Generates MP3 audio and synchronized subtitle data simultaneously.
    """

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural", rate: str = "+0%", volume: str = "+0%"):
        """
        Args:
            voice: Edge TTS voice name (e.g. 'zh-CN-XiaoxiaoNeural').
            rate: Speed adjustment, e.g. '+20%' for faster, '-10%' for slower.
            volume: Volume adjustment, e.g. '+0%' for default.
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume
        logger.info(f"TTS Engine initialized: voice={voice}, rate={rate}, volume={volume}")

    async def _synthesize_async(
        self, text: str, audio_path: str, subtitle_path: Optional[str] = None
    ) -> dict:
        """
        Core async synthesis method.
        Returns dict with: audio_path, subtitle_path, duration_estimate.
        """
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
        )
        sub_maker = SubMaker()

        # Stream synthesis to get both audio and subtitle data
        with open(audio_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    sub_maker.create_sub(
                        (chunk["offset"], chunk["duration"]),
                        chunk["text"],
                    )

        # Save VTT subtitle if path provided
        if subtitle_path:
            vtt_content = sub_maker.generate_subs()
            with open(subtitle_path, "w", encoding="utf-8") as f:
                f.write(vtt_content)
            logger.debug(f"VTT subtitle saved: {subtitle_path}")

        # Also generate SRT format for FFmpeg compatibility
        srt_path = None
        if subtitle_path:
            srt_path = subtitle_path.replace(".vtt", ".srt")
            srt_content = _vtt_to_srt(sub_maker.generate_subs())
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

        logger.success(f"TTS synthesis complete: {audio_path}")
        return {
            "audio_path": audio_path,
            "subtitle_vtt": subtitle_path,
            "subtitle_srt": srt_path,
            "sub_maker": sub_maker,
        }

    def synthesize(
        self,
        text: str,
        output_dir: str,
        filename_prefix: str = "tts",
        progress_callback=None,
    ) -> dict:
        """
        Synthesize speech from text. Blocking wrapper around async method.

        Args:
            text: The script text to synthesize.
            output_dir: Directory to save output files.
            filename_prefix: Prefix for output files.
            progress_callback: Optional callable(message: str).

        Returns:
            dict with keys: audio_path, subtitle_vtt, subtitle_srt
        """
        if progress_callback:
            progress_callback("正在生成语音（Edge TTS）...")

        os.makedirs(output_dir, exist_ok=True)
        audio_path = os.path.join(output_dir, f"{filename_prefix}.mp3")
        subtitle_path = os.path.join(output_dir, f"{filename_prefix}.vtt")

        logger.info(f"Starting TTS synthesis: {len(text)} chars -> {audio_path}")

        result = asyncio.run(
            self._synthesize_async(text, audio_path, subtitle_path)
        )

        # Verify output
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            raise RuntimeError("TTS synthesis failed: audio file is empty or missing")

        return result

    @staticmethod
    async def list_voices(language_filter: str = "zh") -> list[dict]:
        """List all available TTS voices, optionally filtered by language."""
        voices = await edge_tts.list_voices()
        if language_filter:
            voices = [v for v in voices if language_filter.lower() in v["Locale"].lower()]
        return voices


# _vtt_to_srt is now in autovideocraft.utils — kept as alias for backward compat
# from autovideocraft.utils import vtt_to_srt as _vtt_to_srt  (already imported above)
