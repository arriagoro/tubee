"""
frame_extractor.py — Extract key frames from video clips for Kimi K2 visual analysis.

Pulls frames at 10%, 50%, and 90% of each clip so the AI can actually SEE the footage
before making edit decisions. Frames are kept small (max 512px wide) to save tokens.
"""

import os
import uuid
import json
import base64
import logging
import subprocess
import shutil
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Limits to keep API costs sane
MAX_FRAMES_PER_CLIP = 3
MAX_CLIPS = 15  # max 15 clips × 3 frames = 45 frames max
MAX_WIDTH = 512  # pixels — keeps base64 payloads small
FRAME_POSITIONS = [0.10, 0.50, 0.90]  # start, middle, end


def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using FFprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return 0.0
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0.0))
    except Exception:
        return 0.0


def extract_key_frames(
    video_files: List[str],
    max_frames_per_clip: int = MAX_FRAMES_PER_CLIP,
    job_id: Optional[str] = None,
) -> Dict[str, List[str]]:
    """
    Extract key frames from each video clip for visual analysis.

    Pulls frames at 10%, 50%, and 90% of each clip's duration.
    Saves to /tmp/tubee_frames/{job_id}/ as small JPEGs (max 512px wide).

    Args:
        video_files: List of video file paths.
        max_frames_per_clip: Max frames to extract per clip (default 3).
        job_id: Optional job ID for organizing temp files.

    Returns:
        Dict mapping video_path → [frame_path1, frame_path2, ...]
    """
    if job_id is None:
        job_id = str(uuid.uuid4())[:8]

    frames_dir = Path(f"/tmp/tubee_frames/{job_id}")
    frames_dir.mkdir(parents=True, exist_ok=True)

    result: Dict[str, List[str]] = {}
    clips_processed = 0

    for video_path in video_files:
        if clips_processed >= MAX_CLIPS:
            logger.info(f"Hit max clips limit ({MAX_CLIPS}), skipping remaining files")
            break

        if not os.path.exists(video_path):
            logger.warning(f"Video file not found: {video_path}")
            continue

        duration = _get_video_duration(video_path)
        if duration <= 0:
            logger.warning(f"Could not get duration for {video_path}, skipping")
            continue

        video_name = Path(video_path).stem
        frame_paths: List[str] = []

        # Extract frames at configured positions (10%, 50%, 90%)
        positions = FRAME_POSITIONS[:max_frames_per_clip]

        for i, pos in enumerate(positions):
            timestamp = duration * pos
            frame_filename = f"{video_name}_frame_{i}_{pos:.0%}.jpg"
            frame_path = str(frames_dir / frame_filename)

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                "-vf", f"scale='min({MAX_WIDTH},iw)':-1",
                frame_path,
            ]

            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30,
                )
                if proc.returncode == 0 and os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                    frame_paths.append(frame_path)
                    logger.debug(f"Extracted frame: {frame_filename} @ {timestamp:.1f}s")
                else:
                    logger.warning(f"Frame extraction failed for {video_name} @ {timestamp:.1f}s")
            except subprocess.TimeoutExpired:
                logger.warning(f"Frame extraction timed out for {video_name} @ {timestamp:.1f}s")
            except Exception as e:
                logger.warning(f"Frame extraction error for {video_name}: {e}")

        if frame_paths:
            result[video_path] = frame_paths
            clips_processed += 1
            logger.info(f"Extracted {len(frame_paths)} frames from {Path(video_path).name}")

    total_frames = sum(len(v) for v in result.values())
    logger.info(f"Frame extraction complete: {total_frames} frames from {len(result)} clips")
    return result


def frames_to_base64(frame_paths: List[str]) -> List[dict]:
    """
    Convert frame image files to base64-encoded image_url dicts for API calls.

    Args:
        frame_paths: List of paths to JPEG frame files.

    Returns:
        List of dicts in OpenAI vision format:
        [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}]
    """
    image_contents = []

    for frame_path in frame_paths:
        try:
            with open(frame_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_data}",
                },
            })
        except Exception as e:
            logger.warning(f"Failed to encode frame {frame_path}: {e}")

    return image_contents


def cleanup_frames(job_id: str) -> None:
    """
    Remove temporary frame files for a given job.

    Args:
        job_id: The job ID whose frames should be cleaned up.
    """
    frames_dir = Path(f"/tmp/tubee_frames/{job_id}")
    if frames_dir.exists():
        shutil.rmtree(frames_dir, ignore_errors=True)
        logger.info(f"Cleaned up frames for job {job_id}")


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python frame_extractor.py <video1> [video2 ...]")
        sys.exit(1)

    videos = sys.argv[1:]
    frames = extract_key_frames(videos)
    for video, paths in frames.items():
        print(f"\n{Path(video).name}:")
        for p in paths:
            size_kb = os.path.getsize(p) / 1024
            print(f"  {p} ({size_kb:.1f} KB)")
