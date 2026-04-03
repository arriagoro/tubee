"""
processor.py — Main video processing pipeline for Tubee
Orchestrates: scene detection → beat analysis → AI editing decisions → clip assembly → export

Pipeline:
  1. Receive input video files + optional music file + user prompt
  2. Detect scenes in each video
  3. Detect beats in music (or in first video if no music)
  4. Ask Claude (or fallback) for edit decisions
  5. Cut and assemble clips using moviepy / FFmpeg
  6. Export final MP4 (1080p H.264)
"""

import os
import uuid
import json
import logging
import tempfile
import subprocess
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

from scene_detect import detect_scenes
from beat_sync import detect_beats
from ai_editor import get_edit_decisions
from effects import apply_style_preset, apply_transitions_to_sequence

logger = logging.getLogger(__name__)

# Default export settings — Instagram Reel (9:16 vertical, 1080x1920)
DEFAULT_RESOLUTION = (1080, 1920)  # Instagram Reel / TikTok / Shorts
DEFAULT_FPS = 30

# Aspect ratio presets — width x height for common platforms
ASPECT_RATIOS = {
    "9:16": (1080, 1920),   # Reels / TikTok / Shorts (default)
    "1:1":  (1080, 1080),   # Instagram feed square
    "4:5":  (1080, 1350),   # Instagram feed portrait
    "16:9": (1920, 1080),   # YouTube / landscape
    "4:3":  (1440, 1080),   # Retro / vintage aesthetic
}


def get_resolution(aspect_ratio: Optional[str] = None) -> tuple:
    """
    Get (width, height) for a given aspect ratio string.
    Falls back to 9:16 (vertical) if not found.
    """
    if aspect_ratio and aspect_ratio in ASPECT_RATIOS:
        return ASPECT_RATIOS[aspect_ratio]
    return DEFAULT_RESOLUTION
DEFAULT_VIDEO_CODEC = "libx264"
DEFAULT_AUDIO_CODEC = "aac"
DEFAULT_VIDEO_BITRATE = "8M"
DEFAULT_AUDIO_BITRATE = "192k"

# Video file extensions
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv", ".mxf", ".r3d"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"}


