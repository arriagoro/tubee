"""
beat_sync.py — Music beat detection for Tubee
Uses librosa to analyze audio/video files and return beat timestamps.
Supports both standalone audio files and video files (audio extracted first).
"""

import os
import logging
import tempfile
import subprocess
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, output_path: Optional[str] = None) -> str:
    """
    Extract audio from a video file using FFmpeg.

    Args:
        video_path: Path to the input video file.
        output_path: Where to save the extracted audio. If None, creates a temp file.

    Returns:
        Path to the extracted audio file (WAV format).
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

    cmd = [
        "ffmpeg",
        "-y",                   # Overwrite output
        "-i", video_path,
        "-vn",                  # No video
        "-acodec", "pcm_s16le", # PCM 16-bit little-endian (WAV)
        "-ar", "44100",         # 44.1kHz sample rate
        "-ac", "2",             # Stereo
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

    return output_path


def detect_beats(
    audio_path: str,
    is_video: bool = False,
    min_beat_interval: float = 0.1,
) -> Dict[str, Any]:
    """
    Detect beats in an audio or video file using librosa.

    Args:
        audio_path: Path to audio or video file.
        is_video: If True, extract audio from video first.
        min_beat_interval: Minimum interval between beats in seconds.

    Returns:
        Dict with:
            - bpm (float): Estimated tempo in beats per minute
            - beats (List[float]): Beat timestamps in seconds
            - downbeats (List[float]): Estimated downbeat timestamps (every 4th beat)
            - total_duration (float): Total audio duration in seconds
            - onset_times (List[float]): Onset event timestamps (transients)
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    tmp_audio = None

    try:
        import librosa
        import numpy as np

        # Extract audio from video if needed
        if is_video:
            logger.info(f"Extracting audio from video: {audio_path}")
            tmp_audio = extract_audio(audio_path)
            load_path = tmp_audio
        else:
            load_path = audio_path

        logger.info(f"Analyzing beats in: {load_path}")

        # Load audio
        y, sr = librosa.load(load_path, sr=None, mono=True)
        total_duration = float(len(y)) / sr

        # Detect tempo and beat frames
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

        # Handle newer librosa where tempo might be an array
        if hasattr(tempo, '__len__'):
            bpm = float(tempo[0])
        else:
            bpm = float(tempo)

        # Convert beat frames to timestamps
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)

        # Filter out beats that are too close together
        filtered_beats = []
        last_beat = -min_beat_interval
        for t in beat_times:
            if t - last_beat >= min_beat_interval:
                filtered_beats.append(float(t))
                last_beat = t

        # Estimate downbeats (every 4th beat, starting from beat 0)
        downbeats = [filtered_beats[i] for i in range(0, len(filtered_beats), 4)]

        # Detect onsets (transients — useful for cut points even without a strong beat)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()
        onset_times = [float(t) for t in onset_times]

        result = {
            "bpm": round(bpm, 2),
            "beats": [round(t, 4) for t in filtered_beats],
            "downbeats": [round(t, 4) for t in downbeats],
            "total_duration": round(total_duration, 4),
            "onset_times": [round(t, 4) for t in onset_times],
        }

        logger.info(
            f"Beat detection complete: {bpm:.1f} BPM, "
            f"{len(filtered_beats)} beats, "
            f"{total_duration:.1f}s duration"
        )
        return result

    except ImportError:
        logger.warning("librosa not available, using fallback beat detection")
        return _fallback_beat_detect(audio_path, is_video)
    finally:
        # Clean up temp audio file
        if tmp_audio and os.path.exists(tmp_audio):
            os.unlink(tmp_audio)


def _fallback_beat_detect(audio_path: str, is_video: bool = False) -> Dict[str, Any]:
    """
    Fallback beat detection when librosa is not available.
    Returns evenly-spaced beat intervals based on a default 120 BPM assumption.
    Also uses FFprobe to get actual duration.

    Args:
        audio_path: Path to the audio/video file.
        is_video: Whether the input is a video file.

    Returns:
        Dict with approximate beat data (same structure as detect_beats).
    """
    logger.warning("Using fallback beat detection (evenly-spaced at 120 BPM)")

    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = 60.0  # Default fallback

    if result.returncode == 0:
        import json
        fmt = json.loads(result.stdout)
        duration = float(fmt.get("format", {}).get("duration", 60.0))

    bpm = 120.0
    beat_interval = 60.0 / bpm
    beats = [round(i * beat_interval, 4) for i in range(int(duration / beat_interval))]
    downbeats = beats[::4]

    return {
        "bpm": bpm,
        "beats": beats,
        "downbeats": downbeats,
        "total_duration": round(duration, 4),
        "onset_times": beats,  # Use beats as onset approximation
    }


def get_beat_aligned_cuts(
    beat_data: Dict[str, Any],
    target_duration: float,
    cuts_per_bar: int = 1,
) -> List[float]:
    """
    Generate cut timestamps aligned to the beat grid.

    Args:
        beat_data: Output from detect_beats().
        target_duration: Total target duration for the edit.
        cuts_per_bar: How many cuts per 4-beat bar (1=downbeats, 2=half-bar, 4=every beat).

    Returns:
        List of timestamps (seconds) where cuts should happen.
    """
    if cuts_per_bar == 1:
        source = beat_data["downbeats"]
    elif cuts_per_bar == 2:
        # Alternate between beats 1 and 3
        beats = beat_data["beats"]
        source = [beats[i] for i in range(0, len(beats), 2)]
    else:
        source = beat_data["beats"]

    # Only return cuts within target duration
    cuts = [t for t in source if t <= target_duration]
    return cuts


if __name__ == "__main__":
    import sys
    import json

    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python beat_sync.py <audio_or_video_file>")
        sys.exit(1)

    path = sys.argv[1]
    # Auto-detect if it's a video
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv"}
    is_vid = os.path.splitext(path)[1].lower() in video_exts

    result = detect_beats(path, is_video=is_vid)
    print(json.dumps(result, indent=2))
