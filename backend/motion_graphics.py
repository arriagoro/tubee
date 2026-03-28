"""
motion_graphics.py — Basic motion graphics for Tubee
Creates title cards, lower thirds, countdowns, and end cards using FFmpeg.

All outputs are MP4 files ready to concatenate with other clips.
Uses drawtext filter with fade animations.
"""

import os
import logging
import subprocess
import tempfile
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Default resolution: vertical (Reels/TikTok/Shorts)
DEFAULT_RESOLUTION = (1080, 1920)
DEFAULT_FPS = 30
DEFAULT_CODEC = "libx264"


def _run_ffmpeg(cmd: list, timeout: int = 120) -> bool:
    """Run FFmpeg command. Returns True on success."""
    logger.debug(f"FFmpeg: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        logger.error(f"FFmpeg failed: {result.stderr[-600:]}")
        return False
    return True


def _escape_text(text: str) -> str:
    """Escape text for FFmpeg drawtext filter."""
    return text.replace("'", "'\\\\\\''").replace(":", "\\:").replace("%", "%%")


# ---------------------------------------------------------------------------
# Title Card
# ---------------------------------------------------------------------------

def create_title_card(
    text: str,
    duration: float = 3,
    resolution: Tuple[int, int] = DEFAULT_RESOLUTION,
    bg_color: str = "black",
    text_color: str = "white",
    font_size: int = 80,
    output_path: Optional[str] = None,
) -> Optional[str]:
    """
    Create an MP4 title card with centered text and fade in/out animation.

    Args:
        text: Title text to display.
        duration: Duration in seconds (default 3).
        resolution: (width, height) tuple.
        bg_color: Background color (FFmpeg color name or hex).
        text_color: Text color.
        font_size: Font size in pixels.
        output_path: Output file path. Auto-generated if None.

    Returns:
        Path to output MP4, or None on failure.
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "tubee_title_card.mp4")

    w, h = resolution
    safe_text = _escape_text(text)
    fade_dur = min(0.5, duration / 4)

    # Generate solid color background with lavfi, then add text with fade
    # Text fades in over fade_dur, holds, fades out over fade_dur
    alpha_expr = (
        f"if(lt(t,{fade_dur}),t/{fade_dur},"
        f"if(lt(t,{duration - fade_dur}),1,"
        f"({duration}-t)/{fade_dur}))"
    )

    filter_str = (
        f"drawtext=text='{safe_text}':"
        f"fontsize={font_size}:"
        f"fontcolor={text_color}:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:"
        f"alpha='{alpha_expr}':"
        f"shadowcolor=black@0.5:shadowx=3:shadowy=3"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={w}x{h}:d={duration}:r={DEFAULT_FPS}",
        # Generate silent audio track for concatenation compatibility
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", filter_str,
        "-c:v", DEFAULT_CODEC, "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path,
    ]

    try:
        if _run_ffmpeg(cmd):
            logger.info(f"Title card created: {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"create_title_card failed: {e}")

    return None


# ---------------------------------------------------------------------------
# Lower Third
# ---------------------------------------------------------------------------

def create_lower_third(
    text: str,
    duration: float = 4,
    resolution: Tuple[int, int] = DEFAULT_RESOLUTION,
    position: str = "bottom",
    style: str = "modern",
    output_path: Optional[str] = None,
) -> Optional[str]:
    """
    Create an animated lower third overlay as an MP4.

    The lower third slides in from the left, holds, then slides out.
    Features a semi-transparent background bar behind the text.

    Args:
        text: Text to display.
        duration: Total duration (default 4s).
        resolution: (width, height).
        position: "bottom" or "top" — where the bar appears.
        style: "modern" (clean slide) or "bold" (larger, more contrast).
        output_path: Output file path. Auto-generated if None.

    Returns:
        Path to output MP4, or None on failure.
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "tubee_lower_third.mp4")

    w, h = resolution
    safe_text = _escape_text(text)

    # Style parameters
    if style == "bold":
        font_size = 64
        bar_h = 120
        bar_alpha = 0.8
    else:  # "modern"
        font_size = 48
        bar_h = 90
        bar_alpha = 0.6

    # Position the bar
    if position == "top":
        bar_y = int(h * 0.06)
    else:
        bar_y = int(h * 0.85)

    slide_dur = 0.4  # Slide in/out duration
    hold_dur = duration - slide_dur * 2

    # Animate X position: slide in from left, hold, slide out to left
    # Bar x animation expression
    bar_x_expr = (
        f"if(lt(t,{slide_dur}),"
        f"-w+w*(t/{slide_dur}),"  # Slide in
        f"if(lt(t,{slide_dur + hold_dur}),"
        f"0,"  # Hold at 0
        f"0-w*((t-{slide_dur + hold_dur})/{slide_dur})))"  # Slide out
    )

    # Alpha: full opacity during hold, 0 outside
    alpha_expr = (
        f"if(lt(t,{slide_dur}),t/{slide_dur},"
        f"if(lt(t,{duration - slide_dur}),1,"
        f"({duration}-t)/{slide_dur}))"
    )

    # Background bar (semi-transparent) + text on top
    filter_str = (
        # Draw background bar
        f"drawbox=x=0:y={bar_y}:w=iw:h={bar_h}:"
        f"color=black@{bar_alpha}:t=fill:"
        f"enable='between(t,0,{duration})',"
        # Draw text centered vertically in bar
        f"drawtext=text='{safe_text}':"
        f"fontsize={font_size}:"
        f"fontcolor=white:"
        f"x=w*0.05:y={bar_y + (bar_h - font_size) // 2}:"
        f"alpha='{alpha_expr}':"
        f"shadowcolor=black@0.4:shadowx=1:shadowy=1"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black@0.0:s={w}x{h}:d={duration}:r={DEFAULT_FPS}",
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", filter_str,
        "-c:v", DEFAULT_CODEC, "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path,
    ]

    try:
        if _run_ffmpeg(cmd):
            logger.info(f"Lower third created: {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"create_lower_third failed: {e}")

    return None


# ---------------------------------------------------------------------------
# Countdown
# ---------------------------------------------------------------------------

def create_countdown(
    from_num: int = 3,
    resolution: Tuple[int, int] = DEFAULT_RESOLUTION,
    bg_color: str = "black",
    text_color: str = "white",
    output_path: Optional[str] = None,
) -> Optional[str]:
    """
    Create a countdown animation (3... 2... 1... GO!).

    Each number fades in, scales up slightly, then fades out.
    Final "GO!" text flashes at the end.

    Args:
        from_num: Starting number (default 3 → "3, 2, 1, GO!").
        resolution: (width, height).
        bg_color: Background color.
        text_color: Text color.
        output_path: Output file path. Auto-generated if None.

    Returns:
        Path to output MP4, or None on failure.
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "tubee_countdown.mp4")

    w, h = resolution
    total_dur = from_num + 1  # +1 for "GO!" at the end

    # Build drawtext filters for each number + "GO!"
    filters = []

    for i in range(from_num, 0, -1):
        # Each number appears for 1 second
        t_start = from_num - i
        t_end = t_start + 1
        fade = 0.2

        alpha_expr = (
            f"if(lt(t,{t_start}),0,"
            f"if(lt(t,{t_start + fade}),"
            f"(t-{t_start})/{fade},"
            f"if(lt(t,{t_end - fade}),1,"
            f"if(lt(t,{t_end}),"
            f"({t_end}-t)/{fade},0))))"
        )

        # Font size pulse: starts at 120, grows to 160
        fontsize_expr = (
            f"if(between(t,{t_start},{t_end}),"
            f"120+40*(t-{t_start}),120)"
        )

        filters.append(
            f"drawtext=text='{i}':"
            f"fontsize='({fontsize_expr})':"
            f"fontcolor={text_color}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"alpha='{alpha_expr}'"
        )

    # "GO!" text
    go_start = from_num
    go_end = total_dur
    go_fade = 0.15
    go_alpha = (
        f"if(lt(t,{go_start}),0,"
        f"if(lt(t,{go_start + go_fade}),"
        f"(t-{go_start})/{go_fade},"
        f"if(lt(t,{go_end - go_fade}),1,"
        f"if(lt(t,{go_end}),"
        f"({go_end}-t)/{go_fade},0))))"
    )
    filters.append(
        f"drawtext=text='GO!':"
        f"fontsize=140:"
        f"fontcolor=yellow:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:"
        f"alpha='{go_alpha}':"
        f"shadowcolor=black@0.6:shadowx=3:shadowy=3"
    )

    filter_chain = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={w}x{h}:d={total_dur}:r={DEFAULT_FPS}",
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", filter_chain,
        "-c:v", DEFAULT_CODEC, "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(total_dur),
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path,
    ]

    try:
        if _run_ffmpeg(cmd):
            logger.info(f"Countdown created ({from_num}→GO!): {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"create_countdown failed: {e}")

    return None


# ---------------------------------------------------------------------------
# End Card
# ---------------------------------------------------------------------------

def create_end_card(
    text: str,
    social_handle: str,
    duration: float = 5,
    resolution: Tuple[int, int] = DEFAULT_RESOLUTION,
    bg_color: str = "black",
    text_color: str = "white",
    accent_color: str = "yellow",
    output_path: Optional[str] = None,
) -> Optional[str]:
    """
    Create an end card with CTA text and social handle.

    Layout:
        - Main text (CTA) centered, large font, fades in
        - Social handle below, smaller font, slides in after delay
        - Optional subscribe/follow prompt

    Args:
        text: Main CTA text (e.g. "Thanks for watching!").
        social_handle: Social media handle (e.g. "@filmtucktubee").
        duration: Total duration (default 5s).
        resolution: (width, height).
        bg_color: Background color.
        text_color: Main text color.
        accent_color: Social handle color.
        output_path: Output file path. Auto-generated if None.

    Returns:
        Path to output MP4, or None on failure.
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "tubee_end_card.mp4")

    w, h = resolution
    safe_text = _escape_text(text)
    safe_handle = _escape_text(social_handle)

    fade_in = 0.5
    handle_delay = 0.8  # Handle appears slightly after main text
    fade_out_start = duration - 0.8

    # Main text alpha (fade in, hold, fade out)
    main_alpha = (
        f"if(lt(t,{fade_in}),t/{fade_in},"
        f"if(lt(t,{fade_out_start}),1,"
        f"({duration}-t)/0.8))"
    )

    # Handle alpha (delayed fade in, hold, fade out)
    handle_alpha = (
        f"if(lt(t,{handle_delay}),0,"
        f"if(lt(t,{handle_delay + fade_in}),"
        f"(t-{handle_delay})/{fade_in},"
        f"if(lt(t,{fade_out_start}),1,"
        f"({duration}-t)/0.8)))"
    )

    # "Follow" prompt alpha — appears with handle
    follow_alpha = handle_alpha

    filter_str = (
        # Main CTA text
        f"drawtext=text='{safe_text}':"
        f"fontsize=72:"
        f"fontcolor={text_color}:"
        f"x=(w-text_w)/2:y=(h/2)-100:"
        f"alpha='{main_alpha}':"
        f"shadowcolor=black@0.5:shadowx=2:shadowy=2,"
        # Divider line (small)
        f"drawtext=text='———':"
        f"fontsize=36:"
        f"fontcolor={text_color}@0.5:"
        f"x=(w-text_w)/2:y=h/2:"
        f"alpha='{handle_alpha}',"
        # Social handle
        f"drawtext=text='{safe_handle}':"
        f"fontsize=56:"
        f"fontcolor={accent_color}:"
        f"x=(w-text_w)/2:y=(h/2)+60:"
        f"alpha='{handle_alpha}':"
        f"shadowcolor=black@0.4:shadowx=1:shadowy=1,"
        # "Follow for more" prompt
        f"drawtext=text='Follow for more':"
        f"fontsize=32:"
        f"fontcolor={text_color}@0.7:"
        f"x=(w-text_w)/2:y=(h/2)+140:"
        f"alpha='{follow_alpha}'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={w}x{h}:d={duration}:r={DEFAULT_FPS}",
        "-f", "lavfi",
        "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
        "-vf", filter_str,
        "-c:v", DEFAULT_CODEC, "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path,
    ]

    try:
        if _run_ffmpeg(cmd):
            logger.info(f"End card created: {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"create_end_card failed: {e}")

    return None


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Check FFmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        print(f"✅ FFmpeg found: {result.stdout.split(chr(10))[0]}")
    except FileNotFoundError:
        print("❌ FFmpeg not found!")
        sys.exit(1)

    # Check drawtext support
    result = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True)
    if "drawtext" in (result.stdout or ""):
        print("✅ drawtext filter available")
    else:
        print("⚠️  drawtext filter not found — text effects may not work")
        print("   Install FFmpeg with --enable-libfreetype")

    print("\n🎬 Motion graphics module loaded!")
    print("   Functions: create_title_card, create_lower_third, create_countdown, create_end_card")

    # Quick smoke test: create a 1-second title card
    if "--test" in sys.argv:
        print("\n🧪 Running smoke test...")
        out = create_title_card(
            text="TUBEE TEST",
            duration=1,
            resolution=(640, 360),
            output_path="/tmp/tubee_mg_test.mp4",
        )
        if out and os.path.exists(out):
            size = os.path.getsize(out) / 1024
            print(f"✅ Title card test passed: {out} ({size:.0f} KB)")
        else:
            print("❌ Title card test failed")