def is_video_file(path: str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def is_audio_file(path: str) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTENSIONS


# Valid transition styles
TRANSITION_STYLES = {
    "hard_cut", "whip_pan", "circle_reveal", "swipe",
    "zoom_blur", "glitch", "mixed", "fade",
}


def process_job(
    video_files: List[str],
    music_file: Optional[str],
    user_prompt: str,
    output_path: str,
    job_id: str,
    progress_callback: Optional[callable] = None,
    style_preset: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    transition_style: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main processing pipeline. Takes raw footage and returns a finished video.

    Args:
        video_files: List of paths to input video files.
        music_file: Optional path to music/audio file.
        user_prompt: User's edit description.
        output_path: Where to save the final MP4.
        job_id: Unique job identifier for logging.
        progress_callback: Optional callback(stage: str, pct: int) for progress updates.
        style_preset: Optional style preset to apply to the final video before audio mix.
                      Options: "cole_bennett", "cinematic", "vintage", "clean", "neon".
        transition_style: Transition between clips. Options: "hard_cut" (default),
                          "whip_pan", "circle_reveal", "swipe", "zoom_blur",
                          "glitch", "mixed", "fade".

    Returns:
        Dict with:
            - output_path (str): Path to finished video
            - duration (float): Output video duration
            - clips_used (int): Number of clips in edit
            - edit_notes (str): Claude's creative notes
    """

    def progress(stage: str, pct: int):
        logger.info(f"[{job_id}] [{pct}%] {stage}")
        if progress_callback:
            progress_callback(stage, pct)

    # Resolve output resolution from aspect ratio
    res = get_resolution(aspect_ratio)
    output_width, output_height = res
    logger.info(f"[{job_id}] Output format: {aspect_ratio or '9:16'} → {output_width}x{output_height}")

    if not video_files:
        raise ValueError("No video files provided")

    # Validate all files exist
    for f in video_files:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Video file not found: {f}")
    if music_file and not os.path.exists(music_file):
        raise FileNotFoundError(f"Music file not found: {music_file}")

    progress("Detecting scenes in footage", 10)

    # --- STEP 1: Detect scenes in all video files ---
    all_scenes = []
    time_offset = 0.0
    file_scene_map = {}  # Map scene_num -> (file_index, original_scene)

    for file_idx, vf in enumerate(video_files):
        logger.info(f"[{job_id}] Scanning scenes in: {os.path.basename(vf)}")
        try:
            scenes = detect_scenes(vf)
            # If no scenes detected, treat entire clip as one scene
            if not scenes:
                logger.info(f"[{job_id}] No scenes detected in {os.path.basename(vf)}, treating as single scene")
                scenes = _get_video_as_single_scene(vf)
        except Exception as e:
            logger.warning(f"Scene detection failed for {vf}: {e}, treating as single scene")
            scenes = _get_video_as_single_scene(vf)

        for scene in scenes:
            global_scene_num = len(all_scenes) + 1
            global_scene = {
                **scene,
                "scene_num": global_scene_num,
                "source_file_index": file_idx,
                "source_file": vf,
                # Preserve original in-file timestamps
                "source_start_time": scene["start_time"],
                "source_end_time": scene["end_time"],
            }
            all_scenes.append(global_scene)
            file_scene_map[global_scene_num] = global_scene

    logger.info(f"[{job_id}] Total scenes detected: {len(all_scenes)}")
    progress(f"Found {len(all_scenes)} scenes across {len(video_files)} clip(s)", 25)

    # --- STEP 2: Beat detection ---
    beat_data = None
    if music_file:
        progress("Analyzing music beats", 35)
        logger.info(f"[{job_id}] Analyzing music: {os.path.basename(music_file)}")
        try:
            is_video = is_video_file(music_file)
            beat_data = detect_beats(music_file, is_video=is_video)
            logger.info(f"[{job_id}] BPM: {beat_data['bpm']}, {len(beat_data['beats'])} beats")
        except Exception as e:
            logger.warning(f"Beat detection failed: {e}")
    else:
        logger.info(f"[{job_id}] No music file — skipping beat detection")

    progress("Asking AI for edit decisions", 45)

    # --- STEP 3: AI editing decisions ---
    target_duration = beat_data["total_duration"] if beat_data else None

    try:
        decisions = get_edit_decisions(
            scenes=all_scenes,
            beat_data=beat_data,
            user_prompt=user_prompt,
            target_duration=target_duration,
            video_files=video_files,
        )
    except Exception as e:
        logger.error(f"[{job_id}] AI editor failed: {e}")
        raise

    clips_plan = decisions.get("clips", [])
    edit_notes = decisions.get("edit_notes", "")
    logger.info(f"[{job_id}] Edit plan: {len(clips_plan)} clips — {edit_notes}")
    progress(f"AI planned {len(clips_plan)} clips", 55)

    if not clips_plan:
        raise RuntimeError("AI returned empty clip list")

    # --- STEP 4: Extract and assemble clips ---
    progress("Cutting and assembling clips", 60)

    with tempfile.TemporaryDirectory(prefix=f"tubee_{job_id}_") as tmp_dir:
        segment_files = _extract_segments(clips_plan, file_scene_map, tmp_dir, job_id, output_width, output_height)

        if not segment_files:
            raise RuntimeError("No segments were extracted")

        progress("Concatenating clips", 75)

        # --- STEP 4b (optional): Apply transitions between segments ---
        effective_transition = transition_style or "hard_cut"
        # Normalise "swipe" → "swipe_left"
        if effective_transition == "swipe":
            effective_transition = "swipe_left"

        concat_video = os.path.join(tmp_dir, "concat.mp4")
        trans_applied = False

        if effective_transition != "hard_cut" and len(segment_files) >= 2:
            progress(f"Applying '{effective_transition}' transitions", 72)
            trans_result = apply_transitions_to_sequence(
                segment_files,
                concat_video,
                transition_type=effective_transition,
                transition_duration=0.3,
            )
            if trans_result:
                trans_applied = True
                logger.info(f"[{job_id}] Transitions applied: {effective_transition}")
            else:
                logger.warning(f"[{job_id}] Transitions returned None, falling back to hard cut concat")

        if not trans_applied:
            # Build intermediate video with plain concat (no transitions)
            _concat_segments(segment_files, concat_video)

        # --- STEP 5 (optional): Apply style preset ---
        styled_video = concat_video
        if style_preset:
            valid_presets = {"cole_bennett", "cinematic", "vintage", "vintage_2026", "clean", "neon"}
            if style_preset in valid_presets:
                progress(f"Applying '{style_preset}' style preset", 82)
                styled_path = os.path.join(tmp_dir, "styled.mp4")
                # Pass beat timestamps if available for beat-synced effects
                beat_ts = beat_data.get("beats", []) if beat_data else []
                styled_result = apply_style_preset(
                    concat_video, styled_path,
                    preset=style_preset,
                    beat_timestamps=beat_ts,
                )
                if styled_result:
                    styled_video = styled_result
                    logger.info(f"[{job_id}] Style preset '{style_preset}' applied")
                else:
                    logger.warning(f"[{job_id}] Style preset '{style_preset}' failed, using ungraded video")
            else:
                logger.warning(f"[{job_id}] Unknown style preset '{style_preset}', skipping. Valid: {valid_presets}")

        progress("Mixing audio and exporting", 90)

        # --- STEP 6: Mix audio and export ---
        _export_final(
            video_path=styled_video,
            music_file=music_file,
            output_path=output_path,
        )

    # Get output duration
    output_duration = _get_video_duration(output_path)
    progress("Done!", 100)

    logger.info(
        f"[{job_id}] Export complete: {output_path} "
        f"({output_duration:.1f}s, {len(clips_plan)} clips)"
    )

    return {
        "output_path": output_path,
        "duration": output_duration,
        "clips_used": len(clips_plan),
        "edit_notes": edit_notes,
    }


def _get_video_as_single_scene(video_path: str) -> List[Dict[str, Any]]:
    """Return entire video as a single scene (fallback)."""
    duration = _get_video_duration(video_path)
    return [{
        "scene_num": 1,
        "start_time": 0.0,
        "end_time": duration,
        "duration": duration,
        "start_frame": 0,
        "end_frame": int(duration * DEFAULT_FPS),
    }]


def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using FFprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0
    data = json.loads(result.stdout)
    return float(data.get("format", {}).get("duration", 0.0))


def _extract_segments(
    clips_plan: List[Dict[str, Any]],
    scene_map: Dict[int, Dict[str, Any]],
    tmp_dir: str,
    job_id: str,
    output_width: int = 1080,
    output_height: int = 1920,
) -> List[str]:
    """
    Extract each planned clip from its source video using FFmpeg.

    Args:
        clips_plan: List of clip dicts from AI editor.
        scene_map: Maps scene_num to scene metadata (including source file).
        tmp_dir: Directory to write segment files.
        job_id: For logging.

    Returns:
        List of paths to extracted segment MP4 files, in order.
    """
    segment_files = []

    for clip in clips_plan:
        clip_idx = clip["clip_index"]
        scene_num = clip["source_scene_num"]
        clip_start = clip["clip_start"]
        clip_end = clip["clip_end"]
        transition = clip.get("transition", "cut")

        scene = scene_map.get(scene_num)
        if not scene:
            logger.warning(f"Scene {scene_num} not found in scene map, skipping clip {clip_idx}")
            continue

        source_file = scene["source_file"]
        segment_path = os.path.join(tmp_dir, f"seg_{clip_idx:04d}.mp4")

        duration = clip_end - clip_start
        if duration <= 0:
            logger.warning(f"Clip {clip_idx} has zero/negative duration, skipping")
            continue

        logger.debug(
            f"[{job_id}] Extracting clip {clip_idx}: "
            f"{os.path.basename(source_file)} [{clip_start:.2f}s – {clip_end:.2f}s]"
        )

        # Use FFmpeg to cut the segment
        # -ss before -i for fast seek, -t for duration
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(clip_start),
            "-i", source_file,
            "-t", str(duration),
            # Re-encode to ensure consistent format for concat
            "-c:v", DEFAULT_VIDEO_CODEC,
            "-crf", "16",
            "-preset", "slow",
            "-vf", f"scale={output_width}:{output_height}:force_original_aspect_ratio=increase,"
                   f"crop={output_width}:{output_height},unsharp=5:5:1.0:5:5:0.0",
            "-r", str(DEFAULT_FPS),
            "-pix_fmt", "yuv420p",
            "-c:a", DEFAULT_AUDIO_CODEC,
            "-b:a", DEFAULT_AUDIO_BITRATE,
            "-ar", "44100",
            segment_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"FFmpeg segment extraction failed for clip {clip_idx}: {result.stderr[-500:]}")
            continue

        if os.path.exists(segment_path) and os.path.getsize(segment_path) > 0:
            segment_files.append(segment_path)
        else:
            logger.warning(f"Segment file not created for clip {clip_idx}")

    logger.info(f"[{job_id}] Extracted {len(segment_files)}/{len(clips_plan)} segments")
    return segment_files


def _concat_segments(segment_files: List[str], output_path: str) -> None:
    """
    Concatenate video segments using FFmpeg concat demuxer.

    Args:
        segment_files: Ordered list of segment file paths.
        output_path: Output MP4 path.
    """
    # Write concat list file
    list_path = output_path + ".txt"
    with open(list_path, "w") as f:
        for seg in segment_files:
            # Escape single quotes in paths
            safe_path = seg.replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if os.path.exists(list_path):
        os.unlink(list_path)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed: {result.stderr[-500:]}")

    logger.info(f"Concatenated {len(segment_files)} segments → {output_path}")


def _export_final(
    video_path: str,
    music_file: Optional[str],
    output_path: str,
) -> None:
    """
    Mix audio with video and export final 1080p MP4.
    If music is provided, mixes it with original audio (music at 80%, original at 30%).
    If no music, exports with original audio only.

    Args:
        video_path: Path to concatenated video (with original audio).
        music_file: Optional path to music file.
        output_path: Final output path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if music_file:
        # Mix music with original audio using amix filter
        # Music at 80% volume, original audio at 30%
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_file,
            "-filter_complex",
            "[0:a]volume=0.3[orig];"
            "[1:a]volume=0.8[music];"
            "[orig][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", DEFAULT_AUDIO_CODEC,
            "-b:a", DEFAULT_AUDIO_BITRATE,
            "-shortest",  # End at shorter of video/audio
            output_path,
        ]
    else:
        # No music — just copy video as-is
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-c:v", "copy",
            "-c:a", DEFAULT_AUDIO_CODEC,
            "-b:a", DEFAULT_AUDIO_BITRATE,
            output_path,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"Final export failed: {result.stderr[-500:]}")

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Final export: {output_path} ({file_size_mb:.1f} MB)")


