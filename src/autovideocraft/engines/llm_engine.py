"""
AutoVideoCraft - LLM Engine
Generates video scripts and search keywords using any OpenAI-compatible LLM.
Supports: OpenAI, DeepSeek, Zhipu, Qwen, Moonshot, Doubao, and any custom provider.
"""

import json
from typing import Optional
from loguru import logger
from openai import OpenAI, APIError, AuthenticationError, RateLimitError


SCRIPT_GENERATION_PROMPT = """你是一位专业的短视频文案创作者。

用户主题：{topic}
视频时长目标：{duration}秒
语言：{language}

请生成：
1. 一段适合作为短视频口播的文案（字数根据时长，约每秒5个字）
2. 3个用于搜索视频素材的**英文关键词**（用逗号分隔，适合在Pexels/Pixabay上搜索）

严格按以下JSON格式输出，不要有任何额外内容：
{{
  "script": "文案内容",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "title": "视频标题（15字以内）"
}}"""


class LLMEngine:
    """
    Universal LLM client supporting all OpenAI-compatible providers.
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        if not api_key:
            raise ValueError("API Key cannot be empty")
        if not base_url:
            raise ValueError("Base URL cannot be empty")
        if not model:
            raise ValueError("Model name cannot be empty")

        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
        )
        logger.info(f"LLM Engine initialized: model={model}, base_url={base_url}")

    def generate_script(
        self,
        topic: str,
        duration: int = 30,
        language: str = "中文",
        progress_callback=None,
    ) -> dict:
        """
        Generate a video script and search keywords for the given topic.

        Args:
            topic: The video topic.
            duration: Target video duration in seconds.
            language: Language for the script.
            progress_callback: Optional callable(message: str) for progress updates.

        Returns:
            dict with keys: script, keywords (list), title
        """
        if progress_callback:
            progress_callback("正在调用大模型生成文案...")

        prompt = SCRIPT_GENERATION_PROMPT.format(
            topic=topic,
            duration=duration,
            language=language,
        )

        try:
            logger.info(f"Generating script for topic: '{topic}' ({duration}s, {language})")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content.strip()
            result = json.loads(content)

            # Validate required fields
            if "script" not in result:
                raise ValueError("LLM response missing 'script' field")
            if "keywords" not in result or not isinstance(result["keywords"], list):
                result["keywords"] = [topic]
            if "title" not in result:
                result["title"] = topic[:15]

            logger.success(f"Script generated: {len(result['script'])} chars, keywords={result['keywords']}")
            return result

        except AuthenticationError:
            raise RuntimeError("API Key 无效或已过期，请检查设置中的 API Key")
        except RateLimitError:
            raise RuntimeError("API 调用频率超限，请稍后重试")
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            # Fallback: extract script from raw text
            raw = response.choices[0].message.content if 'response' in dir() else ""
            return {
                "script": raw,
                "keywords": [topic],
                "title": topic[:15],
            }
        except APIError as e:
            raise RuntimeError(f"大模型 API 错误: {str(e)}")
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            raise RuntimeError(f"文案生成失败: {str(e)}")

    def test_connection(self) -> tuple[bool, str]:
        """
        Test the LLM connection with a minimal request.
        Returns (success, message).
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Reply with 'OK' only."}],
                max_tokens=10,
            )
            reply = response.choices[0].message.content.strip()
            logger.success(f"LLM connection test passed: '{reply}'")
            return True, f"连接成功！模型回复: {reply}"
        except AuthenticationError:
            return False, "认证失败：API Key 无效或已过期"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
