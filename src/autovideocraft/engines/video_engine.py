"""
AutoVideoCraft - Video Engine
Handles video composition: clip concatenation, audio mixing, subtitle burning.
Uses MoviePy for Python-level processing and FFmpeg for subtitle rendering.
"""

import os
import subprocess
import random
import math
from pathlib import Path
from typing import Optional
from loguru import logger

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    TextClip,
    ColorClip,
)
from moviepy.video.fx.all import resize, crop


class VideoEngine:
    """
    Video composition engine for short-form content generation.
    """

    def __init__(
        self,
        fps: int = 24,
        resolution: str = "1080x1920",
        subtitle_enabled: bool = True,
        subtitle_font_size: int = 48,
        subtitle_color: str = "white",
        subtitle_stroke_color: str = "black",
        subtitle_stroke_width: int = 2,
        subtitle_position: str = "bottom",
    ):
        # Parse resolution
        width, height = map(int, resolution.split("x"))
        self.width = width
        self.height = height
        self.fps = fps
        self.subtitle_enabled = subtitle_enabled
        self.subtitle_font_size = subtitle_font_size
        self.subtitle_color = subtitle_color
        self.subtitle_stroke_color = subtitle_stroke_color
        self.subtitle_stroke_width = subtitle_stroke_width
        self.subtitle_position = subtitle_position

        logger.info(f"Video Engine initialized: {width}x{height} @ {fps}fps")

    def compose(
        self,
        video_clips: list[str],
        audio_path: str,
        subtitle_srt: Optional[str],
        output_path: str,
        progress_callback=None,
    ) -> str:
        """
        Compose the final video from clips, audio, and optional subtitles.

        Args:
            video_clips: List of local video file paths.
            audio_path: Path to the TTS audio file.
            subtitle_srt: Optional path to SRT subtitle file.
            output_path: Output video file path.
            progress_callback: Optional callable(message: str).

        Returns:
            Path to the output video file.
        """
        if progress_callback:
            progress_callback("正在合成视频...")

        if not video_clips:
            raise ValueError("No video clips provided")

        # Step 1: Load audio to get duration
        if progress_callback:
            progress_callback("加载音频文件...")
        audio = AudioFileClip(audio_path)
        target_duration = audio.duration
        logger.info(f"Target video duration: {target_duration:.2f}s")

        # Step 2: Load, resize and prepare video clips
        if progress_callback:
            progress_callback("处理视频素材（裁切 & 缩放）...")
        prepared_clips = self._prepare_clips(video_clips, target_duration)

        # Step 3: Concatenate clips to match audio length
        if progress_callback:
            progress_callback("拼接视频片段...")
        combined = self._concat_to_duration(prepared_clips, target_duration)

        # Step 4: Mix in audio
        if progress_callback:
            progress_callback("合并音频...")
        final_video = combined.set_audio(audio)

        # Step 5: Write intermediate video (without subtitles)
        if progress_callback:
            progress_callback("渲染视频文件（可能需要1-2分钟）...")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        temp_path = output_path.replace(".mp4", "_nosub.mp4")

        final_video.write_videofile(
            temp_path,
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=temp_path.replace(".mp4", "_temp_audio.m4a"),
            remove_temp=True,
            verbose=False,
            logger=None,
        )

        # Release resources
        audio.close()
        final_video.close()
        combined.close()
        for c in prepared_clips:
            try:
                c.close()
            except Exception:
                pass

        # Step 6: Burn subtitles with FFmpeg (much faster than MoviePy TextClip)
        if self.subtitle_enabled and subtitle_srt and os.path.exists(subtitle_srt):
            if progress_callback:
                progress_callback("压制字幕...")
            self._burn_subtitles_ffmpeg(temp_path, subtitle_srt, output_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)
        else:
            os.rename(temp_path, output_path)

        if not os.path.exists(output_path):
            raise RuntimeError(f"Video composition failed: output file not found at {output_path}")

        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.success(f"Video composed: {output_path} ({file_size_mb:.1f} MB)")
        return output_path

    def _prepare_clips(self, clip_paths: list[str], target_duration: float) -> list[VideoFileClip]:
        """Load and resize clips to the target resolution with smart cropping."""
        prepared = []
        for path in clip_paths:
            try:
                clip = VideoFileClip(path)
                clip = self._smart_resize(clip)
                prepared.append(clip)
                logger.debug(f"Prepared clip: {path} ({clip.duration:.1f}s)")
            except Exception as e:
                logger.warning(f"Failed to load clip {path}: {e}")
                continue

        if not prepared:
            raise RuntimeError("No valid video clips could be loaded")
        return prepared

    def _smart_resize(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Resize and crop a clip to fit the target resolution while maintaining aspect ratio.
        Uses center-crop to avoid black bars.
        """
        target_w, target_h = self.width, self.height
        target_ratio = target_w / target_h
        clip_ratio = clip.w / clip.h

        if clip_ratio > target_ratio:
            # Clip is wider than target: scale by height, then crop width
            new_h = target_h
            new_w = int(clip_ratio * new_h)
        else:
            # Clip is taller than target: scale by width, then crop height
            new_w = target_w
            new_h = int(new_w / clip_ratio)

        clip = clip.resize((new_w, new_h))
        # Center crop
        x_center = new_w / 2
        y_center = new_h / 2
        clip = clip.crop(
            x_center=x_center,
            y_center=y_center,
            width=target_w,
            height=target_h,
        )
        return clip

    def _concat_to_duration(
        self, clips: list[VideoFileClip], target_duration: float
    ) -> VideoFileClip:
        """
        Concatenate clips cyclically until target duration is reached, then trim.
        """
        total = 0.0
        selected = []

        while total < target_duration:
            remaining = target_duration - total
            for clip in clips:
                if total >= target_duration:
                    break
                use_duration = min(clip.duration, remaining)
                sub = clip.subclip(0, use_duration)
                selected.append(sub)
                total += use_duration
                remaining = target_duration - total

        result = concatenate_videoclips(selected, method="compose")
        return result.subclip(0, target_duration)

    def _burn_subtitles_ffmpeg(
        self, input_path: str, srt_path: str, output_path: str
    ) -> None:
        """
        Burn SRT subtitles into video using FFmpeg (hardware-accelerated where possible).
        """
        # Escape path for FFmpeg subtitle filter (Windows paths need special handling)
        escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")

        # Build subtitle style
        font_size = self.subtitle_font_size
        color = self._color_to_ass(self.subtitle_color)
        stroke_color = self._color_to_ass(self.subtitle_stroke_color)
        stroke_width = self.subtitle_stroke_width

        # Vertical position: bottom=10%, middle=50%
        margin_v = int(self.height * 0.08) if self.subtitle_position == "bottom" else int(self.height * 0.45)

        subtitle_filter = (
            f"subtitles='{escaped_srt}':force_style='"
            f"FontSize={font_size},"
            f"PrimaryColour={color},"
            f"OutlineColour={stroke_color},"
            f"Outline={stroke_width},"
            f"Alignment=2,"
            f"MarginV={margin_v}'"
        )

        ffmpeg_exe = os.environ.get("IMAGEIO_FFMPEG_EXE", "ffmpeg")
        cmd = [
            ffmpeg_exe,
            "-i", input_path,
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-c:a", "copy",
            "-y",
            output_path,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                logger.warning(f"FFmpeg subtitle burn warning: {result.stderr[-500:]}")
                # Fallback: copy without subtitles
                import shutil
                shutil.copy(input_path, output_path)
        except subprocess.TimeoutExpired:
            raise RuntimeError("视频字幕压制超时（5分钟），请缩短视频长度")
        except FileNotFoundError:
            logger.warning("FFmpeg not found, skipping subtitle burn")
            import shutil
            shutil.copy(input_path, output_path)

    @staticmethod
    def _color_to_ass(color_name: str) -> str:
        """Convert common color names to ASS subtitle hex format (&HBBGGRR&)."""
        color_map = {
            "white": "&H00FFFFFF",
            "black": "&H00000000",
            "yellow": "&H0000FFFF",
            "red": "&H000000FF",
            "blue": "&H00FF0000",
            "green": "&H0000FF00",
        }
        return color_map.get(color_name.lower(), "&H00FFFFFF")
