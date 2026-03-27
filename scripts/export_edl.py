#!/usr/bin/env python3
"""
export_edl.py — Tubee → CMX3600 EDL (Edit Decision List)
=========================================================
Exports a Tubee clips plan as a CMX3600-format EDL file.

EDL (Edit Decision List) is a simple, widely-supported interchange format
that most professional NLEs understand, including:
  - DaVinci Resolve (File → Import → Timeline → EDL)
  - Adobe Premiere Pro
  - Avid Media Composer
  - Final Cut Pro (via EDL import)

Usage:
    python export_edl.py clips.json output.edl \
        --project "Strip Promo" \
        --fps 30

    python export_edl.py clips.json output.edl \
        --project "Wedding Film" \
        --fps 23.976

CMX3600 Format:
    TITLE: ProjectName
    FCM: NON-DROP FRAME

    001  AX       V     C        00:00:00:00 00:00:05:00 00:00:00:00 00:00:05:00
    * FROM CLIP NAME: source_filename.mp4
    ...

Timecodes are expressed as HH:MM:SS:FF (hours:minutes:seconds:frames).
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


# ---------------------------------------------------------------------------
# Timecode helpers
# ---------------------------------------------------------------------------

def seconds_to_timecode(seconds: float, fps: float, drop_frame: bool = False) -> str:
    """
    Convert seconds to a SMPTE timecode string: HH:MM:SS:FF.

    Args:
        seconds:     Time in seconds
        fps:         Frame rate (e.g. 30.0, 29.97, 24.0)
        drop_frame:  Use drop-frame notation (; instead of :) for 29.97/59.94

    Returns:
        Timecode string like "01:23:45:12" or "01:23:45;12" for drop-frame
    """
    # For 29.97, use the standard drop-frame calculation
    nominal_fps = round(fps)  # 29.97 → 30, 23.976 → 24
    total_frames = int(round(seconds * fps))

    if drop_frame and fps in (29.97, 59.94):
        # CMX3600 drop-frame calculation
        # Drop 2 frames every minute except every 10th minute
        d = 2 if fps < 30 else 4
        frames_per_10_min = round(fps * 60 * 10)
        drop_per_min = d
        frames_per_min = round(fps * 60) - drop_per_min

        D = total_frames // frames_per_10_min
        M = (total_frames % frames_per_10_min)
        if M < d:
            M = 0
        else:
            M = (M - d) // frames_per_min + 1

        frame_num = total_frames + d * (9 * D + M)

        ff = frame_num % nominal_fps
        ss = (frame_num // nominal_fps) % 60
        mm = (frame_num // (nominal_fps * 60)) % 60
        hh = frame_num // (nominal_fps * 3600)
        sep = ";"
    else:
        # Non-drop frame (simpler math)
        ff = total_frames % nominal_fps
        total_seconds = total_frames // nominal_fps
        ss = total_seconds % 60
        mm = (total_seconds // 60) % 60
        hh = total_seconds // 3600
        sep = ":"

    return f"{hh:02d}:{mm:02d}:{ss:02d}{sep}{ff:02d}"


def timecode_to_seconds(tc: str, fps: float) -> float:
    """
    Convert a SMPTE timecode string to seconds.
    Supports both drop-frame (;) and non-drop (:) separators.
    """
    drop_frame = ";" in tc
    tc_clean = tc.replace(";", ":").replace(",", ":")
    parts = tc_clean.split(":")
    if len(parts) != 4:
        raise ValueError(f"Invalid timecode: {tc}")

    hh, mm, ss, ff = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
    nominal_fps = round(fps)

    total_frames = (hh * 3600 + mm * 60 + ss) * nominal_fps + ff

    if drop_frame and fps in (29.97, 59.94):
        # Adjust for dropped frames
        d = 2 if fps < 30 else 4
        total_mins = 60 * hh + mm
        total_frames -= d * (total_mins - total_mins // 10)

    return total_frames / fps


# ---------------------------------------------------------------------------
# EDL builder
# ---------------------------------------------------------------------------

def build_edl(
    clips_plan: List[Dict[str, Any]],
    project_name: str,
    fps: float = 30.0,
) -> str:
    """
    Build a CMX3600 EDL string from a Tubee clips plan.

    Args:
        clips_plan:   List of clip dicts from Tubee
        project_name: Project name for the EDL title
        fps:          Frame rate

    Returns:
        Complete EDL as a string
    """
    drop_frame = fps in (29.97, 59.94)
    fcm_line = "DROP FRAME" if drop_frame else "NON-DROP FRAME"

    lines = []

    # EDL header
    lines.append(f"TITLE: {project_name}")
    lines.append(f"FCM: {fcm_line}")
    lines.append("")

    # Timeline position accumulator
    record_tc_start = 0.0
    event_num = 1

    for clip in clips_plan:
        src_file = clip.get("source_file", "")
        clip_start = float(clip.get("clip_start", 0.0))
        clip_end = float(clip.get("clip_end", 0.0))
        clip_duration = clip_end - clip_start

        if clip_duration <= 0 or not src_file:
            continue

        # Source timecodes (in-point and out-point in the source file)
        src_in_tc = seconds_to_timecode(clip_start, fps, drop_frame)
        src_out_tc = seconds_to_timecode(clip_end, fps, drop_frame)

        # Record (timeline) timecodes
        rec_in_tc = seconds_to_timecode(record_tc_start, fps, drop_frame)
        rec_out_tc = seconds_to_timecode(record_tc_start + clip_duration, fps, drop_frame)

        # Reel name — EDL reel names are max 8 chars, use a short form
        # Use clip index or a hash of the filename
        reel_name = f"REEL{event_num:03d}"

        # Main EDL line:
        # EventNum  ReelName  Channels  EditType  SrcIn  SrcOut  RecIn  RecOut
        # C = cut, D = dissolve, W = wipe
        edit_type = "C"  # Always cut for now (Tubee handles transitions separately)

        edl_line = (
            f"{event_num:03d}  "
            f"{reel_name:<8}  "
            f"V     "       # Video only (use "AV" for audio+video, "A" for audio)
            f"{edit_type}        "
            f"{src_in_tc} "
            f"{src_out_tc} "
            f"{rec_in_tc} "
            f"{rec_out_tc}"
        )
        lines.append(edl_line)

        # Comment lines with clip metadata (prefixed with *)
        src_filename = Path(src_file).name
        lines.append(f"* FROM CLIP NAME: {src_filename}")
        lines.append(f"* SOURCE FILE: {src_file}")

        if clip.get("clip_index") is not None:
            lines.append(f"* TUBEE CLIP INDEX: {clip['clip_index']}")

        lines.append("")  # Blank line between events

        # Advance timeline position
        record_tc_start += clip_duration
        event_num += 1

    return "\n".join(lines)


def export_edl(
    clips_plan: List[Dict[str, Any]],
    output_path: str,
    project_name: str = "Tubee Edit",
    fps: float = 30.0,
) -> str:
    """
    Generate and write a CMX3600 EDL file from a Tubee clips plan.

    Args:
        clips_plan:   List of clip dicts
        output_path:  Where to write the .edl file
        project_name: Project name
        fps:          Frame rate

    Returns:
        Absolute path to the written file
    """
    output_path = str(Path(output_path).resolve())
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Filter valid clips
    valid_clips = []
    for clip in clips_plan:
        src = clip.get("source_file", "")
        if not src:
            print(f"  WARNING: Clip {clip.get('clip_index', '?')} has no source_file, skipping")
            continue
        # Don't require file existence for EDL — just pass-through
        valid_clips.append(clip)

    if not valid_clips:
        raise ValueError("No valid clips in plan")

    edl_content = build_edl(valid_clips, project_name, fps)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(edl_content)

    total_duration = sum(
        float(c.get("clip_end", 0)) - float(c.get("clip_start", 0))
        for c in valid_clips
    )

    print(f"✓ EDL exported: {output_path}")
    print(f"  Project: {project_name}")
    print(f"  Events: {len(valid_clips)}")
    print(f"  Frame rate: {fps}fps ({'drop-frame' if fps in (29.97, 59.94) else 'non-drop'})")
    print(f"  Total duration: {total_duration:.2f}s")
    print(f"  Import in DaVinci Resolve: File → Import → Timeline → EDL...")
    print(f"  Import in Premiere Pro: File → Import (select .edl)...")

    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Export a Tubee clips plan to CMX3600 EDL for DaVinci Resolve / Premiere",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("clips_json", help="Path to Tubee clips plan JSON file")
    parser.add_argument("output_edl", help="Output .edl file path")
    parser.add_argument(
        "--project",
        default="Tubee Edit",
        help="Project name (default: 'Tubee Edit')",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=30.0,
        help="Frame rate (default: 30). Supports: 23.976, 24, 25, 29.97, 30, 50, 59.94, 60",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.clips_json):
        print(f"ERROR: Clips JSON not found: {args.clips_json}")
        sys.exit(1)

    with open(args.clips_json) as f:
        clips_plan = json.load(f)

    if isinstance(clips_plan, dict):
        clips_plan = clips_plan.get("clips", clips_plan)

    try:
        export_edl(
            clips_plan=clips_plan,
            output_path=args.output_edl,
            project_name=args.project,
            fps=args.fps,
        )
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
