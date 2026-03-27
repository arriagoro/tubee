#!/usr/bin/env python3
"""
export_timeline.py — Tubee → DaVinci Resolve / Final Cut Pro XML
=================================================================
Exports a Tubee edit result as an FCPXML 1.10 file that can be imported
into DaVinci Resolve (File → Import → Timeline) or Final Cut Pro.

Usage:
    python export_timeline.py clips.json output.fcpxml \
        --project "Strip Promo" \
        --fps 30 \
        --resolution reels

    python export_timeline.py clips.json output.fcpxml \
        --project "Wedding Film" \
        --fps 24 \
        --resolution standard

Input JSON format (clips_plan from Tubee):
    [
      {
        "clip_index": 1,
        "source_scene_num": 3,
        "clip_start": 12.5,
        "clip_end": 15.2,
        "source_file": "/Users/agentarri/footage/2024-03-15/CLIP001.mp4"
      },
      ...
    ]
"""

import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from fractions import Fraction


# ---------------------------------------------------------------------------
# Supported resolutions
# ---------------------------------------------------------------------------

RESOLUTIONS = {
    "reels":    (1080, 1920),   # Instagram Reels / TikTok / Shorts (9:16)
    "standard": (1920, 1080),   # Standard HD (16:9)
    "4k":       (3840, 2160),   # 4K UHD (16:9)
    "4k-v":     (2160, 3840),   # 4K vertical
    "square":   (1080, 1080),   # Square (1:1)
}

# Common frame rates mapped to FCPXML timebase fractions
# FCPXML uses rational time: value/timebase
FRAME_RATES = {
    23.976: Fraction(24000, 1001),
    24:     Fraction(24, 1),
    25:     Fraction(25, 1),
    29.97:  Fraction(30000, 1001),
    30:     Fraction(30, 1),
    50:     Fraction(50, 1),
    59.94:  Fraction(60000, 1001),
    60:     Fraction(60, 1),
}


def fps_to_timebase(fps: float) -> Tuple[int, int]:
    """
    Convert fps to (numerator, denominator) for FCPXML frameDuration.
    FCPXML frameDuration is 1/fps — so 30fps = 1/30 = "1/30s".
    Returns (num, den) for the duration of a single frame.
    """
    # Find closest standard frame rate
    closest = min(FRAME_RATES.keys(), key=lambda r: abs(r - fps))
    rate_frac = FRAME_RATES[closest]

    # frameDuration = 1 frame duration = denominator/numerator of the rate
    # e.g. 30fps → frame duration = 1/30s → in FCPXML: "1001/30000s" for 29.97
    frame_dur = Fraction(1, 1) / rate_frac
    return (frame_dur.numerator, frame_dur.denominator)


def seconds_to_fcpxml_time(seconds: float, fps: float) -> str:
    """
    Convert seconds to FCPXML rational time string.
    FCPXML times are expressed as "N/Ds" where N/D is a fraction of seconds.

    For clean math, we express everything in frame counts:
    time = frame_count * frame_duration

    Example: 5.5s at 30fps = 165 frames → "165/30s"
    For 29.97: 5.5s → 165 frames → "165*1001/30000s" = "165165/30000s"
    """
    num, den = fps_to_timebase(fps)
    # How many frames is this?
    # frame_count = seconds / frame_duration = seconds * fps
    # Use exact rational arithmetic
    rate_frac = Fraction(den, num)  # frames per second (exact)
    frame_frac = Fraction(seconds).limit_denominator(1000000) * rate_frac
    total_frames = int(frame_frac)  # snap to nearest frame

    # Time in FCPXML = total_frames * frame_duration
    # = total_frames * (num/den) seconds
    t_num = total_frames * num
    t_den = den

    # Simplify
    from math import gcd
    g = gcd(t_num, t_den)
    t_num //= g
    t_den //= g

    if t_den == 1:
        return f"{t_num}s"
    return f"{t_num}/{t_den}s"


