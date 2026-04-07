"""
take_analyzer.py — Analyze video takes to identify good vs bad ones.

Uses Whisper for transcription + Kimi K2 Vision for visual quality assessment.
Designed for talking-head content where videographers have multiple takes with
mistakes, stumbles, repeated thoughts, or weak delivery.
"""

import os
import json
import logging
import subprocess
import base64
import tempfile
from typing import List, Dict, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

FFMPEG = os.environ.get("FFMPEG_PATH", "/opt/homebrew/bin/ffmpeg")
FFPROBE = os.environ.get("FFPROBE_PATH", "/opt/homebrew/bin/ffprobe")
KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "")
KIMI_MODEL = "kimi-k2-turbo-preview"


def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    cmd = [
        FFPROBE, "-v", "quiet", "-print_format", "json",
        "-show_format", video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0))
    except Exception as e:
        logger.warning(f"Could not get duration for {video_path}: {e}")
    return 0.0


def _extract_audio(video_path: str, output_path: str) -> bool:
    """Extract audio from video using FFmpeg."""
    cmd = [
        FFMPEG, "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        logger.warning(f"Audio extraction failed for {video_path}: {e}")
        return False


def _extract_frames(video_path: str, output_dir: str, num_frames: int = 3) -> List[str]:
    """Extract evenly-spaced frames from a video clip."""
    duration = _get_video_duration(video_path)
    if duration <= 0:
        return []

    frame_paths = []
    positions = [duration * (i + 1) / (num_frames + 1) for i in range(num_frames)]

    for i, pos in enumerate(positions):
        frame_path = os.path.join(output_dir, f"frame_{i:02d}.jpg")
        cmd = [
            FFMPEG, "-y", "-ss", str(pos),
            "-i", video_path, "-frames:v", "1",
            "-vf", "scale='min(512,iw)':-1",
            "-q:v", "4", frame_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
            if os.path.exists(frame_path):
                frame_paths.append(frame_path)
        except Exception:
            pass

    return frame_paths


def _frames_to_base64(frame_paths: List[str]) -> List[str]:
    """Convert frame images to base64 strings."""
    result = []
    for path in frame_paths:
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                result.append(b64)
        except Exception:
            pass
    return result


def _transcribe_audio(audio_path: str) -> Dict:
    """Transcribe audio using Whisper."""
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, language="en")
        return {
            "text": result.get("text", ""),
            "segments": [
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip(),
                }
                for seg in result.get("segments", [])
            ],
        }
    except ImportError:
        # Fallback: try CLI whisper
        logger.info("Whisper Python module not available, trying CLI...")
        try:
            result = subprocess.run(
                ["python3", "-m", "whisper", audio_path, "--language", "en",
                 "--output_format", "json", "--output_dir", str(Path(audio_path).parent)],
                capture_output=True, text=True, timeout=300,
            )
            json_path = str(Path(audio_path).with_suffix(".json"))
            if os.path.exists(json_path):
                with open(json_path) as f:
                    data = json.load(f)
                return {
                    "text": data.get("text", ""),
                    "segments": [
                        {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
                        for s in data.get("segments", [])
                    ],
                }
        except Exception as e:
            logger.warning(f"Whisper CLI failed: {e}")

    return {"text": "", "segments": []}


def _analyze_with_kimi(transcript: str, frame_b64s: List[str], filename: str,
                       all_transcripts: Optional[List[str]] = None) -> Dict:
    """Send transcript + frames to Kimi K2 for quality analysis."""
    if not KIMI_API_KEY:
        logger.warning("No KIMI_API_KEY — returning default analysis")
        return {
            "quality_score": 0.5,
            "issues": [],
            "recommendation": "keep",
            "reason": "No AI analysis available (missing KIMI_API_KEY)",
        }

    try:
        from openai import OpenAI as KimiClient

        kimi = KimiClient(api_key=KIMI_API_KEY, base_url="https://api.moonshot.ai/v1")

        other_context = ""
        if all_transcripts:
            other_context = "\n\nOther takes for context (to detect repeated content):\n"
            for i, t in enumerate(all_transcripts):
                if t != transcript:
                    other_context += f"  Take {i+1}: {t[:200]}...\n"

        content = [
            {
                "type": "text",
                "text": f"""You are a professional video editor analyzing a talking-head take from file "{filename}".

Transcript of this take:
"{transcript}"
{other_context}

Rate this take 0.0-1.0 based on:
- Confidence and energy (no stumbles, clear speech)
- No repeated content from other takes
- Good pacing and delivery
- Complete thoughts (not cut off mid-sentence)

Identify specific issues with approximate timestamps if possible.
Recommend "keep" or "remove".

Respond in this exact JSON format:
{{
  "quality_score": 0.85,
  "issues": ["stumble at ~2.3s", "repeated thought from another take"],
  "recommendation": "keep",
  "reason": "Strong delivery, clear message with good energy"
}}

Respond with ONLY the JSON, no other text.""",
            }
        ]

        # Add frames as vision input
        for b64 in frame_b64s[:3]:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })

        response = kimi.chat.completions.create(
            model=KIMI_MODEL,
            messages=[{"role": "user", "content": content}],
            temperature=0.3,
        )

        response_text = response.choices[0].message.content.strip()

        # Parse JSON from response
        # Strip markdown code fences if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        analysis = json.loads(response_text)
        return {
            "quality_score": float(analysis.get("quality_score", 0.5)),
            "issues": analysis.get("issues", []),
            "recommendation": analysis.get("recommendation", "keep"),
            "reason": analysis.get("reason", ""),
        }

    except Exception as e:
        logger.error(f"Kimi analysis failed for {filename}: {e}")
        return {
            "quality_score": 0.5,
            "issues": [f"AI analysis error: {str(e)}"],
            "recommendation": "keep",
            "reason": "Could not analyze — keeping by default",
        }


