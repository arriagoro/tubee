#!/usr/bin/env python3
"""
watch_ingest.py — Always-On Volume Watcher Daemon
==================================================
Lightweight background daemon that watches /Volumes/ for new mounts
and automatically runs ingest.py when video files are found.

This script is designed to run as a macOS launchd service.
See: ../launchd/com.tubee.watch-ingest.plist

Usage (direct):
    python watch_ingest.py [--dest ~/footage] [--auto-edit "Make a highlight reel"]

Usage (as daemon):
    launchctl load ~/Library/LaunchAgents/com.tubee.watch-ingest.plist
    launchctl unload ~/Library/LaunchAgents/com.tubee.watch-ingest.plist

Log file:
    ~/footage/ingest.log (configurable via --log)
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Set, Optional

# watchdog for /Volumes/ monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: watchdog not installed. Run: pip install watchdog")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VOLUMES_PATH = "/Volumes"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mxf", ".r3d", ".avi", ".mkv", ".m4v", ".braw"}

# How long to wait after a volume appears before ingesting
# (gives the OS time to fully mount it)
MOUNT_SETTLE_SECONDS = 3

# Minimum number of video files on a drive to trigger ingest
MIN_VIDEO_FILES = 1


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(log_path: str) -> logging.Logger:
    """Configure logging to both file and stdout."""
    log_path = str(Path(log_path).expanduser().resolve())
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger = logging.getLogger("watch_ingest")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler (persistent log)
    fh = logging.FileHandler(log_path)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console handler (for direct runs / launchd stdout)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# Volume detection
# ---------------------------------------------------------------------------

def has_video_files(volume_path: str, min_count: int = MIN_VIDEO_FILES) -> bool:
    """
    Quickly check if a volume has any video files.
    Stops scanning as soon as min_count files are found.
    """
    count = 0
    try:
        for root, dirs, files in os.walk(volume_path):
            # Skip hidden system directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                if Path(fname).suffix.lower() in VIDEO_EXTENSIONS:
                    count += 1
                    if count >= min_count:
                        return True
    except PermissionError:
        pass
    return count >= min_count


# ---------------------------------------------------------------------------
# Watchdog event handler
# ---------------------------------------------------------------------------

class VolumeWatcher(FileSystemEventHandler):
    """
    Watches /Volumes/ for new directory entries (= new mounts).
    When a new volume appears with video files, triggers ingest.py.
    """

    def __init__(
        self,
        ingest_script: str,
        dest_root: str,
        auto_edit_prompt: Optional[str],
        logger: logging.Logger,
        already_known: Set[str],
    ):
        super().__init__()
        self._ingest_script = ingest_script
        self._dest_root = dest_root
        self._auto_edit_prompt = auto_edit_prompt
        self._logger = logger
        self._known_volumes = already_known
        self._lock = threading.Lock()
        self._active_ingests: Set[str] = set()  # Volumes currently being ingested

    def on_created(self, event):
        """Called when a new item appears in /Volumes/."""
        if not event.is_directory:
            return

        volume_path = event.src_path

        with self._lock:
            if volume_path in self._known_volumes:
                return  # Already seen this one
            if volume_path in self._active_ingests:
                return  # Already ingesting
            self._known_volumes.add(volume_path)

        # Handle in background thread so watchdog isn't blocked
        t = threading.Thread(
            target=self._handle_new_volume,
            args=(volume_path,),
            daemon=True,
            name=f"ingest-{os.path.basename(volume_path)}",
        )
        t.start()

    def on_deleted(self, event):
        """Called when a volume is unmounted/ejected."""
        if not event.is_directory:
            return
        volume_path = event.src_path
        with self._lock:
            self._known_volumes.discard(volume_path)
            self._active_ingests.discard(volume_path)
        self._logger.info(f"Volume unmounted: {volume_path}")

    def _handle_new_volume(self, volume_path: str) -> None:
        """Check for video files and trigger ingest if found."""
        self._logger.info(f"New volume detected: {volume_path}")

        # Wait for the OS to fully mount the volume
        time.sleep(MOUNT_SETTLE_SECONDS)

        # Verify it still exists (not immediately ejected)
        if not os.path.isdir(volume_path):
            self._logger.info(f"Volume disappeared before ingest: {volume_path}")
            return

        # Check for video files
        self._logger.info(f"Scanning for video files: {volume_path}")
        if not has_video_files(volume_path):
            self._logger.info(f"No video files found on {volume_path}, ignoring")
            return

        # Mark as active and run ingest
        with self._lock:
            self._active_ingests.add(volume_path)

        self._logger.info(f"Starting ingest from: {volume_path}")
        self._run_ingest(volume_path)

        with self._lock:
            self._active_ingests.discard(volume_path)

    def _run_ingest(self, volume_path: str) -> None:
        """
        Spawn ingest.py as a subprocess.
        This keeps watch_ingest.py lightweight and lets ingest.py handle
        all the copying, notifications, and Tubee triggering.
        """
        cmd = [
            sys.executable,
            self._ingest_script,
            "--drive", volume_path,
            "--dest", self._dest_root,
        ]

        if self._auto_edit_prompt:
            cmd.extend(["--auto-edit", self._auto_edit_prompt])

        self._logger.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=False,  # Let output flow to our log
                text=True,
                timeout=7200,  # 2 hour timeout for large drives
            )
            if result.returncode == 0:
                self._logger.info(f"Ingest completed successfully: {volume_path}")
            else:
                self._logger.error(
                    f"Ingest failed for {volume_path} "
                    f"(exit code {result.returncode})"
                )
        except subprocess.TimeoutExpired:
            self._logger.error(f"Ingest timed out for {volume_path}")
        except Exception as e:
            self._logger.error(f"Failed to run ingest for {volume_path}: {e}")


# ---------------------------------------------------------------------------
# Main daemon loop
# ---------------------------------------------------------------------------

def run_daemon(
    dest_root: str,
    log_path: str,
    auto_edit_prompt: Optional[str] = None,
) -> None:
    """
    Start the volume-watching daemon. Blocks until interrupted.

    Args:
        dest_root:        Root footage destination (e.g. ~/footage)
        log_path:         Path to log file
        auto_edit_prompt: If set, auto-trigger Tubee after each ingest
    """
    logger = setup_logging(log_path)

    dest_root = str(Path(dest_root).expanduser().resolve())
    ingest_script = str(Path(__file__).parent / "ingest.py")

    if not os.path.exists(ingest_script):
        logger.error(f"ingest.py not found at: {ingest_script}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Tubee Watch Ingest — Starting")
    logger.info(f"  Watching:   {VOLUMES_PATH}")
    logger.info(f"  Dest root:  {dest_root}")
    logger.info(f"  Log file:   {log_path}")
    logger.info(f"  ingest.py:  {ingest_script}")
    if auto_edit_prompt:
        logger.info(f"  Auto-edit:  {auto_edit_prompt}")
    logger.info("=" * 60)

    # Snapshot of currently known volumes (don't ingest existing mounts on startup)
    known_volumes: Set[str] = set()
    try:
        for name in os.listdir(VOLUMES_PATH):
            known_volumes.add(os.path.join(VOLUMES_PATH, name))
        logger.info(f"Ignoring {len(known_volumes)} existing volume(s) on startup")
    except Exception as e:
        logger.warning(f"Could not list {VOLUMES_PATH}: {e}")

    # Set up watchdog observer
    handler = VolumeWatcher(
        ingest_script=ingest_script,
        dest_root=dest_root,
        auto_edit_prompt=auto_edit_prompt,
        logger=logger,
        already_known=known_volumes,
    )

    observer = Observer()
    observer.schedule(handler, VOLUMES_PATH, recursive=False)
    observer.start()

    logger.info(f"Watching {VOLUMES_PATH} for new volumes... (PID: {os.getpid()})")

    try:
        while True:
            # Heartbeat log every 30 minutes to confirm daemon is alive
            time.sleep(1800)
            logger.info(f"Daemon alive — watching {VOLUMES_PATH}")
    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        observer.stop()
        observer.join()
        logger.info("Tubee Watch Ingest — Stopped")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Tubee Watch Ingest — Always-on volume watcher daemon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dest",
        default="~/footage",
        help="Destination footage root directory (default: ~/footage)",
    )
    parser.add_argument(
        "--log",
        default="~/footage/ingest.log",
        help="Log file path (default: ~/footage/ingest.log)",
    )
    parser.add_argument(
        "--auto-edit",
        metavar="PROMPT",
        help="After each ingest, auto-trigger Tubee with this prompt",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_daemon(
        dest_root=args.dest,
        log_path=args.log,
        auto_edit_prompt=args.auto_edit,
    )


if __name__ == "__main__":
    main()