def export_fcpxml(
    result: Dict[str, Any],
    clips_plan: List[Dict[str, Any]],
    scene_map: Dict[int, Dict[str, Any]],
    output_path: str,
    project_name: str,
    fps: float = 30,
    resolution: tuple = (1080, 1920),
) -> Optional[str]:
    """
    Generate an FCPXML timeline file from a Tubee edit result.
    Called automatically by process_job() to produce an editable DaVinci timeline
    alongside the flat MP4 export.

    Args:
        result:       The dict returned by process_job()
        clips_plan:   The clips_plan list from get_edit_decisions()
        scene_map:    Maps scene_num → scene metadata (including source_file)
        output_path:  Path for the .fcpxml file (usually same as MP4 but .fcpxml)
        project_name: Name of the project/timeline in DaVinci
        fps:          Frame rate (default 30)
        resolution:   (width, height) tuple — default is 1080x1920 (Reels/vertical)

    Returns:
        Path to the written .fcpxml file, or None on failure.

    Usage:
        result = process_job(video_files, music_file, prompt, output_mp4, job_id)
        fcpxml_path = output_mp4.replace(".mp4", ".fcpxml")
        export_fcpxml(result, clips_plan, scene_map, fcpxml_path, "My Project")
    """
    import xml.etree.ElementTree as ET
    import hashlib
    from fractions import Fraction
    from pathlib import Path as _Path
    from math import gcd

    def _fps_to_frame_duration(fps: float):
        """Return (numerator, denominator) for a single frame's duration."""
        FRAME_RATES = {
            23.976: Fraction(1001, 24000),
            24:     Fraction(1, 24),
            25:     Fraction(1, 25),
            29.97:  Fraction(1001, 30000),
            30:     Fraction(1, 30),
            50:     Fraction(1, 50),
            59.94:  Fraction(1001, 60000),
            60:     Fraction(1, 60),
        }
        closest = min(FRAME_RATES.keys(), key=lambda r: abs(r - fps))
        frac = FRAME_RATES[closest]
        return (frac.numerator, frac.denominator)

    def _secs_to_tc(seconds: float, fps: float) -> str:
        """Convert seconds to FCPXML rational time string (e.g. '165/30s')."""
        fn, fd = _fps_to_frame_duration(fps)
        # frames per second = fd/fn
        rate_frac = Fraction(fd, fn)
        frame_count = int(Fraction(seconds).limit_denominator(1_000_000) * rate_frac)
        t_num = frame_count * fn
        t_den = fd
        g = gcd(t_num, t_den)
        t_num //= g
        t_den //= g
        return f"{t_num}s" if t_den == 1 else f"{t_num}/{t_den}s"

    def _uid(path: str) -> str:
        h = hashlib.md5(path.encode()).hexdigest().upper()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    logger.info(f"Generating FCPXML: {output_path}")

    # Enrich clips_plan with source_file from scene_map (if not already present)
    enriched_clips = []
    for clip in clips_plan:
        c = dict(clip)
        if not c.get("source_file"):
            scene_num = c.get("source_scene_num")
            scene = scene_map.get(scene_num) if scene_num else None
            if scene:
                c["source_file"] = scene.get("source_file", "")
        # Validate source file exists
        src = c.get("source_file", "")
        if src and os.path.exists(src):
            enriched_clips.append(c)
        else:
            logger.warning(f"FCPXML: source file missing for clip {c.get('clip_index')}: {src}")

    if not enriched_clips:
        logger.error("FCPXML: No valid clips with existing source files — skipping export")
        return None

    width, height = resolution
    frame_num, frame_den = _fps_to_frame_duration(fps)

    # --- Build FCPXML tree ---
    root = ET.Element("fcpxml", version="1.10")
    resources = ET.SubElement(root, "resources")

    format_id = "r1"
    ET.SubElement(resources, "format", {
        "id": format_id,
        "name": f"FFVideoFormat{height}p{int(fps)}",
        "frameDuration": f"{frame_num}/{frame_den}s",
        "width": str(width),
        "height": str(height),
        "colorSpace": "1-1-1 (Rec. 709)",
    })

    # Collect unique source files → assign asset IDs
    source_assets: Dict[str, str] = {}
    asset_counter = 2

    for clip in enriched_clips:
        src = str(_Path(clip["source_file"]).resolve())
        if src not in source_assets:
            res_id = f"r{asset_counter}"
            source_assets[src] = res_id
            asset_counter += 1

            # Use clip_end as a conservative file duration estimate
            file_dur = float(clip.get("clip_end", 60.0))

            asset = ET.SubElement(resources, "asset", {
                "id": res_id,
                "name": _Path(src).stem,
                "uid": _uid(src),
                "start": "0s",
                "duration": _secs_to_tc(file_dur, fps),
                "hasVideo": "1",
                "hasAudio": "1",
                "videoSources": "1",
                "audioSources": "1",
                "audioChannels": "2",
            })
            ET.SubElement(asset, "media-rep", {
                "kind": "original-media",
                "src": _Path(src).as_uri(),
            })

    # Total timeline duration
    total_dur = sum(
        float(c.get("clip_end", 0)) - float(c.get("clip_start", 0))
        for c in enriched_clips
    )

    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", {"name": project_name})
    project_el = ET.SubElement(event, "project", {"name": project_name})
    sequence = ET.SubElement(project_el, "sequence", {
        "format": format_id,
        "duration": _secs_to_tc(total_dur, fps),
        "tcStart": "0s",
        "tcFormat": "NDF",
    })
    spine = ET.SubElement(sequence, "spine")

    for clip in enriched_clips:
        src = str(_Path(clip["source_file"]).resolve())
        clip_start = float(clip.get("clip_start", 0.0))
        clip_end = float(clip.get("clip_end", 0.0))
        clip_dur = clip_end - clip_start

        if clip_dur <= 0:
            continue

        asset_id = source_assets.get(src)
        if not asset_id:
            continue

        clip_el = ET.SubElement(spine, "asset-clip", {
            "ref": asset_id,
            "name": f"Clip {clip.get('clip_index', '?')} — {_Path(src).stem}",
            "duration": _secs_to_tc(clip_dur, fps),
            "start": _secs_to_tc(clip_start, fps),
            "format": format_id,
            "tcFormat": "NDF",
        })

    # Write file
    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="  ")  # Python 3.9+
        except AttributeError:
            pass  # Older Python — skip pretty-printing

        with open(output_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE fcpxml>\n')
            f.write(ET.tostring(root, encoding="unicode", xml_declaration=False))
            f.write("\n")

        logger.info(
            f"FCPXML exported: {output_path} "
            f"({len(enriched_clips)} clips, {total_dur:.1f}s)"
        )
        return output_path

    except Exception as e:
        logger.error(f"Failed to write FCPXML {output_path}: {e}")
        return None


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if len(sys.argv) < 3:
        print("Usage: python processor.py <output.mp4> <video1> [video2 ...] [--music <music_file>] [--prompt 'your prompt'] [--style <preset>] [--transition <type>]")
        print()
        print("Example:")
        print("  python processor.py output.mp4 clip1.mp4 clip2.mp4 --music song.mp3 --prompt 'Fast-paced highlight reel' --style cole_bennett --transition whip_pan")
        print()
        print("Style presets: cole_bennett, cinematic, vintage, clean, neon")
        print("Transitions:   hard_cut, whip_pan, circle_reveal, swipe, zoom_blur, glitch, mixed, fade")
        sys.exit(1)

    output = sys.argv[1]
    videos = []
    music = None
    prompt = "Create an engaging highlight video"
    style = None
    transition = None
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--music" and i + 1 < len(sys.argv):
            music = sys.argv[i + 1]
            i += 2
        elif arg == "--prompt" and i + 1 < len(sys.argv):
            prompt = sys.argv[i + 1]
            i += 2
        elif arg == "--style" and i + 1 < len(sys.argv):
            style = sys.argv[i + 1]
            i += 2
        elif arg == "--transition" and i + 1 < len(sys.argv):
            transition = sys.argv[i + 1]
            i += 2
        else:
            videos.append(arg)
            i += 1

    job_id = str(uuid.uuid4())[:8]
    result = process_job(videos, music, prompt, output, job_id, style_preset=style, transition_style=transition)
    print(json.dumps(result, indent=2))
