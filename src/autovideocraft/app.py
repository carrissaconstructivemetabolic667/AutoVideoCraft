"""
AutoVideoCraft - Main Gradio Web Application
Launch this file to start the web UI.
"""

import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional
from loguru import logger

# ── Bootstrap: ensure we can import from src/ ──────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))

# ── Auto-initialize environment before anything else ───────────────────────
from autovideocraft.init_env import initialize
try:
    initialize()
except Exception as e:
    print(f"[WARN] Environment initialization issue: {e}")
    print("Continuing anyway — some features may not work.")

# ── Imports ─────────────────────────────────────────────────────────────────
import gradio as gr
from autovideocraft.config import (
    load_config, save_config, update_config_section,
    PROVIDER_PRESETS, TTS_VOICES, validate_llm_config, validate_media_config,
)
from autovideocraft.engines.llm_engine import LLMEngine
from autovideocraft.engines.media_engine import MediaEngine
from autovideocraft.pipeline import VideoPipeline


# ── Globals ──────────────────────────────────────────────────────────────────
_pipeline_lock = threading.Lock()
APP_VERSION = "1.0.0"


# ──────────────────────────────────────────────────────────────────────────────
# Helper: build pipeline from current config
# ──────────────────────────────────────────────────────────────────────────────

def _build_pipeline() -> tuple[Optional[VideoPipeline], str]:
    config = load_config()
    ok, err = validate_llm_config(config)
    if not ok:
        return None, err
    try:
        return VideoPipeline(config), ""
    except Exception as e:
        return None, str(e)


# ──────────────────────────────────────────────────────────────────────────────
# Tab 1 — Video Generation
# ──────────────────────────────────────────────────────────────────────────────

def generate_video(topic, duration, language, progress=gr.Progress()):
    """Main generation handler called by Gradio."""
    if not topic or not topic.strip():
        return None, "", "❌ 请输入视频主题", gr.update(visible=False)

    config = load_config()
    ok, err = validate_llm_config(config)
    if not ok:
        return None, "", f"❌ {err}", gr.update(visible=False)

    ok2, err2 = validate_media_config(config)
    if not ok2:
        return None, "", f"❌ {err2}", gr.update(visible=False)

    if not _pipeline_lock.acquire(blocking=False):
        return None, "", "⏳ 当前有视频正在生成，请稍后再试", gr.update(visible=False)

    script_display = ""
    status_msg = ""

    try:
        pipeline = VideoPipeline(config)
        steps = []

        def on_progress(msg: str):
            steps.append(msg)
            progress(len(steps) / 8, desc=msg)

        result = pipeline.generate(
            topic=topic.strip(),
            duration=int(duration),
            language=language,
            progress_callback=on_progress,
        )

        if result.success:
            script_display = f"**标题：** {result.title}\n\n**文案：**\n\n{result.script}"
            status_msg = (
                f"✅ 视频生成成功！耗时 {result.elapsed_seconds:.0f} 秒\n"
                f"关键词: {', '.join(result.keywords)}"
            )
            return result.video_path, script_display, status_msg, gr.update(visible=True)
        else:
            status_msg = f"❌ 生成失败：{result.error}"
            return None, script_display, status_msg, gr.update(visible=False)

    except Exception as e:
        logger.error(f"Unexpected error in generate_video: {e}")
        return None, "", f"❌ 未知错误：{str(e)}", gr.update(visible=False)
    finally:
        _pipeline_lock.release()


# ──────────────────────────────────────────────────────────────────────────────
# Tab 2 — LLM Settings
# ──────────────────────────────────────────────────────────────────────────────

def load_llm_settings():
    config = load_config()
    llm = config["llm"]
    return llm["provider"], llm["api_key"], llm["base_url"], llm["model"]


def on_provider_change(provider: str):
    """Auto-fill base_url and model when provider changes."""
    preset = PROVIDER_PRESETS.get(provider, {})
    return preset.get("base_url", ""), preset.get("default_model", "")


def save_llm_settings(provider, api_key, base_url, model):
    if not api_key.strip():
        return "❌ API Key 不能为空"
    if not base_url.strip():
        return "❌ Base URL 不能为空"
    if not model.strip():
        return "❌ 模型名称不能为空"

    update_config_section("llm", {
        "provider": provider,
        "api_key": api_key.strip(),
        "base_url": base_url.strip().rstrip("/"),
        "model": model.strip(),
    })
    return "✅ 大模型配置已保存"