def analyze_takes(
    video_files: List[str],
    job_id: str,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> Dict:
    """
    Analyze video clips to identify good vs bad takes.

    Uses Whisper for transcription + Kimi K2 Vision for visual quality assessment.

    Returns:
    {
        "takes": [
            {
                "file": "clip.mp4",
                "start": 0.0,
                "end": 10.5,
                "transcript": "...",
                "quality_score": 0.85,
                "issues": ["stumble at 2.3s", "repeated thought"],
                "recommendation": "keep" | "remove",
                "reason": "Strong delivery, clear message"
            }
        ],
        "summary": "Kept 4/7 takes, removed 3 weak takes"
    }
    """
    if progress_callback:
        progress_callback("Analyzing takes", 5)

    takes = []
    all_transcripts = []
    total = len(video_files)
    temp_dirs = []

    try:
        # Step 1: Transcribe all takes first (need all transcripts for comparison)
        for i, video_path in enumerate(video_files):
            if not os.path.exists(video_path):
                logger.warning(f"Video file not found: {video_path}")
                continue

            filename = Path(video_path).name
            pct = int(5 + (i / total) * 40)
            if progress_callback:
                progress_callback(f"Transcribing take {i+1}/{total}: {filename}", pct)

            temp_dir = tempfile.mkdtemp(prefix=f"take_{job_id}_{i}_")
            temp_dirs.append(temp_dir)

            # Extract audio
            audio_path = os.path.join(temp_dir, "audio.wav")
            _extract_audio(video_path, audio_path)

            # Transcribe
            transcript_data = {"text": "", "segments": []}
            if os.path.exists(audio_path):
                transcript_data = _transcribe_audio(audio_path)

            all_transcripts.append(transcript_data["text"])

            # Extract frames
            frame_paths = _extract_frames(video_path, temp_dir)
            frame_b64s = _frames_to_base64(frame_paths)

            duration = _get_video_duration(video_path)

            takes.append({
                "file": filename,
                "path": video_path,
                "start": 0.0,
                "end": duration,
                "transcript": transcript_data["text"],
                "segments": transcript_data["segments"],
                "frame_b64s": frame_b64s,
                "quality_score": 0.5,
                "issues": [],
                "recommendation": "keep",
                "reason": "",
            })

        # Step 2: Analyze each take with Kimi (now with full context)
        for i, take in enumerate(takes):
            pct = int(45 + (i / max(len(takes), 1)) * 50)
            if progress_callback:
                progress_callback(f"AI analyzing take {i+1}/{len(takes)}: {take['file']}", pct)

            analysis = _analyze_with_kimi(
                transcript=take["transcript"],
                frame_b64s=take.get("frame_b64s", []),
                filename=take["file"],
                all_transcripts=all_transcripts,
            )

            take["quality_score"] = analysis["quality_score"]
            take["issues"] = analysis["issues"]
            take["recommendation"] = analysis["recommendation"]
            take["reason"] = analysis["reason"]

            # Clean up internal fields
            take.pop("frame_b64s", None)
            take.pop("segments", None)
            take.pop("path", None)

        # Generate summary
        kept = sum(1 for t in takes if t["recommendation"] == "keep")
        removed = sum(1 for t in takes if t["recommendation"] == "remove")
        total_takes = len(takes)

        summary = f"Kept {kept}/{total_takes} takes, removed {removed} weak takes"

        if progress_callback:
            progress_callback("Take analysis complete", 100)

        return {
            "takes": takes,
            "summary": summary,
            "kept_count": kept,
            "removed_count": removed,
            "total_count": total_takes,
        }

    finally:
        # Cleanup temp directories
        import shutil
        for td in temp_dirs:
            try:
                shutil.rmtree(td, ignore_errors=True)
            except Exception:
                pass
