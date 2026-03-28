"""
effects.py — Advanced video effects module for Tubee
All effects use FFmpeg subprocess calls for reliability and speed.

Effects:
  1. Zoom Punch (beat-synced)
  2. Speed Ramp
  3. RGB Split / Chromatic Aberration
  4. Film Grain
  5. Color Grade Presets (Cole Bennett, Cinematic, Vintage, B&W, Neon)
  6. Shake Effect
  7. Flash/Strobe
  8. Vignette
  9. Letterbox / Aspect Bars
  10. Text Overlay
  + Combo style presets
"""

import os
import json
import logging
import subprocess
import tempfile
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_video_info(path: str) -> dict:
    """Get video duration, width, height, fps via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    data = json.loads(result.stdout)
    info = {
        "duration": float(data.get("format", {}).get("duration", 0)),
    }
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            info["width"] = int(s.get("width", 1080))
            info["height"] = int(s.get("height", 1920))
            # Parse fps from r_frame_rate (e.g. "30/1")
            rfr = s.get("r_frame_rate", "30/1")
            try:
                num, den = rfr.split("/")
                info["fps"] = round(int(num) / int(den), 3)
            except Exception:
                info["fps"] = 30.0
            break
    return info


def _run_ffmpeg(cmd: list, timeout: int = 600) -> bool:
    """Run an FFmpeg command. Returns True on success."""
    logger.debug(f"FFmpeg: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        logger.error(f"FFmpeg failed: {result.stderr[-800:]}")
        return False
    return True


def _safe_output(func):
    """Decorator: return output_path on success, None on any exception."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            return None
    return wrapper


# ---------------------------------------------------------------------------
# 1. Zoom Punch (beat-synced zoom in/out)
# ---------------------------------------------------------------------------

