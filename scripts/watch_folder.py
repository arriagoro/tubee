"""
watch_folder.py — Auto-process videos dropped into ~/tubee_input/
Watches for new files in ~/tubee_input/. When a prompt.txt + at least one video
file are present together, automatically kicks off the Tubee pipeline.

Usage:
  python watch_folder.py

Expected folder structure:
  ~/tubee_input/
    prompt.txt          ← Required: contains the edit prompt (plain text)
    clip1.mp4           ← Required: one or more video files
    clip2.mp4
    song.mp3            ← Optional: music file

Output: ~/tubee_output/{timestamp}/output.mp4

The script processes the files, saves output, then MOVES processed files to
~/tubee_input/processed/{timestamp}/ so they don't get re-processed.
"""

import os
import sys
import time
import shutil
import logging
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# Add backend to path so we can import processor directly
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("tubee.watcher")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WATCH_DIR = Path.home() / "tubee_input"
OUTPUT_DIR = Path.home() / "tubee_output"
PROCESSED_DIR = WATCH_DIR / "processed"
POLL_INTERVAL = 3.0  # seconds between folder scans

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv", ".mxf"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"}

# Minimum file age before processing (avoid processing mid-copy files)
MIN_FILE_AGE_SECONDS = 2.0

# ---------------------------------------------------------------------------
# Global flag for graceful shutdown
# ---------------------------------------------------------------------------
_shutdown = False


def handle_shutdown(signum, frame):
    global _shutdown
    logger.info("Shutdown signal received — stopping watcher")
    _shutdown = True


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


# ---------------------------------------------------------------------------
# Folder scanning
# ---------------------------------------------------------------------------

def scan_input_folder(watch_dir: Path) -> dict:
    """
    Scan the input folder for processable content.

    Returns:
        Dict with:
            - ready (bool): True if we have prompt + at least one video
            - prompt (str): The prompt text
            - videos (List[Path]): Video file paths
            - music (Optional[Path]): Music file path
    """
    if not watch_dir.exists():
        return {"ready": False}

    files = list(watch_dir.glob("*"))
    now = time.time()

    prompt_file = None
    video_files = []
    music_file = None

    for f in files:
        if not f.is_file():
            continue

        # Skip hidden files and system files
        if f.name.startswith(".") or f.name == ".DS_Store":
            continue

        # Skip the processed subdirectory
        if f.is_dir():
            continue

        # Check file age (don't process files still being copied)
        try:
            age = now - f.stat().st_mtime
            if age < MIN_FILE_AGE_SECONDS:
                logger.debug(f"Skipping {f.name} — too new ({age:.1f}s old)")
                continue
        except OSError:
            continue

        ext = f.suffix.lower()

        if f.name.lower() == "prompt.txt":
            prompt_file = f
        elif ext in VIDEO_EXTENSIONS:
            video_files.append(f)
        elif ext in AUDIO_EXTENSIONS:
            if music_file is None:
                music_file = f
            else:
                logger.warning(f"Multiple music files found, using first: {music_file.name}")

    if prompt_file is None or not video_files:
        return {"ready": False}

    # Read prompt
    try:
        prompt_text = prompt_file.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.error(f"Failed to read prompt.txt: {e}")
        return {"ready": False}

    if not prompt_text:
        logger.warning("prompt.txt is empty")
        return {"ready": False}

    return {
        "ready": True,
        "prompt": prompt_text,
        "prompt_file": prompt_file,
        "videos": sorted(video_files),
        "music": music_file,
    }


