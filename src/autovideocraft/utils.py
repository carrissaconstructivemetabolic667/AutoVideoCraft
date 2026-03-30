"""
AutoVideoCraft - Utility functions
Shared utilities with no heavy external dependencies.
"""


def vtt_to_srt(vtt_content: str) -> str:
    """
    Convert WebVTT format to SRT format for FFmpeg subtitle rendering.

    Args:
        vtt_content: Raw VTT subtitle content string.

    Returns:
        SRT-formatted subtitle string.
    """
    lines = vtt_content.strip().split("\n")
    srt_lines = []
    counter = 1
    i = 0

    # Skip WEBVTT header and any metadata
    while i < len(lines) and "-->" not in lines[i]:
        i += 1

    while i < len(lines):
        line = lines[i].strip()
        if "-->" in line:
            # Convert VTT timestamp (HH:MM:SS.mmm) to SRT (HH:MM:SS,mmm)
            srt_time = line.replace(".", ",")
            srt_lines.append(str(counter))
            srt_lines.append(srt_time)
            counter += 1
            i += 1
            # Collect text lines until blank line or end
            while i < len(lines) and lines[i].strip():
                srt_lines.append(lines[i].strip())
                i += 1
            srt_lines.append("")  # blank line separator
        i += 1

    return "\n".join(srt_lines)