@_safe_output
def apply_zoom_punch(
    input_path: str,
    output_path: str,
    zoom_timestamps: List[float] = None,
    intensity: float = 1.3,
) -> Optional[str]:
    """
    Apply quick zoom-in punches at specified timestamps (beat hits).

    Uses FFmpeg zoompan with sendcmd to keyframe zoom values.
    Each beat gets a fast zoom in (1.0→intensity) then snap back over ~0.15s.

    Args:
        input_path: Source video path.
        output_path: Destination path.
        zoom_timestamps: List of timestamps (seconds) to apply zoom punch.
        intensity: Max zoom level (1.3 = 30% zoom in).

    Returns:
        output_path on success, None on failure.
    """
    if not zoom_timestamps:
        # No timestamps — just copy
        _run_ffmpeg(["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path])
        return output_path

    info = _get_video_info(input_path)
    w = info.get("width", 1080)
    h = info.get("height", 1920)
    fps = info.get("fps", 30)
    duration = info.get("duration", 10)

    # Build a complex zoompan expression
    # zoompan evaluates per-frame: 'on' is the output frame number
    # We build an expression that checks if current time is near a beat
    punch_dur_frames = int(fps * 0.15)  # ~0.15s punch duration

    # Build zoom expression: for each beat, if we're within punch_dur_frames,
    # interpolate zoom. Otherwise zoom=1.
    # Expression: zoom = max(1, <beat1_expr>, <beat2_expr>, ...)
    beat_exprs = []
    for ts in zoom_timestamps:
        frame_start = int(ts * fps)
        # Triangle: ramp up then down over punch_dur_frames*2
        half = max(punch_dur_frames, 1)
        # dist = abs(on - frame_center), zoom = intensity - (intensity-1) * dist / half
        expr = (
            f"if(lt(abs(on-{frame_start}),{half}),"
            f"{intensity}-({intensity}-1)*abs(on-{frame_start})/{half},1)"
        )
        beat_exprs.append(expr)

    if beat_exprs:
        zoom_expr = "max(" + ",".join(["1"] + beat_exprs) + ")"
    else:
        zoom_expr = "1"

    total_frames = int(duration * fps)

    # zoompan: z=zoom expression, d=total frames, s=resolution
    # x/y center the crop
    filter_str = (
        f"zoompan=z='{zoom_expr}':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:"
        f"s={w}x{h}:"
        f"fps={fps}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# ---------------------------------------------------------------------------
# 2. Speed Ramp
# ---------------------------------------------------------------------------

@_safe_output
def apply_speed_ramp(
    input_path: str,
    output_path: str,
    slow_start: float,
    slow_end: float,
    slow_factor: float = 0.5,
) -> Optional[str]:
    """
    Apply speed ramp: slow motion between slow_start and slow_end, normal speed elsewhere.

    Uses FFmpeg trim + setpts + concat approach for precise control.

    Args:
        input_path: Source video.
        output_path: Destination.
        slow_start: Start of slow-mo section (seconds).
        slow_end: End of slow-mo section (seconds).
        slow_factor: Speed multiplier for slow section (0.5 = half speed).

    Returns:
        output_path on success, None on failure.
    """
    info = _get_video_info(input_path)
    duration = info.get("duration", 0)

    # PTS factor: to slow down, multiply PTS. slow_factor=0.5 means 2x PTS.
    pts_factor = 1.0 / slow_factor  # e.g. 0.5 speed → 2.0 PTS multiplier
    atempo = slow_factor  # audio tempo adjustment

    # Handle atempo limits (0.5 to 2.0) — chain if needed
    atempo_filters = []
    remaining = atempo
    while remaining < 0.5:
        atempo_filters.append("atempo=0.5")
        remaining /= 0.5
    while remaining > 2.0:
        atempo_filters.append("atempo=2.0")
        remaining /= 2.0
    atempo_filters.append(f"atempo={remaining:.4f}")
    atempo_chain = ",".join(atempo_filters)

    # Build filter_complex: 3 segments (before, slow, after)
    # Each segment: trim → setpts → output
    fc = (
        # Segment 1: before slow section
        f"[0:v]trim=0:{slow_start},setpts=PTS-STARTPTS[v0];"
        f"[0:a]atrim=0:{slow_start},asetpts=PTS-STARTPTS[a0];"
        # Segment 2: slow section
        f"[0:v]trim={slow_start}:{slow_end},setpts={pts_factor}*(PTS-STARTPTS)[v1];"
        f"[0:a]atrim={slow_start}:{slow_end},asetpts=PTS-STARTPTS,{atempo_chain}[a1];"
        # Segment 3: after slow section
        f"[0:v]trim={slow_end},setpts=PTS-STARTPTS[v2];"
        f"[0:a]atrim={slow_end},asetpts=PTS-STARTPTS[a2];"
        # Concatenate
        f"[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[vout][aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# ---------------------------------------------------------------------------
# 3. RGB Split / Chromatic Aberration
# ---------------------------------------------------------------------------

@_safe_output
def apply_rgb_split(
    input_path: str,
    output_path: str,
    offset: int = 5,
) -> Optional[str]:
    """
    Apply RGB channel split (chromatic aberration) for a music video look.

    Uses FFmpeg rgbashift filter to offset R/G/B channels.

    Args:
        input_path: Source video.
        output_path: Destination.
        offset: Pixel offset for channel separation (default 5).

    Returns:
        output_path on success, None on failure.
    """
    # rgbashift: shift red and blue channels in opposite directions
    filter_str = f"rgbashift=rh={offset}:rv={offset}:bh=-{offset}:bv=-{offset}:gh=0:gv=0"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# ---------------------------------------------------------------------------
# 4. Film Grain
# ---------------------------------------------------------------------------

@_safe_output
def apply_film_grain(
    input_path: str,
    output_path: str,
    intensity: int = 15,
) -> Optional[str]:
    """
    Add film grain for a cinematic feel.

    Uses FFmpeg noise filter.

    Args:
        input_path: Source video.
        output_path: Destination.
        intensity: Grain intensity (0-100, default 15).

    Returns:
        output_path on success, None on failure.
    """
    # noise filter: alls=intensity applies to all planes, allf=t for temporal noise
    filter_str = f"noise=alls={intensity}:allf=t+u"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# ---------------------------------------------------------------------------
# 5. Color Grade Presets
# ---------------------------------------------------------------------------

@_safe_output
def grade_cole_bennett(input_path: str, output_path: str) -> Optional[str]:
    """
    Cole Bennett style: high saturation, vibrant, punchy contrast, warm tones.
    Think Lyrical Lemonade music videos — super colorful and poppy.
    """
    filter_str = (
        "eq=contrast=1.3:brightness=0.05:saturation=1.8:gamma=0.95,"
        "colorbalance=rs=0.15:gs=0.05:bs=-0.1:rm=0.1:gm=0.02:bm=-0.05:"
        "rh=0.08:gh=0.0:bh=-0.08,"
        "unsharp=5:5:0.8:5:5:0.0,"
        "curves=m='0/0 0.25/0.20 0.5/0.55 0.75/0.85 1/1'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


@_safe_output
def grade_cinematic(input_path: str, output_path: str) -> Optional[str]:
    """
    Cinematic teal & orange grade: crushed blacks, filmic color split.
    Classic Hollywood blockbuster look.
    """
    filter_str = (
        "eq=contrast=1.15:brightness=-0.03:saturation=1.1:gamma=1.05,"
        # Push shadows toward teal, highlights toward orange
        "colorbalance=rs=-0.12:gs=-0.02:bs=0.15:rm=0.0:gm=0.0:bm=0.0:"
        "rh=0.15:gh=0.05:bh=-0.12,"
        # Crush blacks, slightly roll off highlights
        "curves=m='0/0.03 0.15/0.08 0.5/0.50 0.85/0.88 1/0.97'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


@_safe_output
def grade_vintage(input_path: str, output_path: str) -> Optional[str]:
    """
    Vintage/retro: faded, warm, low saturation, lifted blacks.
    Think old film stock or Instagram Valencia filter.
    """
    filter_str = (
        "eq=contrast=0.9:brightness=0.04:saturation=0.65:gamma=1.1,"
        # Warm shift across the board
        "colorbalance=rs=0.12:gs=0.05:bs=-0.08:rm=0.08:gm=0.03:bm=-0.05:"
        "rh=0.05:gh=0.02:bh=-0.03,"
        # Lifted blacks (shadows don't go full black), soft highlights
        "curves=m='0/0.10 0.25/0.22 0.5/0.50 0.75/0.76 1/0.93'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


@_safe_output
def grade_bw_contrast(input_path: str, output_path: str) -> Optional[str]:
    """
    High-contrast black and white. Dramatic, editorial look.
    """
    filter_str = (
        # Convert to grayscale, then boost contrast
        "hue=s=0,"
        "eq=contrast=1.5:brightness=-0.02:gamma=0.9,"
        "curves=m='0/0 0.2/0.05 0.5/0.55 0.8/0.95 1/1',"
        "unsharp=5:5:1.0:5:5:0.0"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


@_safe_output
def grade_neon(input_path: str, output_path: str) -> Optional[str]:
    """
    Neon: boosted neon colors, high vibrance, electric feel.
    Great for nightlife, club, and electronic music videos.
    """
    filter_str = (
        "eq=contrast=1.25:brightness=0.02:saturation=2.2:gamma=0.9,"
        # Push colors to extremes
        "colorbalance=rs=0.08:gs=-0.05:bs=0.15:rm=-0.05:gm=0.1:bm=0.08:"
        "rh=0.1:gh=-0.05:bh=0.12,"
        "curves=m='0/0 0.2/0.15 0.5/0.55 0.8/0.90 1/1',"
        "unsharp=5:5:0.6:5:5:0.0"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# Map preset names to grade functions
COLOR_GRADE_PRESETS = {
    "cole_bennett": grade_cole_bennett,
    "cinematic": grade_cinematic,
    "vintage": grade_vintage,
    "bw_contrast": grade_bw_contrast,
    "neon": grade_neon,
}


# ---------------------------------------------------------------------------
# 6. Shake Effect
# ---------------------------------------------------------------------------

@_safe_output
def apply_shake(
    input_path: str,
    output_path: str,
    intensity: int = 5,
    frequency: int = 30,
) -> Optional[str]:
    """
    Simulated camera shake for energy/impact.

    Uses FFmpeg crop with random offsets to simulate handheld shake.
    Slightly zooms in to allow room for offset without black borders.

    Args:
        input_path: Source video.
        output_path: Destination.
        intensity: Max pixel displacement (default 5).
        frequency: How often shake updates — tied to frame evaluation (default 30).

    Returns:
        output_path on success, None on failure.
    """
    info = _get_video_info(input_path)
    w = info.get("width", 1080)
    h = info.get("height", 1920)

    # Pad/scale up slightly to allow shake room, then crop back to original size
    pad = intensity * 2
    scale_w = w + pad * 2
    scale_h = h + pad * 2

    # Random offset using FFmpeg expressions
    # random(0) gives a pseudo-random value 0-1 per frame
    shake_x = f"{pad}+{intensity}*sin(n*{frequency}*0.1)*random(0)"
    shake_y = f"{pad}+{intensity}*cos(n*{frequency}*0.13)*random(1)"

    filter_str = (
        f"scale={scale_w}:{scale_h},"
        f"crop={w}:{h}:'{shake_x}':'{shake_y}'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# ---------------------------------------------------------------------------
# 7. Flash / Strobe
# ---------------------------------------------------------------------------

@_safe_output
def apply_flash(
    input_path: str,
    output_path: str,
    flash_timestamps: List[float] = None,
) -> Optional[str]:
    """
    Add quick white flash frames at specified timestamps (beat hits).

    Uses FFmpeg geq filter with enable expressions to flash white at specific times.

    Args:
        input_path: Source video.
        output_path: Destination.
        flash_timestamps: List of timestamps (seconds) for flash frames.

    Returns:
        output_path on success, None on failure.
    """
    if not flash_timestamps:
        _run_ffmpeg(["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path])
        return output_path

    # Build enable expression: flash lasts ~2 frames (~0.066s at 30fps)
    flash_dur = 0.066

    # Build a drawbox=white covering the whole frame, enabled at flash timestamps
    # Use multiple drawbox filters chained together
    # For efficiency, build a single enable expression with OR conditions
    conditions = []
    for ts in flash_timestamps:
        conditions.append(f"between(t,{ts:.3f},{ts + flash_dur:.3f})")

    enable_expr = "+".join(conditions)

    # Use geq to flash white: when condition is met, output white; otherwise pass through
    # More reliable approach: overlay a white frame with enable
    filter_str = (
        f"drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:"
        f"enable='{enable_expr}'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# ---------------------------------------------------------------------------
# 8. Vignette
# ---------------------------------------------------------------------------

@_safe_output
def apply_vignette(
    input_path: str,
    output_path: str,
    intensity: float = 0.3,
) -> Optional[str]:
    """
    Apply vignette (dark edges) for a cinematic look.

    Args:
        input_path: Source video.
        output_path: Destination.
        intensity: Vignette angle/strength. Higher = darker edges. (default 0.3)
                   Maps to FFmpeg vignette angle parameter (PI * intensity).

    Returns:
        output_path on success, None on failure.
    """
    # FFmpeg vignette filter: angle is in radians, PI/5 is moderate
    # We map intensity 0-1 to angle range
    angle = f"PI*{intensity:.2f}"

    filter_str = f"vignette=angle={angle}:mode=forward"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# ---------------------------------------------------------------------------
# 9. Letterbox / Aspect Bars
# ---------------------------------------------------------------------------

@_safe_output
def apply_letterbox(
    input_path: str,
    output_path: str,
    ratio: str = "2.35:1",
) -> Optional[str]:
    """
    Add cinematic letterbox bars (black bars top/bottom).

    Args:
        input_path: Source video.
        output_path: Destination.
        ratio: Target aspect ratio string (e.g. "2.35:1", "21:9", "1.85:1").

    Returns:
        output_path on success, None on failure.
    """
    info = _get_video_info(input_path)
    w = info.get("width", 1080)
    h = info.get("height", 1920)

    # Parse aspect ratio
    if ":" in ratio:
        parts = ratio.split(":")
        target_ar = float(parts[0]) / float(parts[1])
    else:
        target_ar = float(ratio)

    current_ar = w / h

    if current_ar > target_ar:
        # Video is wider than target — add bars on sides (pillarbox)
        new_w = int(h * target_ar)
        new_w = new_w + (new_w % 2)  # Ensure even
        filter_str = (
            f"scale={new_w}:{h},"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"
        )
    else:
        # Video is taller than target — add bars on top/bottom (letterbox)
        new_h = int(w / target_ar)
        new_h = new_h + (new_h % 2)  # Ensure even
        filter_str = (
            f"scale={w}:{new_h},"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# ---------------------------------------------------------------------------
# 10. Text Overlay
# ---------------------------------------------------------------------------

@_safe_output
def apply_text(
    input_path: str,
    output_path: str,
    text: str,
    position: str = "center",
    font_size: int = 72,
    color: str = "white",
    start_time: float = 0,
    duration: float = 2,
) -> Optional[str]:
    """
    Animated text overlay with fade-in/fade-out.

    Args:
        input_path: Source video.
        output_path: Destination.
        text: Text to display.
        position: "center", "top", "bottom", "top-left", "bottom-right", etc.
        font_size: Font size in pixels.
        color: Text color (FFmpeg color name or hex).
        start_time: When text appears (seconds).
        duration: How long text is visible (seconds).

    Returns:
        output_path on success, None on failure.
    """
    # Escape special characters for FFmpeg drawtext
    safe_text = text.replace("'", "'\\\\\\''").replace(":", "\\:")
    safe_text = safe_text.replace("%", "%%")

    # Position mapping
    pos_map = {
        "center": "x=(w-text_w)/2:y=(h-text_h)/2",
        "top": "x=(w-text_w)/2:y=h*0.08",
        "bottom": "x=(w-text_w)/2:y=h*0.88",
        "top-left": "x=w*0.05:y=h*0.05",
        "top-right": "x=w*0.95-text_w:y=h*0.05",
        "bottom-left": "x=w*0.05:y=h*0.92",
        "bottom-right": "x=w*0.95-text_w:y=h*0.92",
    }
    pos_expr = pos_map.get(position, pos_map["center"])

    end_time = start_time + duration
    fade_dur = min(0.3, duration / 4)  # 0.3s fade, or shorter for brief text

    # Alpha fade in/out expression
    alpha_expr = (
        f"if(lt(t,{start_time}),0,"
        f"if(lt(t,{start_time + fade_dur}),"
        f"(t-{start_time})/{fade_dur},"
        f"if(lt(t,{end_time - fade_dur}),1,"
        f"if(lt(t,{end_time}),"
        f"({end_time}-t)/{fade_dur},0))))"
    )

    filter_str = (
        f"drawtext=text='{safe_text}':"
        f"fontsize={font_size}:"
        f"fontcolor={color}:"
        f"{pos_expr}:"
        f"alpha='{alpha_expr}':"
        f"shadowcolor=black@0.6:shadowx=2:shadowy=2"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_str,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    if _run_ffmpeg(cmd):
        return output_path
    return None


# ---------------------------------------------------------------------------
# Combo: Style Presets
# ---------------------------------------------------------------------------

def apply_style_preset(
    input_path: str,
    output_path: str,
    preset: str = "cole_bennett",
    beat_timestamps: List[float] = None,
) -> Optional[str]:
    """
    Apply a full style preset: combines color grade + zoom punches on beats +
    film grain + vignette into one cohesive look.

    Presets:
        - "cole_bennett": Vibrant + zoom punches + light grain + flash on beats
        - "cinematic": Teal/orange + vignette + grain + letterbox
        - "vintage": Faded warm + heavy grain + vignette
        - "clean": Subtle grade + vignette only (no grain, no effects)
        - "neon": Neon colors + RGB split + flash on beats

    Args:
        input_path: Source video.
        output_path: Final output path.
        preset: Preset name.
        beat_timestamps: Beat timestamps for beat-synced effects.

    Returns:
        output_path on success, None on failure.
    """
    if beat_timestamps is None:
        beat_timestamps = []

    # Define effect chains per preset
    preset_configs = {
        "cole_bennett": {
            "grade": grade_cole_bennett,
            "grain": 8,
            "vignette": 0.2,
            "zoom_beats": True,
            "zoom_intensity": 1.3,
            "flash_beats": True,
            "rgb_split": 0,
            "letterbox": None,
        },
        "cinematic": {
            "grade": grade_cinematic,
            "grain": 12,
            "vignette": 0.35,
            "zoom_beats": False,
            "zoom_intensity": 1.0,
            "flash_beats": False,
            "rgb_split": 0,
            "letterbox": "2.35:1",
        },
        "vintage": {
            "grade": grade_vintage,
            "grain": 20,
            "vignette": 0.4,
            "zoom_beats": False,
            "zoom_intensity": 1.0,
            "flash_beats": False,
            "rgb_split": 0,
            "letterbox": None,
        },
        "clean": {
            "grade": grade_cinematic,  # Subtle grade
            "grain": 0,
            "vignette": 0.2,
            "zoom_beats": False,
            "zoom_intensity": 1.0,
            "flash_beats": False,
            "rgb_split": 0,
            "letterbox": None,
        },
        "neon": {
            "grade": grade_neon,
            "grain": 5,
            "vignette": 0.15,
            "zoom_beats": True,
            "zoom_intensity": 1.2,
            "flash_beats": True,
            "rgb_split": 4,
            "letterbox": None,
        },
    }

    config = preset_configs.get(preset)
    if not config:
        logger.error(f"Unknown style preset: {preset}")
        return None

    # Apply effects in sequence using temp files
    # Order: grade → effects (zoom/flash/rgb) → grain → vignette → letterbox
    try:
        with tempfile.TemporaryDirectory(prefix="tubee_fx_") as tmp_dir:
            current = input_path
            step = 0

            def next_tmp():
                nonlocal step
                step += 1
                return os.path.join(tmp_dir, f"step_{step:02d}.mp4")

            # 1. Color grade
            if config["grade"]:
                tmp_out = next_tmp()
                result = config["grade"](current, tmp_out)
                if result:
                    current = result
                else:
                    logger.warning(f"Grade step failed for preset {preset}, continuing")

            # 2. Zoom punches on beats
            if config["zoom_beats"] and beat_timestamps:
                tmp_out = next_tmp()
                result = apply_zoom_punch(
                    current, tmp_out,
                    zoom_timestamps=beat_timestamps,
                    intensity=config["zoom_intensity"],
                )
                if result:
                    current = result

            # 3. Flash on beats
            if config["flash_beats"] and beat_timestamps:
                tmp_out = next_tmp()
                result = apply_flash(current, tmp_out, flash_timestamps=beat_timestamps)
                if result:
                    current = result

            # 4. RGB split
            if config["rgb_split"] > 0:
                tmp_out = next_tmp()
                result = apply_rgb_split(current, tmp_out, offset=config["rgb_split"])
                if result:
                    current = result

            # 5. Film grain
            if config["grain"] > 0:
                tmp_out = next_tmp()
                result = apply_film_grain(current, tmp_out, intensity=config["grain"])
                if result:
                    current = result

            # 6. Vignette
            if config["vignette"] > 0:
                tmp_out = next_tmp()
                result = apply_vignette(current, tmp_out, intensity=config["vignette"])
                if result:
                    current = result

            # 7. Letterbox
            if config["letterbox"]:
                tmp_out = next_tmp()
                result = apply_letterbox(current, tmp_out, ratio=config["letterbox"])
                if result:
                    current = result

            # Copy final result to output
            if current == input_path:
                # Nothing was applied successfully — just copy
                _run_ffmpeg(["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path])
            else:
                import shutil
                shutil.copy2(current, output_path)

            if os.path.exists(output_path):
                logger.info(f"Style preset '{preset}' applied → {output_path}")
                return output_path

    except Exception as e:
        logger.error(f"Style preset '{preset}' failed: {e}")

    return None


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Quick validation: check FFmpeg is available
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True
        )
        version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
        print(f"✅ FFmpeg found: {version_line}")
    except FileNotFoundError:
        print("❌ FFmpeg not found! Install it first.")
        sys.exit(1)

    # Check for rgbashift filter support
    result = subprocess.run(
        ["ffmpeg", "-filters"], capture_output=True, text=True
    )
    filters_available = result.stdout if result.stdout else ""

    effects_check = {
        "rgbashift": "RGB Split",
        "noise": "Film Grain",
        "vignette": "Vignette",
        "zoompan": "Zoom Punch",
        "drawtext": "Text Overlay",
        "drawbox": "Flash/Strobe",
        "colorbalance": "Color Grading",
    }

    print("\n📋 Filter availability:")
    for filt, name in effects_check.items():
        available = filt in filters_available
        status = "✅" if available else "⚠️ "
        print(f"  {status} {name} ({filt})")

    print("\n🎬 Effects module loaded successfully!")
    print(f"   Available presets: {list(preset_configs.keys()) if 'preset_configs' in dir() else list(COLOR_GRADE_PRESETS.keys())}")
    print(f"   Color grades: {list(COLOR_GRADE_PRESETS.keys())}")