def build_fcpxml(
    clips_plan: List[Dict[str, Any]],
    project_name: str,
    fps: float = 30.0,
    resolution: Tuple[int, int] = (1080, 1920),
) -> ET.Element:
    """
    Build the full FCPXML 1.10 document tree.

    Args:
        clips_plan:   List of clip dicts from Tubee AI editor
        project_name: Name for the project/timeline
        fps:          Frame rate (e.g. 30.0, 29.97, 24.0)
        resolution:   (width, height) in pixels

    Returns:
        Root <fcpxml> Element
    """
    width, height = resolution
    frame_num, frame_den = fps_to_timebase(fps)

    # -----------------------------------------------------------------------
    # FCPXML root
    # -----------------------------------------------------------------------
    root = ET.Element("fcpxml", version="1.10")

    # -----------------------------------------------------------------------
    # Resources section — declares all media assets and formats
    # -----------------------------------------------------------------------
    resources = ET.SubElement(root, "resources")

    # Format (frame rate + resolution)
    format_id = "r1"
    ET.SubElement(resources, "format", {
        "id": format_id,
        "name": f"FFVideoFormat{height}p{int(fps)}",
        "frameDuration": f"{frame_num}/{frame_den}s",
        "width": str(width),
        "height": str(height),
        "colorSpace": "1-1-1 (Rec. 709)",
    })

    # Collect unique source files and assign resource IDs
    source_files: Dict[str, str] = {}  # abs_path → resource_id
    asset_id_counter = 2  # start at r2 (r1 is the format)

    for clip in clips_plan:
        src = clip.get("source_file", "")
        if not src:
            continue
        src = str(Path(src).resolve())
        if src not in source_files:
            res_id = f"r{asset_id_counter}"
            source_files[src] = res_id
            asset_id_counter += 1

            # Get file duration (use clip_end as fallback)
            file_duration = clip.get("file_duration") or clip.get("clip_end", 60.0)

            # Asset element (the media file itself)
            asset = ET.SubElement(resources, "asset", {
                "id": res_id,
                "name": Path(src).stem,
                "uid": _make_uid(src),
                "start": "0s",
                "duration": seconds_to_fcpxml_time(float(file_duration), fps),
                "hasVideo": "1",
                "hasAudio": "1",
                "videoSources": "1",
                "audioSources": "1",
                "audioChannels": "2",
            })

            # Media reference (file URL)
            media_rep = ET.SubElement(asset, "media-rep", {
                "kind": "original-media",
                "src": Path(src).as_uri(),  # file:///absolute/path/to/file.mp4
            })

    # -----------------------------------------------------------------------
    # Library → Event → Project → Sequence (the timeline)
    # -----------------------------------------------------------------------
    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", {"name": project_name})
    project = ET.SubElement(event, "project", {"name": project_name})

    # Calculate total timeline duration
    total_duration = 0.0
    for clip in clips_plan:
        total_duration += float(clip.get("clip_end", 0)) - float(clip.get("clip_start", 0))

    sequence = ET.SubElement(project, "sequence", {
        "format": format_id,
        "duration": seconds_to_fcpxml_time(total_duration, fps),
        "tcStart": "0s",
        "tcFormat": "NDF",  # Non-drop frame (use "DF" for 29.97 drop-frame)
    })

    spine = ET.SubElement(sequence, "spine")

    # -----------------------------------------------------------------------
    # Add clips to the spine (main timeline track)
    # -----------------------------------------------------------------------
    for clip in clips_plan:
        src = clip.get("source_file", "")
        if not src:
            continue

        src = str(Path(src).resolve())
        clip_start = float(clip.get("clip_start", 0.0))
        clip_end = float(clip.get("clip_end", 0.0))
        clip_duration = clip_end - clip_start

        if clip_duration <= 0:
            continue

        asset_id = source_files.get(src)
        if not asset_id:
            continue

        # <asset-clip> places a clip on the timeline
        # offset = where this clip starts on the timeline (calculated cumulatively)
        # start = where in the source file we start (in-point)
        # duration = how long we use

        asset_clip = ET.SubElement(spine, "asset-clip", {
            "ref": asset_id,
            "name": Path(src).stem,
            "duration": seconds_to_fcpxml_time(clip_duration, fps),
            "start": seconds_to_fcpxml_time(clip_start, fps),
            "format": format_id,
            "tcFormat": "NDF",
        })

        # Optional: add clip name annotation
        if clip.get("clip_index") is not None:
            asset_clip.set("name", f"Clip {clip['clip_index']} — {Path(src).stem}")

    return root


