"""
AutoVideoCraft - Automatic Environment Initialization
Handles FFmpeg setup and dependency verification on first launch.
"""

import os
import sys
import subprocess
import importlib.util
from loguru import logger


def _check_package(package_name: str) -> bool:
    """Check if a Python package is installed."""
    spec = importlib.util.find_spec(package_name.replace("-", "_").replace(".", "_"))
    return spec is not None


def setup_ffmpeg() -> str:
    """
    Configure FFmpeg using imageio-ffmpeg (cross-platform, no manual download needed).
    Returns the path to the FFmpeg executable.
    """
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        # Tell MoviePy and imageio to use this FFmpeg
        os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe

        # Also add to PATH so subprocess calls work
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path

        logger.info(f"FFmpeg configured: {ffmpeg_exe}")
        return ffmpeg_exe

    except ImportError:
        logger.error("imageio-ffmpeg not installed. Please run: pip install imageio-ffmpeg")
        raise RuntimeError(
            "imageio-ffmpeg is required. Run: pip install imageio-ffmpeg"
        )
    except Exception as e:
        logger.error(f"FFmpeg setup failed: {e}")
        raise


def verify_critical_deps() -> list[str]:
    """
    Verify that all critical dependencies are installed.
    Returns a list of missing packages.
    """
    critical_packages = {
        "gradio": "gradio",
        "openai": "openai",
        "edge_tts": "edge-tts",
        "moviepy": "moviepy",
        "requests": "requests",
        "loguru": "loguru",
        "PIL": "Pillow",
        "imageio_ffmpeg": "imageio-ffmpeg",
    }

    missing = []
    for import_name, pip_name in critical_packages.items():
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            missing.append(pip_name)
            logger.warning(f"Missing package: {pip_name}")

    return missing


def install_missing_deps(missing: list[str]) -> bool:
    """
    Attempt to install missing packages via pip.
    Returns True if successful.
    """
    if not missing:
        return True

    logger.info(f"Auto-installing missing packages: {', '.join(missing)}")
    try:
        cmd = [sys.executable, "-m", "pip", "install"] + missing
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        logger.success("All missing packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install packages: {e}")
        return False


def ensure_dirs() -> None:
    """Create required project directories if they don't exist."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dirs = [
        os.path.join(base_dir, "outputs"),
        os.path.join(base_dir, "temp"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.debug(f"Project directories verified.")


def initialize() -> str:
    """
    Full initialization sequence. Call this before launching the app.
    Returns the FFmpeg executable path.
    """
    logger.info("=== AutoVideoCraft Environment Initialization ===")

    # 1. Verify Python version
    if sys.version_info < (3, 9):
        raise RuntimeError(f"Python 3.9+ is required, got {sys.version}")
    logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor} - OK")

    # 2. Check and install missing deps
    missing = verify_critical_deps()
    if missing:
        logger.warning(f"{len(missing)} package(s) missing, attempting auto-install...")
        success = install_missing_deps(missing)
        if not success:
            raise RuntimeError(
                f"Failed to install required packages: {missing}\n"
                f"Please run manually: pip install -r requirements.txt"
            )

    # 3. Setup FFmpeg
    ffmpeg_exe = setup_ffmpeg()

    # 4. Ensure output dirs
    ensure_dirs()

    logger.success("=== Initialization Complete. Starting AutoVideoCraft... ===")
    return ffmpeg_exe


if __name__ == "__main__":
    initialize()