def process_and_archive(content: dict) -> bool:
    """
    Run the Tubee pipeline on discovered content, then archive inputs.

    Returns:
        True if processing succeeded, False if it failed.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_DIR / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "output.mp4")

    logger.info("=" * 60)
    logger.info("📹  NEW EDIT JOB DETECTED")
    logger.info(f"Prompt: {content['prompt']}")
    logger.info(f"Videos: {[v.name for v in content['videos']]}")
    if content.get("music"):
        logger.info(f"Music: {content['music'].name}")
    logger.info(f"Output: {output_path}")
    logger.info("=" * 60)

    # Import and run the processor
    try:
        from processor import process_job
        import uuid

        job_id = f"watch_{timestamp}"

        result = process_job(
            video_files=[str(v) for v in content["videos"]],
            music_file=str(content["music"]) if content.get("music") else None,
            user_prompt=content["prompt"],
            output_path=output_path,
            job_id=job_id,
        )

        logger.info("✅  Edit complete!")
        logger.info(f"    Duration: {result['duration']:.1f}s")
        logger.info(f"    Clips: {result['clips_used']}")
        logger.info(f"    Output: {output_path}")
        logger.info(f"    Notes: {result['edit_notes']}")

        # Save edit report
        report_path = output_dir / "edit_report.json"
        import json
        with open(report_path, "w") as f:
            json.dump({
                "job_id": job_id,
                "timestamp": timestamp,
                "prompt": content["prompt"],
                "videos": [v.name for v in content["videos"]],
                "music": content["music"].name if content.get("music") else None,
                "output": output_path,
                **result,
            }, f, indent=2)

        success = True

    except Exception as e:
        logger.error(f"❌  Processing failed: {e}", exc_info=True)

        # Write error log
        error_file = output_dir / "error.txt"
        error_file.write_text(f"Error: {e}\n\nPrompt: {content['prompt']}\n")

        success = False

    # Archive processed files regardless of success
    archive_dir = PROCESSED_DIR / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    files_to_archive = content["videos"] + [content["prompt_file"]]
    if content.get("music"):
        files_to_archive.append(content["music"])

    for f in files_to_archive:
        try:
            dest = archive_dir / f.name
            shutil.move(str(f), str(dest))
            logger.debug(f"Archived: {f.name} → processed/{timestamp}/")
        except Exception as e:
            logger.warning(f"Failed to archive {f.name}: {e}")

    if success:
        logger.info(f"✅  Files archived to: {archive_dir}")
        logger.info(f"🎬  Open output: {output_path}")
        # Open the output folder in Finder (macOS)
        try:
            subprocess.Popen(["open", str(output_dir)])
        except Exception:
            pass  # Not critical if this fails

    return success


# ---------------------------------------------------------------------------
# Main watch loop
# ---------------------------------------------------------------------------

def main():
    global _shutdown

    # Create directories
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("🎬  Tubee Watch Folder Started")
    logger.info(f"   Watching: {WATCH_DIR}")
    logger.info(f"   Output:   {OUTPUT_DIR}")
    logger.info("=" * 60)
    logger.info("How to use:")
    logger.info(f"  1. Drop video files into: {WATCH_DIR}")
    logger.info(f"  2. Add a music file (optional)")
    logger.info(f"  3. Create prompt.txt with your edit instructions")
    logger.info(f"  4. Watch Tubee auto-process and save to: {OUTPUT_DIR}")
    logger.info("  Press Ctrl+C to stop")
    logger.info("=" * 60)

    while not _shutdown:
        try:
            content = scan_input_folder(WATCH_DIR)

            if content.get("ready"):
                logger.info("Files detected — starting processing...")
                process_and_archive(content)
            else:
                # Log what's missing (only occasionally to avoid spam)
                if not hasattr(main, "_last_status_log") or time.time() - main._last_status_log > 30:
                    waiting_for = []
                    if not (WATCH_DIR / "prompt.txt").exists():
                        waiting_for.append("prompt.txt")
                    video_count = sum(
                        1 for f in WATCH_DIR.glob("*")
                        if f.suffix.lower() in VIDEO_EXTENSIONS
                    )
                    if video_count == 0:
                        waiting_for.append("video files")

                    if waiting_for:
                        logger.info(f"⏳  Waiting for: {', '.join(waiting_for)}")
                    main._last_status_log = time.time()

        except Exception as e:
            logger.error(f"Watcher loop error: {e}", exc_info=True)

        # Sleep in small increments so we can respond to shutdown quickly
        for _ in range(int(POLL_INTERVAL / 0.1)):
            if _shutdown:
                break
            time.sleep(0.1)

    logger.info("Tubee watcher stopped.")


if __name__ == "__main__":
    main()
