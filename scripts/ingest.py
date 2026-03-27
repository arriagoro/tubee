#!/usr/bin/env python3
"""
ingest.py — SD Card / Drive Auto-Ingest for Tubee
==================================================
Automatically ingests video files from a mounted SD card or hard drive.

Usage:
    python ingest.py [--drive /Volumes/MyDrive] [--auto-edit "Edit a fast highlight reel"]

Options:
    --drive       Path to the drive to ingest (default: auto-detect new volumes)
    --auto-edit   Prompt to pass to Tubee after ingest (optional)
    --dest        Destination footage root (default: ~/footage)
    --dry-run     Show what would be copied without actually copying

If no --drive is given, the script watches /Volumes/ for newly mounted volumes
and ingests the first one that contains video files.
"""

import os
import sys
import json
import time
import shutil
import hashlib
import argparse
import logging
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

# watchdog for filesystem monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: watchdog not installed. Run: pip install watchdog")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mxf", ".r3d", ".avi", ".mkv", ".m4v", ".braw"}
VOLUMES_PATH = "/Volumes"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("ingest")


# ---------------------------------------------------------------------------
# FFprobe helpers
# ---------------------------------------------------------------------------

def get_video_duration(file_path: str) -> Optional[float]:
    """Return video duration in seconds using ffprobe, or None on failure."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0.0))
    except Exception as e:
        logger.warning(f"Could not get duration for {file_path}: {e}")
    return None


def get_file_creation_date(file_path: str) -> str:
    """
    Return the file's best available creation date as YYYY-MM-DD.
    Uses birthtime (macOS) if available, otherwise mtime.
    Also tries to read embedded creation date from ffprobe metadata.
    """
    # Try ffprobe metadata first (most accurate for camera files)
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_entries", "format_tags=creation_time",
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            creation_time = data.get("format", {}).get("tags", {}).get("creation_time", "")
            if creation_time:
                # Format: "2024-03-15T10:30:00.000000Z"
                dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Fall back to filesystem dates
    stat = os.stat(file_path)
    # birthtime is macOS-specific (st_birthtime)
    if hasattr(stat, "st_birthtime"):
        ts = stat.st_birthtime
    else:
        # Use mtime as fallback (closest to creation on Linux)
        ts = stat.st_mtime

    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Core ingest logic
# ---------------------------------------------------------------------------

def find_video_files(drive_path: str) -> List[str]:
    """
    Recursively find all video files on a drive.
    Skips hidden directories (like .Spotlight-V100, .Trashes).
    """
    video_files = []
    drive_path = Path(drive_path)

    for root, dirs, files in os.walk(drive_path):
        # Skip hidden/system directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for fname in files:
            if Path(fname).suffix.lower() in VIDEO_EXTENSIONS:
                video_files.append(os.path.join(root, fname))

    return sorted(video_files)


def copy_with_progress(src: str, dst: str) -> None:
    """
    Copy a file with live progress display (prints to stdout).
    Uses shutil.copyfileobj with a chunked approach.
    """
    file_size = os.path.getsize(src)
    copied = 0
    chunk_size = 1024 * 1024  # 1 MB chunks

    fname = os.path.basename(src)
    size_mb = file_size / (1024 * 1024)

    print(f"  → {fname} ({size_mb:.1f} MB)", end="", flush=True)

    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        while True:
            chunk = fsrc.read(chunk_size)
            if not chunk:
                break
            fdst.write(chunk)
            copied += len(chunk)
            pct = int(copied / file_size * 100) if file_size > 0 else 100
            print(f"\r  → {fname} ({size_mb:.1f} MB) [{pct}%]", end="", flush=True)

    # Copy metadata (timestamps, permissions)
    shutil.copystat(src, dst)
    print(f"\r  ✓ {fname} ({size_mb:.1f} MB) [done]")


def compute_md5(file_path: str, sample_bytes: int = 1024 * 1024) -> str:
    """
    Compute a quick MD5 of the first 1MB of a file.
    Used to detect duplicates without hashing the full file.
    """
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        h.update(f.read(sample_bytes))
    return h.hexdigest()


def send_macos_notification(title: str, message: str) -> None:
    """Send a macOS notification using osascript."""
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], check=False, timeout=5)
    except Exception as e:
        logger.warning(f"Could not send notification: {e}")


def play_completion_sound() -> None:
    """Play the macOS Glass notification sound."""
    try:
        subprocess.run(
            ["afplay", "/System/Library/Sounds/Glass.aiff"],
            check=False, timeout=5
        )
    except Exception as e:
        logger.warning(f"Could not play sound: {e}")


def ingest_drive(
    drive_path: str,
    dest_root: str,
    dry_run: bool = False,
    auto_edit_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingest all video files from a drive into ~/footage/YYYY-MM-DD/ folders.

    Args:
        drive_path:       Path to the mounted drive (e.g. /Volumes/SDCARD)
        dest_root:        Root destination folder (e.g. ~/footage)
        dry_run:          If True, don't actually copy files
        auto_edit_prompt: If set, trigger Tubee after ingest with this prompt

    Returns:
        Dict summary with imported files, manifest paths, etc.
    """
    drive_path = str(Path(drive_path).resolve())
    dest_root = str(Path(dest_root).expanduser().resolve())

    drive_name = os.path.basename(drive_path)
    logger.info(f"Starting ingest from: {drive_path}")

    # Find all video files
    print(f"\n🔍 Scanning {drive_path} for video files...")
    video_files = find_video_files(drive_path)

    if not video_files:
        logger.info("No video files found on this drive.")
        return {"drive": drive_path, "files_imported": 0, "manifests": []}

    print(f"   Found {len(video_files)} video file(s)\n")

    # Group files by their creation date
    date_groups: Dict[str, List[str]] = {}
    for vf in video_files:
        date_str = get_file_creation_date(vf)
        date_groups.setdefault(date_str, []).append(vf)

    total_imported = 0
    manifests = []

    for date_str, files in sorted(date_groups.items()):
        dest_dir = os.path.join(dest_root, date_str)

        print(f"📁 {date_str}/ — {len(files)} file(s)")

        if not dry_run:
            os.makedirs(dest_dir, exist_ok=True)

        manifest_entries = []

        for src_path in files:
            dst_path = os.path.join(dest_dir, os.path.basename(src_path))

            # Handle filename collisions by appending a counter
            if os.path.exists(dst_path) and not dry_run:
                base, ext = os.path.splitext(os.path.basename(src_path))
                # Check if it's a genuine duplicate (same first-MB hash)
                if compute_md5(src_path) == compute_md5(dst_path):
                    print(f"  ⏭  {os.path.basename(src_path)} [already imported, skipping]")
                    continue
                # Different file, same name — add counter
                counter = 1
                while os.path.exists(dst_path):
                    dst_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                    counter += 1

            if dry_run:
                print(f"  [DRY RUN] Would copy: {os.path.basename(src_path)}")
                duration = get_video_duration(src_path)
            else:
                try:
                    copy_with_progress(src_path, dst_path)
                    duration = get_video_duration(dst_path)
                except Exception as e:
                    logger.error(f"Failed to copy {src_path}: {e}")
                    continue

            # Build manifest entry
            stat = os.stat(src_path)
            manifest_entries.append({
                "filename": os.path.basename(dst_path),
                "source_path": src_path,
                "dest_path": dst_path if not dry_run else "(dry run)",
                "source_drive": drive_name,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "duration_seconds": round(duration, 2) if duration else None,
                "creation_date": date_str,
                "imported_at": datetime.now().isoformat(),
            })
            total_imported += 1

        # Write manifest for this date folder
        if manifest_entries and not dry_run:
            manifest_path = os.path.join(dest_dir, "manifest.json")

            # Merge with existing manifest if present
            existing = []
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path) as f:
                        existing = json.load(f)
                except Exception:
                    existing = []

            # Avoid duplicate entries
            existing_sources = {e["source_path"] for e in existing}
            new_entries = [e for e in manifest_entries if e["source_path"] not in existing_sources]
            all_entries = existing + new_entries

            with open(manifest_path, "w") as f:
                json.dump(all_entries, f, indent=2)

            logger.info(f"Manifest written: {manifest_path}")
            manifests.append(manifest_path)

        print()  # blank line between date groups

    # -----------------------------------------------------------------------
    # Done! Notify and optionally auto-trigger Tubee
    # -----------------------------------------------------------------------
    print(f"✅ Ingest complete — {total_imported} file(s) imported from {drive_name}\n")

    if not dry_run:
        play_completion_sound()
        send_macos_notification(
            title="Tubee — Ingest Complete",
            message=f"{total_imported} file(s) imported from {drive_name}",
        )

    result = {
        "drive": drive_path,
        "drive_name": drive_name,
        "files_imported": total_imported,
        "manifests": manifests,
        "dest_root": dest_root,
    }

    # Auto-trigger Tubee if requested
    if auto_edit_prompt and total_imported > 0 and not dry_run:
        _trigger_tubee(manifests, auto_edit_prompt, dest_root)

    return result


