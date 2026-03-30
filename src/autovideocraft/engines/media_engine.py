"""
AutoVideoCraft - Media Engine
Downloads royalty-free stock video clips from Pexels and Pixabay.
"""

import os
import time
import random
from typing import Optional
from loguru import logger

import requests


class MediaEngine:
    """
    Stock video fetcher supporting Pexels and Pixabay APIs.
    Both are free with registration.
    """

    PEXELS_API_BASE = "https://api.pexels.com/videos/search"
    PIXABAY_API_BASE = "https://pixabay.com/api/videos/"

    def __init__(
        self,
        pexels_api_key: str = "",
        pixabay_api_key: str = "",
        preferred_source: str = "pexels",
        video_orientation: str = "portrait",
    ):
        self.pexels_key = pexels_api_key
        self.pixabay_key = pixabay_api_key
        self.preferred_source = preferred_source
        self.orientation = video_orientation  # portrait | landscape | square
        logger.info(f"Media Engine initialized: source={preferred_source}, orientation={video_orientation}")

    def search_and_download(
        self,
        keywords: list[str],
        output_dir: str,
        max_clips: int = 5,
        target_duration: float = 30.0,
        progress_callback=None,
    ) -> list[str]:
        """
        Search for and download video clips matching the keywords.

        Args:
            keywords: List of English search terms.
            output_dir: Directory to save downloaded clips.
            max_clips: Maximum number of clips to download.
            target_duration: Target total video duration (to determine clip count).
            progress_callback: Optional callable(message: str).

        Returns:
            List of local file paths to downloaded video clips.
        """
        if progress_callback:
            progress_callback("正在搜索视频素材...")

        os.makedirs(output_dir, exist_ok=True)
        downloaded = []

        for keyword in keywords:
            if len(downloaded) >= max_clips:
                break

            if progress_callback:
                progress_callback(f"搜索素材关键词: '{keyword}'...")

            try:
                if self.preferred_source == "pexels" and self.pexels_key:
                    clips = self._fetch_pexels(keyword, max_clips - len(downloaded))
                elif self.pixabay_key:
                    clips = self._fetch_pixabay(keyword, max_clips - len(downloaded))
                else:
                    logger.warning(f"No API key configured for {self.preferred_source}")
                    continue

                for i, clip_url in enumerate(clips):
                    if len(downloaded) >= max_clips:
                        break
                    fname = f"clip_{len(downloaded):03d}_{keyword.replace(' ', '_')}.mp4"
                    fpath = os.path.join(output_dir, fname)

                    if progress_callback:
                        progress_callback(f"下载素材 {len(downloaded)+1}/{max_clips}...")

                    if self._download_file(clip_url, fpath):
                        downloaded.append(fpath)
                        logger.info(f"Downloaded clip: {fpath}")

            except Exception as e:
                logger.warning(f"Failed to fetch clips for '{keyword}': {e}")
                continue

        if not downloaded:
            raise RuntimeError(
                "未能下载任何视频素材。请检查：\n"
                "1. API Key 是否正确\n"
                "2. 网络是否正常\n"
                "3. 尝试更换搜索关键词"
            )

        logger.success(f"Downloaded {len(downloaded)} video clips")
        return downloaded

    def _fetch_pexels(self, keyword: str, count: int) -> list[str]:
        """Fetch video URLs from Pexels API."""
        headers = {"Authorization": self.pexels_key}
        params = {
            "query": keyword,
            "per_page": min(count + 2, 15),  # fetch a few extra for quality filtering
            "orientation": self.orientation,
            "size": "medium",
        }

        response = requests.get(
            self.PEXELS_API_BASE,
            headers=headers,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        urls = []
        for video in data.get("videos", []):
            # Prefer HD quality (1280x720 or better)
            video_files = sorted(
                video.get("video_files", []),
                key=lambda x: x.get("width", 0),
                reverse=True,
            )
            for vf in video_files:
                if vf.get("file_type") == "video/mp4" and vf.get("width", 0) >= 720:
                    urls.append(vf["link"])
                    break

            if len(urls) >= count:
                break

        logger.debug(f"Pexels returned {len(urls)} URLs for '{keyword}'")
        return urls

    def _fetch_pixabay(self, keyword: str, count: int) -> list[str]:
        """Fetch video URLs from Pixabay API."""
        params = {
            "key": self.pixabay_key,
            "q": keyword,
            "video_type": "film",
            "per_page": min(count + 2, 20),
            "order": "popular",
        }

        response = requests.get(
            self.PIXABAY_API_BASE,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        urls = []
        for hit in data.get("hits", []):
            videos = hit.get("videos", {})
            # Try high quality first, then medium
            for quality in ["high", "medium", "small"]:
                if quality in videos and videos[quality].get("url"):
                    urls.append(videos[quality]["url"])
                    break
            if len(urls) >= count:
                break

        logger.debug(f"Pixabay returned {len(urls)} URLs for '{keyword}'")
        return urls

    def _download_file(self, url: str, output_path: str, chunk_size: int = 1024 * 1024) -> bool:
        """
        Download a file from URL to local path.
        Returns True on success.
        """
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.debug(f"File already exists, skipping: {output_path}")
            return True

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

            # Verify download
            if os.path.getsize(output_path) < 1000:
                os.remove(output_path)
                logger.warning(f"Downloaded file too small, discarded: {output_path}")
                return False

            return True

        except requests.RequestException as e:
            logger.error(f"Download failed ({url}): {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False

    def test_pexels_connection(self) -> tuple[bool, str]:
        """Test Pexels API connection."""
        if not self.pexels_key:
            return False, "Pexels API Key 未配置"
        try:
            urls = self._fetch_pexels("nature", 1)
            if urls:
                return True, f"Pexels 连接成功，找到视频资源"
            return False, "Pexels 连接成功但未找到视频，请检查 Key 权限"
        except Exception as e:
            return False, f"Pexels 连接失败: {str(e)}"

    def test_pixabay_connection(self) -> tuple[bool, str]:
        """Test Pixabay API connection."""
        if not self.pixabay_key:
            return False, "Pixabay API Key 未配置"
        try:
            urls = self._fetch_pixabay("nature", 1)
            if urls:
                return True, "Pixabay 连接成功"
            return False, "Pixabay 连接成功但未找到视频"
        except Exception as e:
            return False, f"Pixabay 连接失败: {str(e)}"