def test_llm_connection(api_key, base_url, model):
    if not api_key.strip() or not base_url.strip() or not model.strip():
        return "❌ 请先填写 API Key、Base URL 和模型名称"
    try:
        engine = LLMEngine(api_key=api_key.strip(), base_url=base_url.strip(), model=model.strip())
        ok, msg = engine.test_connection()
        return f"{'✅' if ok else '❌'} {msg}"
    except Exception as e:
        return f"❌ {str(e)}"


# ──────────────────────────────────────────────────────────────────────────────
# Tab 3 — Media / TTS Settings
# ──────────────────────────────────────────────────────────────────────────────

def load_media_settings():
    config = load_config()
    media = config["media"]
    tts = config["tts"]
    voice_display = {v: k for k, v in TTS_VOICES.items()}.get(tts["voice"], list(TTS_VOICES.keys())[0])
    return (
        media.get("pexels_api_key", ""),
        media.get("pixabay_api_key", ""),
        media.get("preferred_source", "pexels"),
        media.get("video_orientation", "portrait"),
        voice_display,
        tts.get("rate", "+0%"),
    )


def save_media_settings(pexels_key, pixabay_key, source, orientation, voice_display, rate):
    voice_id = TTS_VOICES.get(voice_display, "zh-CN-XiaoxiaoNeural")
    update_config_section("media", {
        "pexels_api_key": pexels_key.strip(),
        "pixabay_api_key": pixabay_key.strip(),
        "preferred_source": source,
        "video_orientation": orientation,
    })
    update_config_section("tts", {
        "voice": voice_id,
        "rate": rate,
    })
    return "✅ 素材与配音配置已保存"


def test_pexels(pexels_key):
    if not pexels_key.strip():
        return "❌ 请先填写 Pexels API Key"
    engine = MediaEngine(pexels_api_key=pexels_key.strip())
    ok, msg = engine.test_pexels_connection()
    return f"{'✅' if ok else '❌'} {msg}"


def test_pixabay(pixabay_key):
    if not pixabay_key.strip():
        return "❌ 请先填写 Pixabay API Key"
    engine = MediaEngine(pixabay_api_key=pixabay_key.strip(), preferred_source="pixabay")
    ok, msg = engine.test_pixabay_connection()
    return f"{'✅' if ok else '❌'} {msg}"


# ──────────────────────────────────────────────────────────────────────────────
# Tab 4 — Video Quality Settings
# ──────────────────────────────────────────────────────────────────────────────

def load_video_settings():
    config = load_config()
    v = config["video"]
    return (
        v.get("resolution", "1080x1920"),
        v.get("subtitle_enabled", True),
        v.get("subtitle_font_size", 48),
        v.get("subtitle_color", "white"),
        v.get("subtitle_position", "bottom"),
    )


def save_video_settings(resolution, subtitle_enabled, font_size, sub_color, sub_position):
    update_config_section("video", {
        "resolution": resolution,
        "subtitle_enabled": subtitle_enabled,
        "subtitle_font_size": font_size,
        "subtitle_color": sub_color,
        "subtitle_position": sub_position,
    })
    return "✅ 视频质量配置已保存"


# ──────────────────────────────────────────────────────────────────────────────
# Build Gradio UI
# ──────────────────────────────────────────────────────────────────────────────

CSS = """
.status-box { font-size: 0.9em; padding: 8px; border-radius: 6px; }
.generate-btn { font-size: 1.1em !important; }
footer { display: none !important; }
"""