def _make_uid(path: str) -> str:
    """Generate a deterministic UID for an asset from its path."""
    import hashlib
    h = hashlib.md5(path.encode()).hexdigest().upper()
    # Format as UUID-style: 8-4-4-4-12
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def export_fcpxml(
    clips_plan: List[Dict[str, Any]],
    output_path: str,
    project_name: str = "Tubee Edit",
    fps: float = 30.0,
    resolution: Tuple[int, int] = (1080, 1920),
) -> str:
    """
    Generate and write an FCPXML file from a Tubee clips plan.

    Args:
        clips_plan:   List of clip dicts (source_file, clip_start, clip_end, etc.)
        output_path:  Where to write the .fcpxml file
        project_name: Name of the project/timeline
        fps:          Frame rate
        resolution:   (width, height)

    Returns:
        Absolute path to the written file
    """
    output_path = str(Path(output_path).resolve())
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Validate clips
    valid_clips = []
    for clip in clips_plan:
        src = clip.get("source_file", "")
        if not src:
            print(f"  WARNING: Clip {clip.get('clip_index', '?')} has no source_file, skipping")
            continue
        if not os.path.exists(src):
            print(f"  WARNING: Source file not found: {src}, skipping")
            continue
        valid_clips.append(clip)

    if not valid_clips:
        raise ValueError("No valid clips with existing source files")

    # Build XML tree
    root = build_fcpxml(valid_clips, project_name, fps, resolution)

    # Write with XML declaration
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")  # Pretty-print (Python 3.9+)

    # Write with DOCTYPE (required by DaVinci Resolve)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE fcpxml>\n')
        # Write the tree without the default declaration (we wrote it above)
        xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
        f.write(xml_str)
        f.write("\n")

    print(f"✓ FCPXML exported: {output_path}")
    print(f"  Project: {project_name}")
    print(f"  Clips: {len(valid_clips)}")
    print(f"  Resolution: {resolution[0]}x{resolution[1]} @ {fps}fps")
    print(f"  Import in DaVinci Resolve: File → Import → Timeline...")

    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Export a Tubee clips plan to FCPXML for DaVinci Resolve / Final Cut Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("clips_json", help="Path to Tubee clips plan JSON file")
    parser.add_argument("output_fcpxml", help="Output .fcpxml file path")
    parser.add_argument(
        "--project",
        default="Tubee Edit",
        help="Project/timeline name (default: 'Tubee Edit')",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=30.0,
        help="Frame rate (default: 30). Supports: 23.976, 24, 25, 29.97, 30, 50, 59.94, 60",
    )
    parser.add_argument(
        "--resolution",
        choices=list(RESOLUTIONS.keys()) + ["custom"],
        default="reels",
        help="Output resolution preset (default: reels = 1080x1920 vertical)",
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Custom width (use with --resolution custom)",
    )
    parser.add_argument(
        "--height",
        type=int,
        help="Custom height (use with --resolution custom)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Load clips plan
    if not os.path.exists(args.clips_json):
        print(f"ERROR: Clips JSON not found: {args.clips_json}")
        sys.exit(1)

    with open(args.clips_json) as f:
        clips_plan = json.load(f)

    if isinstance(clips_plan, dict):
        # Support both {"clips": [...]} and plain list formats
        clips_plan = clips_plan.get("clips", clips_plan)

    # Resolve resolution
    if args.resolution == "custom":
        if not args.width or not args.height:
            print("ERROR: --width and --height required when --resolution is 'custom'")
            sys.exit(1)
        resolution = (args.width, args.height)
    else:
        resolution = RESOLUTIONS[args.resolution]

    # Export
    try:
        export_fcpxml(
            clips_plan=clips_plan,
            output_path=args.output_fcpxml,
            project_name=args.project,
            fps=args.fps,
            resolution=resolution,
        )
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
