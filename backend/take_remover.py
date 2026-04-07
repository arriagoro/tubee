"""
take_remover.py — Remove bad takes from video clips and concatenate good ones.

Uses FFmpeg to cut and concatenate only the good takes based on analysis results.
"""

import os
import json
import logging
import subprocess
import tempfile
from typing import List, Dict, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

FFMPEG = os.environ.get("FFMPEG_PATH", "/opt/homebrew/bin/ffmpeg")


def remove_bad_takes(
    video_files: List[str],
    analysis: Dict,
    output_path: str,
    aggressiveness: float = 0.5,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> str:
    """
    Remove bad takes from videos and concatenate remaining good takes.

    aggressiveness: 0.0 = keep everything, 1.0 = remove anything below 0.9 score

    The threshold is calculated as:
      threshold = 0.3 + (aggressiveness * 0.6)
      - aggressiveness 0.0 → threshold 0.3 (very lenient, only removes terrible takes)
      - aggressiveness 0.5 → threshold 0.6 (balanced)
      - aggressiveness 1.0 → threshold 0.9 (very strict, only keeps excellent takes)

    Returns: path to output video with bad takes removed
    """
    if progress_callback:
        progress_callback("Filtering takes", 10)

    # Calculate quality threshold from aggressiveness
    threshold = 0.3 + (aggressiveness * 0.6)
    logger.info(f"Take removal: aggressiveness={aggressiveness}, threshold={threshold:.2f}")

    takes = analysis.get("takes", [])

    # Build a map of filename → video_path
    file_to_path = {}
    for vf in video_files:
        fname = Path(vf).name
        file_to_path[fname] = vf

    # Filter takes: keep those above threshold OR explicitly marked "keep"
    good_takes = []
    removed_takes = []

    for take in takes:
        score = take.get("quality_score", 0.5)
        recommendation = take.get("recommendation", "keep")
        filename = take.get("file", "")

        # Apply aggressiveness-adjusted threshold
        if score >= threshold or (aggressiveness < 0.3 and recommendation == "keep"):
            if filename in file_to_path:
                good_takes.append({
                    "file": filename,
                    "path": file_to_path[filename],
                    "score": score,
                })
        else:
            removed_takes.append({
                "file": filename,
                "score": score,
                "reason": take.get("reason", "Below quality threshold"),
            })

    # If no good takes remain, keep the best one at minimum
    if not good_takes and takes:
        best_take = max(takes, key=lambda t: t.get("quality_score", 0))
        filename = best_take.get("file", "")
        if filename in file_to_path:
            good_takes.append({
                "file": filename,
                "path": file_to_path[filename],
                "score": best_take.get("quality_score", 0),
            })
            removed_takes = [t for t in removed_takes if t["file"] != filename]
            logger.warning("All takes below threshold — keeping best one")

    # If analysis has no takes data, include all video files
    if not takes:
        logger.warning("No take analysis data — keeping all clips")
        good_takes = [
            {"file": Path(vf).name, "path": vf, "score": 0.5}
            for vf in video_files
        ]

    logger.info(f"Keeping {len(good_takes)} takes, removing {len(removed_takes)}")

    if progress_callback:
        progress_callback(f"Keeping {len(good_takes)} takes, removing {len(removed_takes)}", 30)

    if len(good_takes) == 0:
        raise ValueError("No takes to keep — cannot create output video")

    if len(good_takes) == 1:
        # Single clip — just copy it
        if progress_callback:
            progress_callback("Copying single good take", 60)

        cmd = [
            FFMPEG, "-y", "-i", good_takes[0]["path"],
            "-c", "copy", output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            # Try re-encoding if copy fails
            cmd = [
                FFMPEG, "-y", "-i", good_takes[0]["path"],
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if progress_callback:
            progress_callback("Complete", 100)

        return output_path

    # Multiple good takes — concatenate them
    if progress_callback:
        progress_callback("Concatenating good takes", 40)

    # First, normalize all clips to the same format for concat
    temp_dir = tempfile.mkdtemp(prefix="take_concat_")
    normalized_paths = []

    try:
        for i, take in enumerate(good_takes):
            pct = int(40 + (i / len(good_takes)) * 40)
            if progress_callback:
                progress_callback(f"Normalizing clip {i+1}/{len(good_takes)}", pct)

            norm_path = os.path.join(temp_dir, f"norm_{i:03d}.mp4")

            # Normalize: same codec, frame rate, and audio sample rate
            cmd = [
                FFMPEG, "-y", "-i", take["path"],
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-r", "30",  # normalize frame rate
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart",
                norm_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0 and os.path.exists(norm_path):
                normalized_paths.append(norm_path)
            else:
                logger.warning(f"Failed to normalize {take['file']}, trying direct copy")
                # Fallback: try stream copy
                cmd_copy = [
                    FFMPEG, "-y", "-i", take["path"],
                    "-c", "copy", norm_path,
                ]
                result2 = subprocess.run(cmd_copy, capture_output=True, text=True, timeout=300)
                if result2.returncode == 0 and os.path.exists(norm_path):
                    normalized_paths.append(norm_path)

        if not normalized_paths:
            raise ValueError("Failed to normalize any clips for concatenation")

        # Create concat file list
        concat_list_path = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_list_path, "w") as f:
            for p in normalized_paths:
                # FFmpeg concat demuxer requires escaped paths
                escaped = p.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")

        if progress_callback:
            progress_callback("Joining clips", 85)

        # Concatenate
        cmd = [
            FFMPEG, "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",
            "-movflags", "+faststart",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            logger.warning(f"Concat copy failed, trying re-encode: {result.stderr[:200]}")
            cmd = [
                FFMPEG, "-y", "-f", "concat", "-safe", "0",
                "-i", concat_list_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)

        if not os.path.exists(output_path):
            raise ValueError(f"FFmpeg concat failed: {result.stderr[:300]}")

        if progress_callback:
            progress_callback("Take removal complete", 100)

        return output_path

    finally:
        # Cleanup temp files
        import shutil
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
