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


def srt_to_vtt(srt_content: str) -> str:
    """
    Convert SRT format to WebVTT format for browser subtitle rendering.

    Args:
        srt_content: Raw SRT subtitle content string.

    Returns:
        VTT-formatted subtitle string.
    """
    lines = srt_content.strip().split("\n")
    vtt_lines = ["WEBVTT", ""]  # VTT header
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.isdigit():
            # SRT index - skip it
            i += 1
            if i < len(lines) and "-->" in lines[i]:
                # Convert SRT timestamp (HH:MM:SS,mmm) to VTT (HH:MM:SS.mmm)
                vtt_time = lines[i].strip().replace(",", ".")
                vtt_lines.append(vtt_time)
                i += 1
                # Collect text lines until blank line or end
                while i < len(lines) and lines[i].strip():
                    vtt_lines.append(lines[i].strip())
                    i += 1
                vtt_lines.append("")  # blank line separator
        elif "-->" in line:
            # Convert SRT timestamp to VTT
            vtt_time = line.replace(",", ".")
            vtt_lines.append(vtt_time)
            i += 1
            # Collect text lines
            while i < len(lines) and lines[i].strip():
                vtt_lines.append(lines[i].strip())
                i += 1
            vtt_lines.append("")
        else:
            i += 1

    return "\n".join(vtt_lines)
