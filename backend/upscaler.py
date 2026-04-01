"""
upscaler.py — Video upscaling for Tubee
Supports Real-ESRGAN (AI upscaling) with FFmpeg lanczos fallback.

Usage:
    from upscaler import upscale_video
    result = upscale_video("input.mp4", "output.mp4", scale=4)

Works locally on M4 Mac without any API keys.
"""

import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Check if Real-ESRGAN is available
REALESRGAN_AVAILABLE = False
try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    import cv2
    import numpy as np
    REALESRGAN_AVAILABLE = True
    logger.info("Real-ESRGAN available — AI upscaling enabled")
except ImportError:
    logger.warning("Real-ESRGAN not installed — will use FFmpeg lanczos fallback")


def _get_video_info(video_path: str) -> dict:
    """Get video resolution, fps, and codec info via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    import json
    data = json.loads(result.stdout)

    video_stream = None
    audio_stream = None
    for stream in data.get("streams", []):
        if stream["codec_type"] == "video" and not video_stream:
            video_stream = stream
        elif stream["codec_type"] == "audio" and not audio_stream:
            audio_stream = stream

    if not video_stream:
        raise RuntimeError("No video stream found")

    # Parse fps from r_frame_rate (e.g. "30000/1001")
    fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0

    return {
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "fps": fps,
        "duration": float(data.get("format", {}).get("duration", 0)),
        "has_audio": audio_stream is not None,
    }


def _extract_frames(video_path: str, frames_dir: str, fps: Optional[float] = None) -> int:
    """Extract all frames from video using FFmpeg. Returns frame count."""
    cmd = ["ffmpeg", "-y", "-i", video_path]
    if fps:
        cmd += ["-vf", f"fps={fps}"]
    cmd += [os.path.join(frames_dir, "frame_%06d.png")]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Frame extraction failed: {result.stderr[:500]}")

    frame_count = len([f for f in os.listdir(frames_dir) if f.startswith("frame_")])
    logger.info(f"Extracted {frame_count} frames")
    return frame_count


def _upscale_frames_realesrgan(input_dir: str, output_dir: str, scale: int = 4,
                                progress_callback: Optional[Callable] = None) -> None:
    """Upscale all frames in a directory using Real-ESRGAN."""
    if not REALESRGAN_AVAILABLE:
        raise RuntimeError("Real-ESRGAN not available")

    # Set up the model
    if scale == 2:
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        model_name = "RealESRGAN_x2plus"
    else:
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        model_name = "RealESRGAN_x4plus"

    upsampler = RealESRGANer(
        scale=scale,
        model_path=None,  # Will auto-download
        model=model,
        tile=400,  # Process in tiles to save VRAM
        tile_pad=10,
        pre_pad=0,
        half=False,  # Use full precision on M4 Mac (MPS)
    )

    frames = sorted([f for f in os.listdir(input_dir) if f.startswith("frame_")])
    total = len(frames)

    for i, frame_name in enumerate(frames):
        input_path = os.path.join(input_dir, frame_name)
        output_path = os.path.join(output_dir, frame_name)

        img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            logger.warning(f"Could not read frame: {frame_name}")
            continue

        try:
            output, _ = upsampler.enhance(img, outscale=scale)
            cv2.imwrite(output_path, output)
        except Exception as e:
            logger.warning(f"Real-ESRGAN failed on {frame_name}: {e}, copying original")
            shutil.copy2(input_path, output_path)

        if progress_callback and (i % 10 == 0 or i == total - 1):
            pct = int((i + 1) / total * 100)
            progress_callback(f"Upscaling frame {i+1}/{total}", pct)

    logger.info(f"Upscaled {total} frames with Real-ESRGAN ({scale}x)")


def _reassemble_video(frames_dir: str, output_path: str, fps: float,
                       audio_source: Optional[str] = None) -> None:
    """Reassemble upscaled frames into video with FFmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frames_dir, "frame_%06d.png"),
    ]

    # Add audio from original if present
    if audio_source:
        cmd += ["-i", audio_source, "-map", "0:v", "-map", "1:a", "-shortest"]

    cmd += [
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Video reassembly failed: {result.stderr[:500]}")

    logger.info(f"Reassembled video: {output_path}")


def _upscale_ffmpeg_fallback(input_path: str, output_path: str, scale: int = 4) -> None:
    """Fallback: upscale with FFmpeg's lanczos scaler (no AI, but fast and reliable)."""
    info = _get_video_info(input_path)
    target_w = info["width"] * scale
    target_h = info["height"] * scale

    # Cap at 4K (3840x2160) for 16:9 or equivalent
    max_dim = 3840
    if target_w > max_dim or target_h > max_dim:
        ratio = min(max_dim / target_w, max_dim / target_h)
        target_w = int(target_w * ratio)
        target_h = int(target_h * ratio)

    # Ensure even dimensions (required by most codecs)
    target_w = target_w + (target_w % 2)
    target_h = target_h + (target_h % 2)

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"scale={target_w}:{target_h}:flags=lanczos",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_path
    ]

    logger.info(f"FFmpeg lanczos upscale: {info['width']}x{info['height']} → {target_w}x{target_h}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg upscale failed: {result.stderr[:500]}")


def upscale_video(
    input_path: str,
    output_path: str,
    scale: int = 4,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Upscale a video file.

    Args:
        input_path: Path to the input video file
        output_path: Path for the upscaled output video
        scale: Upscale factor (2 or 4)
        progress_callback: Optional callback(stage: str, pct: int)

    Returns:
        dict with keys: output_path, method, original_resolution, upscaled_resolution
    """
    if scale not in (2, 4):
        raise ValueError(f"Scale must be 2 or 4, got {scale}")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")

    info = _get_video_info(input_path)
    original_res = f"{info['width']}x{info['height']}"

    if progress_callback:
        progress_callback("Analyzing video", 5)

    # Try Real-ESRGAN first, fall back to FFmpeg
    if REALESRGAN_AVAILABLE:
        method = "realesrgan"
        with tempfile.TemporaryDirectory(prefix="tubee_upscale_") as tmpdir:
            raw_frames_dir = os.path.join(tmpdir, "raw")
            upscaled_frames_dir = os.path.join(tmpdir, "upscaled")
            os.makedirs(raw_frames_dir)
            os.makedirs(upscaled_frames_dir)

            if progress_callback:
                progress_callback("Extracting frames", 10)

            _extract_frames(input_path, raw_frames_dir, fps=info["fps"])

            # Upscale each frame
            _upscale_frames_realesrgan(
                raw_frames_dir, upscaled_frames_dir, scale=scale,
                progress_callback=progress_callback,
            )

            if progress_callback:
                progress_callback("Reassembling video", 90)

            # Reassemble with original audio
            audio_source = input_path if info["has_audio"] else None
            _reassemble_video(upscaled_frames_dir, output_path, info["fps"], audio_source)
    else:
        method = "ffmpeg_lanczos"
        if progress_callback:
            progress_callback("Upscaling with FFmpeg (lanczos)", 20)

        _upscale_ffmpeg_fallback(input_path, output_path, scale)

    # Get output info
    out_info = _get_video_info(output_path)
    upscaled_res = f"{out_info['width']}x{out_info['height']}"

    if progress_callback:
        progress_callback("Upscale complete", 100)

    logger.info(f"Upscale complete: {original_res} → {upscaled_res} ({method})")

    return {
        "output_path": output_path,
        "method": method,
        "original_resolution": original_res,
        "upscaled_resolution": upscaled_res,
    }
