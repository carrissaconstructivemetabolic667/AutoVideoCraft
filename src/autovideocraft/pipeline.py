"""
AutoVideoCraft - Video Generation Pipeline
Orchestrates the full workflow: LLM → TTS → Media → Video composition.
"""

import os
import time
import uuid
from pathlib import Path
from typing import Optional, Callable
from loguru import logger

from .config import load_config, validate_llm_config, validate_media_config
from .engines.llm_engine import LLMEngine
from .engines.tts_engine import TTSEngine
from .engines.media_engine import MediaEngine
from .engines.video_engine import VideoEngine


class GenerationResult:
    """Result container for a video generation run."""

    def __init__(self):
        self.success: bool = False
        self.video_path: Optional[str] = None
        self.script: str = ""
        self.title: str = ""
        self.keywords: list[str] = []
        self.audio_path: Optional[str] = None
        self.error: Optional[str] = None
        self.elapsed_seconds: float = 0.0

    def __repr__(self) -> str:
        if self.success:
            return f"GenerationResult(success=True, video={self.video_path}, elapsed={self.elapsed_seconds:.1f}s)"
        return f"GenerationResult(success=False, error={self.error})"


class VideoPipeline:
    """
    End-to-end video generation pipeline.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        self._init_engines()

    def _init_engines(self):
        """Initialize all engine instances from current config."""
        cfg = self.config
        llm_cfg = cfg["llm"]
        tts_cfg = cfg["tts"]
        media_cfg = cfg["media"]
        video_cfg = cfg["video"]

        self.llm = LLMEngine(
            api_key=llm_cfg["api_key"],
            base_url=llm_cfg["base_url"],
            model=llm_cfg["model"],
        )
        self.tts = TTSEngine(
            voice=tts_cfg["voice"],
            rate=tts_cfg["rate"],
            volume=tts_cfg["volume"],
        )
        self.media = MediaEngine(
            pexels_api_key=media_cfg.get("pexels_api_key", ""),
            pixabay_api_key=media_cfg.get("pixabay_api_key", ""),
            preferred_source=media_cfg.get("preferred_source", "pexels"),
            video_orientation=media_cfg.get("video_orientation", "portrait"),
        )
        self.video = VideoEngine(
            fps=video_cfg.get("fps", 24),
            resolution=video_cfg.get("resolution", "1080x1920"),
            subtitle_enabled=video_cfg.get("subtitle_enabled", True),
            subtitle_font_size=video_cfg.get("subtitle_font_size", 48),
            subtitle_color=video_cfg.get("subtitle_color", "white"),
            subtitle_stroke_color=video_cfg.get("subtitle_stroke_color", "black"),
            subtitle_stroke_width=video_cfg.get("subtitle_stroke_width", 2),
            subtitle_position=video_cfg.get("subtitle_position", "bottom"),
        )

    def generate(
        self,
        topic: str,
        duration: int = 30,
        language: str = "中文",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> GenerationResult:
        """
        Run the full video generation pipeline.

        Args:
            topic: Video topic/theme.
            duration: Target duration in seconds (15-120).
            language: Script language.
            progress_callback: Callable for real-time progress updates.

        Returns:
            GenerationResult with video path on success.
        """
        result = GenerationResult()
        start_time = time.time()

        def _progress(msg: str):
            logger.info(f"[Pipeline] {msg}")
            if progress_callback:
                progress_callback(msg)

        # Create unique session directory
        session_id = uuid.uuid4().hex[:8]
        base_dir = Path(__file__).parent.parent.parent
        session_dir = base_dir / "temp" / session_id
        output_dir = base_dir / "outputs"
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        try:
            # ── Step 1: Generate script via LLM ──────────────────────────
            _progress("📝 [1/4] 正在生成视频文案...")
            script_data = self.llm.generate_script(
                topic=topic,
                duration=duration,
                language=language,
                progress_callback=_progress,
            )
            result.script = script_data["script"]
            result.keywords = script_data["keywords"]
            result.title = script_data.get("title", topic[:15])
            logger.info(f"Script: {result.script[:80]}...")

            # ── Step 2: TTS synthesis ─────────────────────────────────────
            _progress("🎙️ [2/4] 正在生成配音（Edge TTS）...")
            tts_result = self.tts.synthesize(
                text=result.script,
                output_dir=str(session_dir),
                filename_prefix="speech",
                progress_callback=_progress,
            )
            result.audio_path = tts_result["audio_path"]
            subtitle_srt = tts_result.get("subtitle_srt")

            # ── Step 3: Download stock footage ────────────────────────────
            _progress("🎬 [3/4] 正在搜索并下载视频素材...")
            clips = self.media.search_and_download(
                keywords=result.keywords,
                output_dir=str(session_dir / "clips"),
                max_clips=5,
                target_duration=float(duration),
                progress_callback=_progress,
            )

            # ── Step 4: Compose final video ───────────────────────────────
            _progress("🎞️ [4/4] 正在合成最终视频...")
            safe_title = "".join(c for c in result.title if c.isalnum() or c in "_ ").strip()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_filename = f"{safe_title}_{timestamp}.mp4"
            output_path = str(output_dir / output_filename)

            final_path = self.video.compose(
                video_clips=clips,
                audio_path=result.audio_path,
                subtitle_srt=subtitle_srt,
                output_path=output_path,
                progress_callback=_progress,
            )

            result.video_path = final_path
            result.success = True
            result.elapsed_seconds = time.time() - start_time

            _progress(f"✅ 视频生成完成！耗时 {result.elapsed_seconds:.0f}s → {output_filename}")
            return result

        except Exception as e:
            result.success = False
            result.error = str(e)
            result.elapsed_seconds = time.time() - start_time
            logger.error(f"Pipeline failed after {result.elapsed_seconds:.1f}s: {e}")
            _progress(f"❌ 生成失败: {e}")
            return result

        finally:
            # Clean up temp session directory
            _cleanup_dir(str(session_dir))


def _cleanup_dir(path: str) -> None:
    """Remove a temporary directory and its contents."""
    import shutil
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.debug(f"Cleaned temp dir: {path}")
    except Exception as e:
        logger.warning(f"Failed to clean temp dir {path}: {e}")
