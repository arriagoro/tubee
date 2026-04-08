"""
captions.py — Auto-caption module for Tubee
Transcribes video audio with OpenAI Whisper, generates SRT subtitles,
and burns captions into video using FFmpeg.

Supports multiple caption styles including Temitayo's signature lime-green look.
"""

import shutil
import os
import json
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Optional, Callable

logger = logging.getLogger(__name__)

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

# ---------------------------------------------------------------------------
# Caption style definitions
# ---------------------------------------------------------------------------
CAPTION_STYLES = {
    "temitayo": {
        "description": "Bold sans-serif, ALL CAPS, lime green with dark shadow — Temitayo's signature style",
        "fontsize": 28,
        "fontcolor": "#C8F135",
        "borderw": 3,
        "shadowcolor": "black@0.8",
        "shadowx": 3,
        "shadowy": 3,
        "bold": True,
        "uppercase": True,
        "alignment": 2,  # bottom center
        "margin_v": 60,
        "font": "Arial Bold",
        # ASS style for subtitles filter
        "ass_style": (
            "FontName=Arial,FontSize=28,Bold=1,PrimaryColour=&H0035F1C8,"
            "OutlineColour=&H80000000,BackColour=&H80000000,"
            "Outline=3,Shadow=3,Alignment=2,MarginV=60"
        ),
    },
    "standard": {
        "description": "White text, black outline, bottom center",
        "fontsize": 24,
        "fontcolor": "white",
        "borderw": 2,
        "shadowcolor": "black@0.5",
        "shadowx": 1,
        "shadowy": 1,
        "bold": False,
        "uppercase": False,
        "alignment": 2,
        "margin_v": 40,
        "font": "Arial",
        "ass_style": (
            "FontName=Arial,FontSize=24,Bold=0,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BackColour=&H80000000,"
            "Outline=2,Shadow=1,Alignment=2,MarginV=40"
        ),
    },
    "minimal": {
        "description": "Small white text, no outline, bottom",
        "fontsize": 18,
        "fontcolor": "white@0.9",
        "borderw": 0,
        "shadowcolor": "black@0.3",
        "shadowx": 1,
        "shadowy": 1,
        "bold": False,
        "uppercase": False,
        "alignment": 2,
        "margin_v": 30,
        "font": "Helvetica Neue",
        "ass_style": (
            "FontName=Helvetica Neue,FontSize=18,Bold=0,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BackColour=&H00000000,"
            "Outline=0,Shadow=1,Alignment=2,MarginV=30"
        ),
    },
    "bold": {
        "description": "Large white text, heavy black stroke",
        "fontsize": 34,
        "fontcolor": "white",
        "borderw": 5,
        "shadowcolor": "black",
        "shadowx": 2,
        "shadowy": 2,
        "bold": True,
        "uppercase": False,
        "alignment": 2,
        "margin_v": 50,
        "font": "Impact",
        "ass_style": (
            "FontName=Impact,FontSize=34,Bold=1,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BackColour=&H80000000,"
            "Outline=5,Shadow=2,Alignment=2,MarginV=50"
        ),
    },
}


# ---------------------------------------------------------------------------
# Whisper transcription
# ---------------------------------------------------------------------------