def _trigger_tubee(manifests: List[str], prompt: str, footage_root: str) -> None:
    """
    Auto-trigger Tubee processing after ingest.
    Collects all imported file paths from manifests and calls the Tubee API.
    """
    video_files = []
    for manifest_path in manifests:
        try:
            with open(manifest_path) as f:
                entries = json.load(f)
            for entry in entries:
                dest = entry.get("dest_path", "")
                if dest and os.path.exists(dest):
                    video_files.append(dest)
        except Exception as e:
            logger.warning(f"Could not read manifest {manifest_path}: {e}")

    if not video_files:
        logger.warning("No files to send to Tubee")
        return

    print(f"🤖 Auto-triggering Tubee with {len(video_files)} file(s)...")
    print(f"   Prompt: {prompt}\n")

    # Build the Tubee CLI command
    # Adjust this path to match your actual Tubee entry point
    tubee_script = os.path.join(os.path.dirname(__file__), "..", "backend", "processor.py")
    output_path = os.path.join(footage_root, f"edit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

    cmd = [
        sys.executable, tubee_script,
        output_path,
        *video_files,
        "--prompt", prompt,
    ]

    logger.info(f"Running: {' '.join(cmd)}")

    try:
        subprocess.Popen(cmd)  # Non-blocking — let it run in background
        print(f"   ✓ Tubee job started — output: {output_path}")
    except Exception as e:
        logger.error(f"Failed to start Tubee: {e}")


# ---------------------------------------------------------------------------
# Volume watcher (for --watch mode)
# ---------------------------------------------------------------------------

class VolumeEventHandler(FileSystemEventHandler):
    """Watchdog event handler that detects newly mounted volumes."""

    def __init__(self, callback, already_known: Set[str]):
        super().__init__()
        self._callback = callback
        self._known_volumes = already_known
        self._lock = threading.Lock()

    def on_created(self, event):
        if not event.is_directory:
            return
        volume_path = event.src_path
        with self._lock:
            if volume_path in self._known_volumes:
                return
            self._known_volumes.add(volume_path)
        # Give the OS a moment to fully mount the volume
        time.sleep(2)
        logger.info(f"New volume detected: {volume_path}")
        self._callback(volume_path)


def watch_for_volumes(
    dest_root: str,
    auto_edit_prompt: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    """
    Watch /Volumes/ for new mounts and auto-ingest when video files are found.
    Blocks until Ctrl+C.
    """
    known = set(os.listdir(VOLUMES_PATH))
    known_paths = {os.path.join(VOLUMES_PATH, v) for v in known}

    def on_new_volume(volume_path: str):
        if not os.path.isdir(volume_path):
            return
        # Check if it has video files before ingesting
        videos = find_video_files(volume_path)
        if videos:
            print(f"\n📀 Volume with {len(videos)} video file(s) detected: {volume_path}")
            ingest_drive(volume_path, dest_root, dry_run, auto_edit_prompt)
        else:
            logger.info(f"Volume {volume_path} has no video files, ignoring")

    handler = VolumeEventHandler(on_new_volume, known_paths)
    observer = Observer()
    observer.schedule(handler, VOLUMES_PATH, recursive=False)
    observer.start()

    print(f"👀 Watching {VOLUMES_PATH} for new volumes... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher.")
    finally:
        observer.stop()
        observer.join()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Tubee Ingest — Auto-import video files from SD cards and drives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--drive",
        help="Path to the drive to ingest (e.g. /Volumes/SDCARD). "
             "If omitted, watches for new volumes automatically.",
    )
    parser.add_argument(
        "--dest",
        default="~/footage",
        help="Destination footage root directory (default: ~/footage)",
    )
    parser.add_argument(
        "--auto-edit",
        metavar="PROMPT",
        help="After ingest, auto-trigger Tubee with this edit prompt",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch /Volumes/ for new mounts and auto-ingest (blocking)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without actually copying",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    dest_root = str(Path(args.dest).expanduser().resolve())

    if args.watch:
        # Always-on watching mode
        watch_for_volumes(dest_root, args.auto_edit, args.dry_run)

    elif args.drive:
        # Ingest a specific drive
        if not os.path.isdir(args.drive):
            print(f"ERROR: Drive not found: {args.drive}")
            sys.exit(1)
        result = ingest_drive(args.drive, dest_root, args.dry_run, args.auto_edit)
        print(json.dumps(result, indent=2))

    else:
        # No drive specified — watch for one-time new volume
        print("No --drive specified. Watching for a new volume...\n")
        print("Plug in your SD card or drive now. (Ctrl+C to cancel)\n")

        known_paths: Set[str] = set()
        for v in os.listdir(VOLUMES_PATH):
            known_paths.add(os.path.join(VOLUMES_PATH, v))

        found_event = threading.Event()
        found_volume = [None]

        def on_new_volume(volume_path: str):
            videos = find_video_files(volume_path)
            if videos:
                found_volume[0] = volume_path
                found_event.set()

        handler = VolumeEventHandler(on_new_volume, known_paths)
        observer = Observer()
        observer.schedule(handler, VOLUMES_PATH, recursive=False)
        observer.start()

        try:
            found_event.wait()  # Block until a video-bearing volume appears
        except KeyboardInterrupt:
            print("\nCancelled.")
            observer.stop()
            observer.join()
            sys.exit(0)

        observer.stop()
        observer.join()

        if found_volume[0]:
            result = ingest_drive(found_volume[0], dest_root, args.dry_run, args.auto_edit)
            print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
