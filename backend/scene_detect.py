"""
scene_detect.py — PySceneDetect wrapper for Tubee
Detects scene cuts in a video file and returns a list of scene timestamps.
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def detect_scenes(video_path: str, threshold: float = 27.0) -> List[Dict[str, Any]]:
    """
    Detect scenes in a video file using PySceneDetect.

    Args:
        video_path: Path to the input video file.
        threshold: Content detection threshold (lower = more sensitive, default 27.0).

    Returns:
        List of scene dicts, each with:
            - scene_num (int): 1-indexed scene number
            - start_time (float): Start time in seconds
            - end_time (float): End time in seconds
            - duration (float): Duration in seconds
            - start_frame (int): Start frame number
            - end_frame (int): End frame number
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    logger.info(f"Detecting scenes in: {video_path}")

    try:
        from scenedetect import VideoManager, SceneManager
        from scenedetect.detectors import ContentDetector

        video_manager = VideoManager([video_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))

        # Improve performance by downscaling before detection
        video_manager.set_downscale_factor(4)  # Faster detection with downscaling
        video_manager.start()

        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()

        video_manager.release()

        scenes = []
        for i, (start, end) in enumerate(scene_list):
            scene = {
                "scene_num": i + 1,
                "start_time": start.get_seconds(),
                "end_time": end.get_seconds(),
                "duration": end.get_seconds() - start.get_seconds(),
                "start_frame": start.get_frames(),
                "end_frame": end.get_frames(),
            }
            scenes.append(scene)
            logger.debug(
                f"Scene {i+1}: {scene['start_time']:.2f}s — {scene['end_time']:.2f}s "
                f"({scene['duration']:.2f}s)"
            )

        logger.info(f"Found {len(scenes)} scenes in {video_path}")
        return scenes

    except ImportError:
        logger.warning("PySceneDetect not available, falling back to FFprobe-based detection")
        return _fallback_scene_detect(video_path)


def _fallback_scene_detect(video_path: str, min_scene_duration: float = 2.0) -> List[Dict[str, Any]]:
    """
    Fallback scene detection using FFprobe scene filter.
    Used when PySceneDetect is not installed.

    Args:
        video_path: Path to the input video file.
        min_scene_duration: Minimum scene duration in seconds.

    Returns:
        List of scene dicts (same format as detect_scenes).
    """
    import subprocess
    import json

    logger.info("Using FFprobe fallback for scene detection")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFprobe failed: {result.stderr}")

    info = json.loads(result.stdout)
    video_stream = next(
        (s for s in info.get("streams", []) if s.get("codec_type") == "video"), None
    )
    if not video_stream:
        raise RuntimeError("No video stream found in file")

    # Get total duration
    duration = float(video_stream.get("duration", 0))
    if duration == 0:
        # Try container duration
        cmd2 = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", video_path,
        ]
        r2 = subprocess.run(cmd2, capture_output=True, text=True)
        fmt = json.loads(r2.stdout)
        duration = float(fmt.get("format", {}).get("duration", 0))

    # Detect scene change timestamps using FFmpeg scene filter
    cmd3 = [
        "ffmpeg", "-i", video_path,
        "-vf", "select='gt(scene,0.3)',showinfo",
        "-vsync", "vfr",
        "-f", "null", "-",
    ]
    r3 = subprocess.run(cmd3, capture_output=True, text=True)

    # Parse scene timestamps from showinfo output
    cut_times = [0.0]
    for line in r3.stderr.splitlines():
        if "pts_time:" in line:
            try:
                pts_str = line.split("pts_time:")[1].split()[0]
                t = float(pts_str)
                if t - cut_times[-1] >= min_scene_duration:
                    cut_times.append(t)
            except (IndexError, ValueError):
                continue

    if duration > 0:
        cut_times.append(duration)

    # Build scene list from cut times
    scenes = []
    for i in range(len(cut_times) - 1):
        start = cut_times[i]
        end = cut_times[i + 1]
        scene_duration = end - start
        if scene_duration >= min_scene_duration:
            scenes.append({
                "scene_num": len(scenes) + 1,
                "start_time": start,
                "end_time": end,
                "duration": scene_duration,
                "start_frame": int(start * 30),   # Approximate frame count
                "end_frame": int(end * 30),
            })

    # If no scenes were detected, treat entire video as one scene
    if not scenes and duration > 0:
        scenes = [{
            "scene_num": 1,
            "start_time": 0.0,
            "end_time": duration,
            "duration": duration,
            "start_frame": 0,
            "end_frame": int(duration * 30),
        }]

    logger.info(f"Fallback detection found {len(scenes)} scenes")
    return scenes


if __name__ == "__main__":
    import sys
    import json

    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python scene_detect.py <video_file>")
        sys.exit(1)

    result = detect_scenes(sys.argv[1])
    print(json.dumps(result, indent=2))