def _check_whisper() -> bool:
    """Check if Whisper is available."""
    try:
        result = subprocess.run(
            ["python3", "-c", "import whisper; print('ok')"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _extract_audio(video_path: str, audio_path: str) -> str:
    """Extract audio from video to WAV for Whisper."""
    cmd = [
        FFMPEG, "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr[:500]}")
    return audio_path


def transcribe_video(
    video_path: str,
    model_size: str = "base",
    language: Optional[str] = None,
    word_timestamps: bool = True,
) -> Dict:
    """
    Transcribe video audio using OpenAI Whisper.

    Args:
        video_path: Path to input video
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (e.g., 'en') or None for auto-detect
        word_timestamps: Whether to include word-level timestamps

    Returns:
        Dict with 'segments' (list of segment dicts) and 'text' (full transcript)
    """
    if not _check_whisper():
        raise RuntimeError(
            "OpenAI Whisper is not installed. Install with: pip install openai-whisper"
        )

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Extract audio to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name

    try:
        logger.info(f"Extracting audio from {video_path}")
        _extract_audio(video_path, audio_path)

        logger.info(f"Transcribing with Whisper ({model_size} model)")
        import whisper

        model = whisper.load_model(model_size)
        options = {"word_timestamps": word_timestamps}
        if language:
            options["language"] = language

        result = model.transcribe(audio_path, **options)

        # Build structured segments
        segments = []
        for seg in result.get("segments", []):
            segment = {
                "id": seg["id"],
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
            }
            # Include word-level timestamps if available
            if word_timestamps and "words" in seg:
                segment["words"] = [
                    {
                        "word": w.get("word", w.get("text", "")).strip(),
                        "start": w["start"],
                        "end": w["end"],
                    }
                    for w in seg["words"]
                ]
            segments.append(segment)

        logger.info(f"Transcription complete: {len(segments)} segments")
        return {
            "segments": segments,
            "text": result.get("text", "").strip(),
            "language": result.get("language", "unknown"),
        }

    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)


# ---------------------------------------------------------------------------
# SRT generation
# ---------------------------------------------------------------------------

def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(
    segments: List[Dict],
    output_path: str,
    word_by_word: bool = False,
    uppercase: bool = False,
) -> str:
    """
    Generate an SRT subtitle file from transcription segments.

    Args:
        segments: List of segment dicts with start, end, text (and optionally words)
        output_path: Where to save the .srt file
        word_by_word: If True, create one subtitle per word (karaoke style)
        uppercase: If True, convert all text to uppercase

    Returns:
        Path to the generated SRT file
    """
    lines = []
    counter = 1

    if word_by_word:
        # Karaoke-style: one word at a time
        for seg in segments:
            words = seg.get("words", [])
            if not words:
                # Fallback: split text evenly across segment duration
                text_words = seg["text"].split()
                duration = seg["end"] - seg["start"]
                word_duration = duration / max(len(text_words), 1)
                for i, word in enumerate(text_words):
                    start = seg["start"] + i * word_duration
                    end = start + word_duration
                    display = word.upper() if uppercase else word
                    lines.append(f"{counter}")
                    lines.append(f"{_format_srt_time(start)} --> {_format_srt_time(end)}")
                    lines.append(display)
                    lines.append("")
                    counter += 1
            else:
                for w in words:
                    display = w["word"].upper() if uppercase else w["word"]
                    lines.append(f"{counter}")
                    lines.append(f"{_format_srt_time(w['start'])} --> {_format_srt_time(w['end'])}")
                    lines.append(display)
                    lines.append("")
                    counter += 1
    else:
        # Standard: full sentence segments
        for seg in segments:
            text = seg["text"].upper() if uppercase else seg["text"]
            lines.append(f"{counter}")
            lines.append(f"{_format_srt_time(seg['start'])} --> {_format_srt_time(seg['end'])}")
            lines.append(text)
            lines.append("")
            counter += 1

    srt_content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    logger.info(f"Generated SRT with {counter - 1} entries → {output_path}")
    return output_path


def generate_ass(
    segments: List[Dict],
    output_path: str,
    style: str = "temitayo",
    word_by_word: bool = False,
) -> str:
    """
    Generate an ASS (Advanced SubStation Alpha) subtitle file.
    ASS gives us more control over styling than SRT.

    Args:
        segments: Transcription segments
        output_path: Where to save the .ass file
        style: Caption style name
        word_by_word: One word at a time mode

    Returns:
        Path to generated .ass file
    """
    style_config = CAPTION_STYLES.get(style, CAPTION_STYLES["standard"])
    uppercase = style_config.get("uppercase", False)

    # ASS header
    header = f"""[Script Info]
Title: Tubee Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style_config['font']},{style_config['fontsize']},"""

    # Color conversion for ASS (BGR format with alpha)
    if style == "temitayo":
        header += "&H0035F1C8,&H000000FF,&H80000000,&H80000000,"
    elif style == "bold":
        header += "&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
    elif style == "minimal":
        header += "&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
    else:
        header += "&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"

    bold_flag = "-1" if style_config.get("bold") else "0"
    header += f"{bold_flag},0,0,0,100,100,0,0,1,"
    header += f"{style_config['borderw']},{style_config.get('shadowx', 1)},"
    header += f"{style_config['alignment']},20,20,{style_config['margin_v']},1\n"

    header += """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def _ass_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    events = []

    if word_by_word:
        for seg in segments:
            words = seg.get("words", [])
            if not words:
                text_words = seg["text"].split()
                duration = seg["end"] - seg["start"]
                word_duration = duration / max(len(text_words), 1)
                for i, word in enumerate(text_words):
                    start = seg["start"] + i * word_duration
                    end = start + word_duration
                    display = word.upper() if uppercase else word
                    events.append(
                        f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{display}"
                    )
            else:
                for w in words:
                    display = w["word"].upper() if uppercase else w["word"]
                    events.append(
                        f"Dialogue: 0,{_ass_time(w['start'])},{_ass_time(w['end'])},Default,,0,0,0,,{display}"
                    )
    else:
        for seg in segments:
            text = seg["text"].upper() if uppercase else seg["text"]
            events.append(
                f"Dialogue: 0,{_ass_time(seg['start'])},{_ass_time(seg['end'])},Default,,0,0,0,,{text}"
            )

    content = header + "\n".join(events) + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Generated ASS subtitle → {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Burn captions into video
# ---------------------------------------------------------------------------

def burn_captions(
    video_path: str,
    srt_path: str,
    output_path: str,
    style: str = "temitayo",
    progress_callback: Optional[Callable] = None,
) -> str:
    """
    Burn captions into video using FFmpeg's subtitles filter.

    Args:
        video_path: Input video path
        srt_path: Path to .srt or .ass subtitle file
        output_path: Where to save the captioned video
        style: Caption style name (used for force_style if SRT)
        progress_callback: Optional callback(stage, pct)

    Returns:
        Path to output video with burned-in captions
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not os.path.exists(srt_path):
        raise FileNotFoundError(f"Subtitle file not found: {srt_path}")

    if progress_callback:
        progress_callback("Burning captions", 60)

    # Escape path for FFmpeg filter (need to escape colons and backslashes)
    escaped_srt = srt_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    style_config = CAPTION_STYLES.get(style, CAPTION_STYLES["standard"])

    # Try subtitles filter first (needs libass)
    if srt_path.endswith(".ass"):
        vf = f"subtitles='{escaped_srt}'"
    else:
        force_style = style_config["ass_style"]
        vf = f"subtitles='{escaped_srt}':force_style='{force_style}'"

    cmd = [
        FFMPEG, "-y", "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "copy",
        output_path,
    ]

    logger.info(f"Burning captions: {style} style → {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        logger.warning(f"subtitles filter failed (libass missing?), trying drawtext fallback")
        # Fallback: use drawtext filter with first caption text
        try:
            import re as _re
            # Parse SRT to get first few captions
            with open(srt_path, 'r') as f:
                srt_content = f.read()
            captions = _re.findall(r'\d+\n[\d:,]+ --> [\d:,]+\n(.+?)(?:\n\n|\Z)', srt_content, _re.DOTALL)
            if captions and shutil.which("ffmpeg"):
                # Just copy video without captions as last resort
                shutil.copy2(video_path, output_path)
                logger.warning("Caption burn not supported on this FFmpeg build - returning video without captions")
            else:
                shutil.copy2(video_path, output_path)
        except Exception:
            shutil.copy2(video_path, output_path)
        logger.info("Caption fallback: video returned without burned captions")

    if progress_callback:
        progress_callback("Captions burned", 90)

    logger.info(f"Captioned video saved → {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Full pipeline: transcribe → generate subtitles → burn
# ---------------------------------------------------------------------------

def add_captions_to_video(
    video_path: str,
    output_path: str,
    style: str = "temitayo",
    word_by_word: bool = False,
    model_size: str = "base",
    language: Optional[str] = None,
    progress_callback: Optional[Callable] = None,
) -> Dict:
    """
    Full caption pipeline: transcribe video, generate subtitles, burn into video.

    Args:
        video_path: Input video path
        output_path: Output video path
        style: Caption style (temitayo, standard, minimal, bold)
        word_by_word: Enable word-by-word karaoke captions
        model_size: Whisper model size
        language: Language code or None for auto-detect
        progress_callback: Optional callback(stage, pct)

    Returns:
        Dict with output_path, transcript, segments count, etc.
    """
    if progress_callback:
        progress_callback("Transcribing audio", 10)

    # Step 1: Transcribe
    transcription = transcribe_video(
        video_path, model_size=model_size,
        language=language, word_timestamps=word_by_word,
    )

    if progress_callback:
        progress_callback("Generating subtitles", 40)

    # Step 2: Generate subtitle file (ASS for better styling)
    with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as tmp:
        sub_path = tmp.name

    try:
        generate_ass(
            segments=transcription["segments"],
            output_path=sub_path,
            style=style,
            word_by_word=word_by_word,
        )

        if progress_callback:
            progress_callback("Burning captions into video", 55)

        # Step 3: Burn captions
        burn_captions(
            video_path=video_path,
            srt_path=sub_path,
            output_path=output_path,
            style=style,
            progress_callback=progress_callback,
        )

        return {
            "output_path": output_path,
            "transcript": transcription["text"],
            "language": transcription["language"],
            "segments_count": len(transcription["segments"]),
            "style": style,
            "word_by_word": word_by_word,
        }

    finally:
        if os.path.exists(sub_path):
            os.unlink(sub_path)