def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="AutoVideoCraft",
        theme=gr.themes.Soft(primary_hue="indigo", secondary_hue="blue"),
        css=CSS,
    ) as demo:

        # ── Header ──────────────────────────────────────────────────────────
        gr.HTML("""
        <div style="text-align:center; padding: 20px 0 10px 0;">
            <h1 style="font-size:2em; margin:0;">🎬 AutoVideoCraft</h1>
            <p style="color:#666; margin:4px 0 0 0;">
                AI 驱动的短视频自动生成工具 · 输入主题，一键生成竖版短视频
            </p>
        </div>
        """)

        with gr.Tabs():
            # ──────────────────────────────────────────────────────────────
            # TAB 1: Generate
            # ──────────────────────────────────────────────────────────────
            with gr.Tab("🎬 生成视频"):
                with gr.Row():
                    with gr.Column(scale=1):
                        topic_input = gr.Textbox(
                            label="视频主题",
                            placeholder="例如：为什么天空是蓝色的 / 5个提高工作效率的技巧 / 深海生物科普",
                            lines=2,
                        )
                        with gr.Row():
                            duration_slider = gr.Slider(
                                minimum=15, maximum=90, step=5, value=30,
                                label="目标时长（秒）",
                            )
                            language_dd = gr.Dropdown(
                                choices=["中文", "English", "日本語", "한국어"],
                                value="中文",
                                label="文案语言",
                            )

                        generate_btn = gr.Button(
                            "⚡ 一键生成视频",
                            variant="primary",
                            elem_classes=["generate-btn"],
                        )
                        status_output = gr.Markdown(
                            value="*配置好 API Key 后，输入主题点击生成即可。*",
                            elem_classes=["status-box"],
                        )

                    with gr.Column(scale=1):
                        video_output = gr.Video(label="生成结果", visible=True)
                        script_output = gr.Markdown(label="生成文案")
                        download_btn = gr.DownloadButton(
                            label="⬇️ 下载视频",
                            visible=False,
                        )

                generate_btn.click(
                    fn=generate_video,
                    inputs=[topic_input, duration_slider, language_dd],
                    outputs=[video_output, script_output, status_output, download_btn],
                )

            # ──────────────────────────────────────────────────────────────
            # TAB 2: LLM Settings
            # ──────────────────────────────────────────────────────────────
            with gr.Tab("🤖 大模型设置"):
                gr.Markdown("""
                ### 大模型 API 配置
                支持所有兼容 OpenAI 格式的服务商。免费推荐：**DeepSeek**（注册即送额度）。

                > 获取 API Key：[DeepSeek](https://platform.deepseek.com) · [智谱](https://open.bigmodel.cn) · [阿里云](https://dashscope.console.aliyun.com) · [Moonshot](https://platform.moonshot.cn)
                """)

                with gr.Row():
                    provider_dd = gr.Dropdown(
                        choices=list(PROVIDER_PRESETS.keys()),
                        value="DeepSeek",
                        label="服务商",
                        scale=1,
                    )
                    model_input = gr.Textbox(
                        label="模型名称",
                        placeholder="deepseek-chat",
                        scale=1,
                    )

                with gr.Row():
                    base_url_input = gr.Textbox(
                        label="Base URL",
                        placeholder="https://api.deepseek.com/v1",
                        scale=2,
                    )
                    api_key_input = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="sk-...",
                        scale=2,
                    )

                with gr.Row():
                    save_llm_btn = gr.Button("💾 保存配置", variant="primary")
                    test_llm_btn = gr.Button("🔌 测试连接")

                llm_status = gr.Markdown()

                # Auto-fill on provider change
                provider_dd.change(
                    fn=on_provider_change,
                    inputs=provider_dd,
                    outputs=[base_url_input, model_input],
                )
                save_llm_btn.click(
                    fn=save_llm_settings,
                    inputs=[provider_dd, api_key_input, base_url_input, model_input],
                    outputs=llm_status,
                )
                test_llm_btn.click(
                    fn=test_llm_connection,
                    inputs=[api_key_input, base_url_input, model_input],
                    outputs=llm_status,
                )

                # Load saved values on page render
                demo.load(
                    fn=load_llm_settings,
                    outputs=[provider_dd, api_key_input, base_url_input, model_input],
                )

            # ──────────────────────────────────────────────────────────────
            # TAB 3: Media & TTS Settings
            # ──────────────────────────────────────────────────────────────
            with gr.Tab("🎵 素材 & 配音"):
                gr.Markdown("""
                ### 视频素材 API
                免费申请：[Pexels API](https://www.pexels.com/api) · [Pixabay API](https://pixabay.com/api/docs)
                
                ### 配音设置
                使用微软 Edge TTS，完全免费，无需额外 Key。
                """)

                with gr.Group():
                    gr.Markdown("**Pexels（推荐）**")
                    with gr.Row():
                        pexels_key_input = gr.Textbox(
                            label="Pexels API Key",
                            type="password",
                            placeholder="输入你的 Pexels API Key",
                            scale=3,
                        )
                        test_pexels_btn = gr.Button("🔌 测试", scale=1)
                    pexels_status = gr.Markdown()

                with gr.Group():
                    gr.Markdown("**Pixabay（备用）**")
                    with gr.Row():
                        pixabay_key_input = gr.Textbox(
                            label="Pixabay API Key",
                            type="password",
                            placeholder="输入你的 Pixabay API Key",
                            scale=3,
                        )
                        test_pixabay_btn = gr.Button("🔌 测试", scale=1)
                    pixabay_status = gr.Markdown()

                with gr.Row():
                    source_dd = gr.Dropdown(
                        choices=["pexels", "pixabay"],
                        value="pexels",
                        label="优先使用素材源",
                    )
                    orientation_dd = gr.Dropdown(
                        choices=["portrait", "landscape", "square"],
                        value="portrait",
                        label="视频方向",
                    )

                gr.Markdown("---")
                with gr.Row():
                    voice_dd = gr.Dropdown(
                        choices=list(TTS_VOICES.keys()),
                        value=list(TTS_VOICES.keys())[0],
                        label="配音音色",
                    )
                    rate_dd = gr.Dropdown(
                        choices=["-20%", "-10%", "+0%", "+10%", "+20%", "+30%"],
                        value="+0%",
                        label="语速",
                    )

                save_media_btn = gr.Button("💾 保存配置", variant="primary")
                media_status = gr.Markdown()

                test_pexels_btn.click(fn=test_pexels, inputs=pexels_key_input, outputs=pexels_status)
                test_pixabay_btn.click(fn=test_pixabay, inputs=pixabay_key_input, outputs=pixabay_status)
                save_media_btn.click(
                    fn=save_media_settings,
                    inputs=[pexels_key_input, pixabay_key_input, source_dd, orientation_dd, voice_dd, rate_dd],
                    outputs=media_status,
                )

                demo.load(
                    fn=load_media_settings,
                    outputs=[pexels_key_input, pixabay_key_input, source_dd, orientation_dd, voice_dd, rate_dd],
                )

            # ──────────────────────────────────────────────────────────────
            # TAB 4: Video Quality
            # ──────────────────────────────────────────────────────────────
            with gr.Tab("⚙️ 视频质量"):
                gr.Markdown("### 输出视频参数")

                with gr.Row():
                    resolution_dd = gr.Dropdown(
                        choices=["1080x1920", "720x1280", "1920x1080", "1280x720"],
                        value="1080x1920",
                        label="分辨率（宽x高）",
                    )

                subtitle_enabled_cb = gr.Checkbox(value=True, label="启用字幕")
                with gr.Row():
                    font_size_slider = gr.Slider(
                        minimum=24, maximum=80, step=4, value=48, label="字幕字号"
                    )
                    sub_color_dd = gr.Dropdown(
                        choices=["white", "yellow", "black", "red"],
                        value="white",
                        label="字幕颜色",
                    )
                    sub_pos_dd = gr.Dropdown(
                        choices=["bottom", "middle"],
                        value="bottom",
                        label="字幕位置",
                    )

                save_video_btn = gr.Button("💾 保存配置", variant="primary")
                video_settings_status = gr.Markdown()

                save_video_btn.click(
                    fn=save_video_settings,
                    inputs=[resolution_dd, subtitle_enabled_cb, font_size_slider, sub_color_dd, sub_pos_dd],
                    outputs=video_settings_status,
                )
                demo.load(
                    fn=load_video_settings,
                    outputs=[resolution_dd, subtitle_enabled_cb, font_size_slider, sub_color_dd, sub_pos_dd],
                )

            # ──────────────────────────────────────────────────────────────
            # TAB 5: About
            # ──────────────────────────────────────────────────────────────
            with gr.Tab("ℹ️ 关于"):
                gr.Markdown(f"""
                ## AutoVideoCraft v{APP_VERSION}

                **AI 驱动的开源短视频自动生成工具**

                ### 工作流程
                ```
                用户输入主题
                    ↓
                大模型生成文案 + 英文关键词（支持 DeepSeek / OpenAI / 通义千问等）
                    ↓
                Edge TTS 语音合成（免费，无需 Key）+ 自动生成字幕
                    ↓
                Pexels / Pixabay 下载免版权视频素材
                    ↓
                MoviePy + FFmpeg 合成最终视频（带字幕）
                    ↓
                输出 MP4，可直接下载分享
                ```

                ### 技术栈
                | 组件 | 技术 |
                |------|------|
                | Web UI | Gradio 4.x |
                | 大模型 | OpenAI SDK（兼容所有 OpenAI 格式 API） |
                | 语音合成 | Microsoft Edge TTS（免费） |
                | 视频素材 | Pexels API / Pixabay API（免费注册） |
                | 视频处理 | MoviePy + FFmpeg（自动配置） |

                ### 开源协议
                MIT License · 欢迎 Star & PR

                ### 链接
                - [GitHub](https://github.com/jsoner-desiner/AutoVideoCraft)
                - [问题反馈](https://github.com/jsoner-desiner/AutoVideoCraft/issues)
                """)

    return demo


# ──────────────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=True,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
