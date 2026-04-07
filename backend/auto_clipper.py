"""
auto_clipper.py — Auto-Clipper module for Tubee
Analyzes long videos (streams, podcasts, recordings), finds the best moments,
and clips them into short social-media-ready clips.

Strategy:
1. Extract audio from video with FFmpeg
2. Transcribe FULL video with Whisper (tiny for speed, medium for quality)
3. Analyze transcript in chunks — find high-energy moments, cues, etc.
4. Detect loud audio moments via FFmpeg volumedetect
5. Extract frames around candidate moments for visual scoring
6. Send to Kimi Vision for final scoring
7. Return top N moments sorted by score

Also: extract_clip() to crop, format, and burn captions for social media.
"""

import os
import re
import json
import math
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple

logger = logging.getLogger(__name__)

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

# ---------------------------------------------------------------------------
# High-energy keywords and streamer cues
# ---------------------------------------------------------------------------
HIGH_ENERGY_WORDS = [
    "OH MY GOD", "INSANE", "NO WAY", "HOLY", "CLIP THAT", "CLIP IT",
    "WHAT THE", "LET'S GO", "LETS GO", "WOW", "AMAZING", "INCREDIBLE",
    "UNBELIEVABLE", "CRAZY", "BRUH", "BRO", "DUDE", "OMG", "SHEESH",
    "W CHAT", "HUGE", "MASSIVE", "EPIC", "CLUTCH", "CRACKED",
    "THAT WAS", "DID YOU SEE", "LOOK AT THAT", "ARE YOU KIDDING",
    "I CAN'T BELIEVE", "GOATED", "FIRE", "BUSSIN", "NO SHOT",
    "YOOO", "YOOOO", "AYOO", "HAHA", "LMAO", "DEAD",
]

FUNNY_INDICATORS = [
    "HAHA", "LMAO", "LMFAO", "DEAD", "DYING", "HILARIOUS",
    "FUNNY", "JOKE", "THAT'S SO", "I'M DONE", "BRUH MOMENT",
    "STOP", "PLEASE", "I CAN'T", "CRYING",
]

EDUCATIONAL_INDICATORS = [
    "HERE'S THE THING", "LET ME EXPLAIN", "SO BASICALLY",
    "THE KEY IS", "IMPORTANT", "REMEMBER", "TIP", "TRICK",
    "THE REASON", "WHAT YOU WANT TO DO", "PRO TIP", "LESSON",
    "STRATEGY", "HOW TO", "TUTORIAL",
]

EMOTIONAL_INDICATORS = [
    "LOVE", "THANK YOU", "GRATEFUL", "APPRECIATE", "BEAUTIFUL",
    "TOUCHING", "EMOTIONAL", "HEARTFELT", "MISS", "PROUD",
    "BLESSED", "COMMUNITY", "FAMILY", "TOGETHER",
]

# Content type style profiles
STYLE_PROFILES = {
    "gaming": {
        "energy_weight": 1.5,
        "funny_weight": 1.2,
        "educational_weight": 0.5,
        "emotional_weight": 0.3,
        "volume_weight": 1.5,
        "extra_keywords": ["CLUTCH", "GG", "PLAY", "KILL", "WIN", "LOSE", "RAGE"],
    },
    "podcast": {
        "energy_weight": 0.5,
        "funny_weight": 1.0,
        "educational_weight": 1.5,
        "emotional_weight": 1.3,
        "volume_weight": 0.3,
        "extra_keywords": ["INTERESTING", "POINT", "AGREE", "DISAGREE", "STORY"],
    },
    "sports": {
        "energy_weight": 1.5,
        "funny_weight": 0.8,
        "educational_weight": 0.3,
        "emotional_weight": 1.0,
        "volume_weight": 1.8,
        "extra_keywords": ["GOAL", "SCORE", "SHOT", "PLAY", "DEFENSE", "ATTACK"],
    },
    "general": {
        "energy_weight": 1.0,
        "funny_weight": 1.0,
        "educational_weight": 1.0,
        "emotional_weight": 1.0,
        "volume_weight": 1.0,
        "extra_keywords": [],
    },
}


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Failed to get video duration: {e}")
        return 0.0


def extract_audio(video_path: str, output_path: str) -> bool:
    """Extract audio from video as WAV for Whisper."""
    try:
        cmd = [
            FFMPEG, "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg audio extraction failed: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Audio extraction error: {e}")
        return False


def transcribe_audio(audio_path: str, model: str = "tiny") -> List[Dict]:
    """
    Transcribe audio using OpenAI Whisper.
    Returns list of segments with start, end, text.
    """
    try:
        import whisper
        logger.info(f"Loading Whisper model '{model}'...")
        whisper_model = whisper.load_model(model)
        logger.info("Transcribing audio...")
        result = whisper_model.transcribe(
            audio_path,
            language="en",
            verbose=False,
            word_timestamps=True,
        )
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
            })
        logger.info(f"Transcribed {len(segments)} segments")
        return segments
    except ImportError:
        logger.warning("Whisper not installed, trying whisper-cli fallback...")
        return _transcribe_with_cli(audio_path, model)
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return []


def _transcribe_with_cli(audio_path: str, model: str = "tiny") -> List[Dict]:
    """Fallback: use whisper CLI if python module not available."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                "whisper", audio_path,
                "--model", model,
                "--language", "en",
                "--output_format", "json",
                "--output_dir", tmpdir,
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            json_files = list(Path(tmpdir).glob("*.json"))
            if not json_files:
                return []
            with open(json_files[0]) as f:
                data = json.load(f)
            segments = []
            for seg in data.get("segments", []):
                segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip(),
                })
            return segments
    except Exception as e:
        logger.error(f"Whisper CLI fallback failed: {e}")
        return []


def analyze_audio_levels(video_path: str, chunk_seconds: int = 10) -> List[Dict]:
    """
    Analyze audio volume levels in chunks using FFmpeg.
    Returns list of { start, end, mean_volume, max_volume }.
    """
    duration = get_video_duration(video_path)
    if duration <= 0:
        return []

    chunks = []
    for start in range(0, int(duration), chunk_seconds):
        end = min(start + chunk_seconds, duration)
        try:
            cmd = [
                FFMPEG, "-y", "-i", video_path,
                "-ss", str(start), "-t", str(chunk_seconds),
                "-af", "volumedetect", "-f", "null", "/dev/null"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            stderr = result.stderr

            mean_vol = -30.0  # default
            max_vol = -30.0
            for line in stderr.split("\n"):
                if "mean_volume" in line:
                    match = re.search(r"mean_volume:\s*([-\d.]+)", line)
                    if match:
                        mean_vol = float(match.group(1))
                if "max_volume" in line:
                    match = re.search(r"max_volume:\s*([-\d.]+)", line)
                    if match:
                        max_vol = float(match.group(1))

            chunks.append({
                "start": start,
                "end": end,
                "mean_volume": mean_vol,
                "max_volume": max_vol,
            })
        except Exception as e:
            logger.warning(f"Volume analysis failed for chunk {start}-{end}: {e}")
            chunks.append({
                "start": start,
                "end": end,
                "mean_volume": -30.0,
                "max_volume": -30.0,
            })

    return chunks


def score_transcript_segments(
    segments: List[Dict],
    audio_levels: List[Dict],
    style: str = "general",
    clip_duration: int = 60,
) -> List[Dict]:
    """
    Score transcript segments for highlight potential.
    Combines text analysis with audio levels.
    Returns candidate moments with scores.
    """
    profile = STYLE_PROFILES.get(style, STYLE_PROFILES["general"])
    all_keywords = HIGH_ENERGY_WORDS + profile.get("extra_keywords", [])

    candidates = []

    # Group segments into clip-sized windows
    if not segments:
        return []

    total_duration = segments[-1]["end"] if segments else 0
    window_step = max(clip_duration // 2, 15)  # slide by half clip duration

    for window_start in range(0, int(total_duration), window_step):
        window_end = window_start + clip_duration

        # Get segments in this window
        window_segments = [
            s for s in segments
            if s["start"] >= window_start and s["end"] <= window_end + 5
        ]
        if not window_segments:
            continue

        window_text = " ".join(s["text"] for s in window_segments).upper()
        transcript_snippet = " ".join(s["text"] for s in window_segments[:3])
        if len(transcript_snippet) > 200:
            transcript_snippet = transcript_snippet[:200] + "..."

        # Score: energy keywords
        energy_score = 0
        for kw in all_keywords:
            count = window_text.count(kw)
            energy_score += count * 0.15

        # Score: funny indicators
        funny_score = 0
        for kw in FUNNY_INDICATORS:
            count = window_text.count(kw)
            funny_score += count * 0.2

        # Score: educational indicators
        edu_score = 0
        for kw in EDUCATIONAL_INDICATORS:
            count = window_text.count(kw)
            edu_score += count * 0.2

        # Score: emotional indicators
        emo_score = 0
        for kw in EMOTIONAL_INDICATORS:
            count = window_text.count(kw)
            emo_score += count * 0.2

        # Score: audio volume (loud moments)
        volume_score = 0
        relevant_chunks = [
            c for c in audio_levels
            if c["start"] < window_end and c["end"] > window_start
        ]
        if relevant_chunks:
            max_vol = max(c["max_volume"] for c in relevant_chunks)
            mean_vol = sum(c["mean_volume"] for c in relevant_chunks) / len(relevant_chunks)
            # Normalize: -10dB is very loud, -40dB is quiet
            volume_score = max(0, (max_vol + 40) / 30) * 0.3 + max(0, (mean_vol + 35) / 25) * 0.2

        # Score: "clip that" or similar streamer cues (bonus)
        cue_bonus = 0
        if any(cue in window_text for cue in ["CLIP THAT", "CLIP IT", "THAT'S A CLIP"]):
            cue_bonus = 0.3

        # Determine moment type
        type_scores = {
            "reaction": energy_score * profile["energy_weight"],
            "funny": funny_score * profile["funny_weight"],
            "highlight": (energy_score + volume_score) * profile["energy_weight"],
            "educational": edu_score * profile["educational_weight"],
            "emotional": emo_score * profile["emotional_weight"],
        }
        moment_type = max(type_scores, key=type_scores.get)

        # Combined score
        combined = (
            energy_score * profile["energy_weight"]
            + funny_score * profile["funny_weight"]
            + edu_score * profile["educational_weight"]
            + emo_score * profile["emotional_weight"]
            + volume_score * profile["volume_weight"]
            + cue_bonus
        )

        # Determine reason
        reasons = []
        if energy_score > 0.2:
            reasons.append("High energy moment")
        if volume_score > 0.3:
            reasons.append("loud reaction")
        if funny_score > 0.2:
            reasons.append("funny moment")
        if edu_score > 0.2:
            reasons.append("educational content")
        if emo_score > 0.2:
            reasons.append("emotional moment")
        if cue_bonus > 0:
            reasons.append("streamer clipped this")
        if not reasons:
            reasons.append("Interesting segment")

        if combined > 0.1:  # minimum threshold
            candidates.append({
                "start": float(window_start),
                "end": float(min(window_end, total_duration)),
                "duration": float(min(clip_duration, total_duration - window_start)),
                "score": min(combined, 1.0),
                "reason": " — ".join(reasons),
                "type": moment_type,
                "transcript_snippet": transcript_snippet,
            })

    return candidates


def extract_frame_at(video_path: str, timestamp: float, output_path: str) -> bool:
    """Extract a single frame from video at given timestamp."""
    try:
        cmd = [
            FFMPEG, "-y", "-ss", str(timestamp),
            "-i", video_path, "-frames:v", "1",
            "-q:v", "2", output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def score_with_vision(
    video_path: str,
    candidates: List[Dict],
    max_candidates: int = 20,
) -> List[Dict]:
    """
    Use Kimi Vision API to visually score candidate moments.
    Extracts a frame from each candidate and sends for analysis.
    """
    kimi_api_key = os.environ.get("KIMI_API_KEY")
    if not kimi_api_key:
        logger.warning("KIMI_API_KEY not set, skipping visual scoring")
        return candidates

    import base64

    scored = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, candidate in enumerate(candidates[:max_candidates]):
            mid_time = (candidate["start"] + candidate["end"]) / 2
            frame_path = os.path.join(tmpdir, f"frame_{i}.jpg")

            if not extract_frame_at(video_path, mid_time, frame_path):
                scored.append(candidate)
                continue

            try:
                with open(frame_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()

                import requests
                response = requests.post(
                    "https://api.moonshot.cn/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {kimi_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "moonshot-v1-vision",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{img_b64}"
                                        },
                                    },
                                    {
                                        "type": "text",
                                        "text": (
                                            "Rate this video frame for social media clip potential "
                                            "on a scale of 0-100. Consider: visual interest, action, "
                                            "emotion, composition. Reply with ONLY a number 0-100."
                                        ),
                                    },
                                ],
                            }
                        ],
                        "max_tokens": 10,
                    },
                    timeout=15,
                )

                if response.status_code == 200:
                    reply = response.json()["choices"][0]["message"]["content"].strip()
                    vision_score = int(re.search(r"\d+", reply).group()) / 100.0
                    # Blend: 60% text/audio score, 40% vision score
                    candidate["score"] = (candidate["score"] * 0.6) + (vision_score * 0.4)
                    candidate["vision_score"] = vision_score

            except Exception as e:
                logger.warning(f"Vision scoring failed for candidate {i}: {e}")

            scored.append(candidate)

    return scored


def find_highlight_moments(
    video_path: str,
    num_clips: int = 5,
    clip_duration: int = 60,
    style: str = "general",
    whisper_model: str = "tiny",
    progress_callback: Optional[Callable] = None,
) -> List[Dict]:
    """
    Analyze a long video and find the best moments to clip.

    Returns list of:
    {
        "start": 120.5,
        "end": 180.5,
        "duration": 60.0,
        "score": 0.92,
        "reason": "High energy moment — loud reaction, excited speech",
        "type": "reaction" | "funny" | "highlight" | "educational" | "emotional",
        "transcript_snippet": "OH MY GOD that was insane..."
    }
    """
    if progress_callback:
        progress_callback("Extracting audio...", 5)

    # Step 1: Extract audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
        audio_path = tmp_audio.name

    try:
        if not extract_audio(video_path, audio_path):
            logger.error("Failed to extract audio")
            return []

        if progress_callback:
            progress_callback("Transcribing video with Whisper...", 15)

        # Step 2: Transcribe
        segments = transcribe_audio(audio_path, model=whisper_model)
        if not segments:
            logger.warning("No transcription segments found")

        if progress_callback:
            progress_callback("Analyzing audio levels...", 40)

        # Step 3: Analyze audio levels
        audio_levels = analyze_audio_levels(video_path, chunk_seconds=10)

        if progress_callback:
            progress_callback("Scoring moments...", 55)

        # Step 4: Score transcript segments
        candidates = score_transcript_segments(
            segments, audio_levels, style=style, clip_duration=clip_duration
        )

        if progress_callback:
            progress_callback("Visual scoring with AI...", 70)

        # Step 5: Visual scoring (if Kimi available)
        candidates = score_with_vision(video_path, candidates, max_candidates=num_clips * 3)

        # Step 6: Remove overlapping, keep top N
        candidates.sort(key=lambda x: x["score"], reverse=True)
        selected = []
        for c in candidates:
            overlap = False
            for s in selected:
                if not (c["end"] <= s["start"] or c["start"] >= s["end"]):
                    overlap = True
                    break
            if not overlap:
                selected.append(c)
            if len(selected) >= num_clips:
                break

        # Re-sort by time
        selected.sort(key=lambda x: x["start"])

        # Normalize scores to 0-1 range
        if selected:
            max_score = max(c["score"] for c in selected)
            if max_score > 0:
                for c in selected:
                    c["score"] = round(c["score"] / max_score, 2)

        if progress_callback:
            progress_callback(f"Found {len(selected)} highlights", 85)

        return selected

    finally:
        try:
            os.unlink(audio_path)
        except Exception:
            pass


def extract_clip(
    video_path: str,
    start: float,
    end: float,
    output_path: str,
    format: str = "reels",
    burn_captions: bool = True,
    transcript_snippet: str = "",
    progress_callback: Optional[Callable] = None,
) -> str:
    """
    Extract a clip and format for social media.

    Formats:
    - reels: 9:16 (1080x1920) vertical for Instagram Reels / TikTok / Shorts
    - landscape: 16:9 (1920x1080) horizontal
    - square: 1:1 (1080x1080) square

    Features:
    - Smart crop centered on video
    - Optional burned-in captions
    - Proper encoding for social platforms
    """
    duration = end - start

    # Format specs
    format_specs = {
        "reels": {"width": 1080, "height": 1920, "aspect": "9:16"},
        "landscape": {"width": 1920, "height": 1080, "aspect": "16:9"},
        "square": {"width": 1080, "height": 1080, "aspect": "1:1"},
    }
    spec = format_specs.get(format, format_specs["reels"])

    # Get source dimensions
    try:
        probe_cmd = [
            FFPROBE, "-v", "quiet", "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0", video_path
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        src_w, src_h = map(int, probe_result.stdout.strip().split(","))
    except Exception:
        src_w, src_h = 1920, 1080

    # Build filter chain
    filters = []

    # Smart crop based on format
    target_w, target_h = spec["width"], spec["height"]
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if format == "reels":
        # Vertical: crop center portion of horizontal video
        if src_ratio > target_ratio:
            # Source is wider than target — crop width
            crop_w = int(src_h * target_ratio)
            crop_h = src_h
            crop_x = f"(iw-{crop_w})/2"
            crop_y = "0"
        else:
            crop_w = src_w
            crop_h = int(src_w / target_ratio)
            crop_x = "0"
            crop_y = f"(ih-{crop_h})/2"
        filters.append(f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}")
    elif format == "square":
        # Square: crop center
        if src_w > src_h:
            filters.append(f"crop={src_h}:{src_h}:(iw-{src_h})/2:0")
        else:
            filters.append(f"crop={src_w}:{src_w}:0:(ih-{src_w})/2")
    # landscape: usually no crop needed

    # Scale to target
    filters.append(f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease")
    filters.append(f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black")

    # Burn in captions if requested
    if burn_captions and transcript_snippet:
        # Escape special characters for FFmpeg drawtext
        safe_text = transcript_snippet.replace("'", "'\\''").replace(":", "\\:")
        safe_text = safe_text.replace("[", "\\[").replace("]", "\\]")
        if len(safe_text) > 100:
            safe_text = safe_text[:100] + "..."

        # Caption styling
        fontsize = 36 if format == "reels" else 28
        margin_bottom = 150 if format == "reels" else 60

        filters.append(
            f"drawtext=text='{safe_text}'"
            f":fontsize={fontsize}"
            f":fontcolor=white"
            f":borderw=3"
            f":bordercolor=black@0.8"
            f":x=(w-text_w)/2"
            f":y=h-{margin_bottom}"
            f":fontfile=/System/Library/Fonts/Helvetica.ttc"
        )

    filter_str = ",".join(filters) if filters else "null"

    # Build FFmpeg command
    cmd = [
        FFMPEG, "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-vf", filter_str,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]

    if progress_callback:
        progress_callback(f"Extracting clip ({start:.0f}s - {end:.0f}s)...", 0)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"Clip extraction failed: {result.stderr}")
            # Fallback: simpler extraction without filters
            cmd_simple = [
                FFMPEG, "-y",
                "-ss", str(start),
                "-i", video_path,
                "-t", str(duration),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                output_path,
            ]
            result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"Simple clip extraction also failed: {result.stderr}")
                return ""

        return output_path

    except subprocess.TimeoutExpired:
        logger.error("Clip extraction timed out")
        return ""
    except Exception as e:
        logger.error(f"Clip extraction error: {e}")
        return ""


def process_auto_clip_job(
    video_path: str,
    output_dir: str,
    num_clips: int = 5,
    clip_duration: int = 60,
    style: str = "general",
    format: str = "reels",
    progress_callback: Optional[Callable] = None,
) -> Dict:
    """
    Full auto-clip pipeline: analyze video, find highlights, extract clips.

    Returns:
    {
        "highlights": [...],
        "clips": [{"path": "...", "highlight": {...}}, ...],
        "total_clips": int,
    }
    """
    os.makedirs(output_dir, exist_ok=True)

    # Use tiny model for videos > 30min, medium for shorter
    duration = get_video_duration(video_path)
    whisper_model = "tiny" if duration > 1800 else "tiny"  # Start with tiny always for speed

    # Step 1: Find highlights
    highlights = find_highlight_moments(
        video_path=video_path,
        num_clips=num_clips,
        clip_duration=clip_duration,
        style=style,
        whisper_model=whisper_model,
        progress_callback=progress_callback,
    )

    if not highlights:
        logger.warning("No highlights found")
        return {"highlights": [], "clips": [], "total_clips": 0}

    if progress_callback:
        progress_callback(f"Extracting {len(highlights)} clips...", 85)

    # Step 2: Extract each clip
    clips = []
    for i, highlight in enumerate(highlights):
        clip_filename = f"clip_{i+1:02d}_{int(highlight['start'])}s.mp4"
        clip_path = os.path.join(output_dir, clip_filename)

        def clip_progress(msg, pct):
            overall = 85 + (i / len(highlights)) * 12
            if progress_callback:
                progress_callback(f"Clip {i+1}/{len(highlights)}: {msg}", int(overall))

        result_path = extract_clip(
            video_path=video_path,
            start=highlight["start"],
            end=highlight["end"],
            output_path=clip_path,
            format=format,
            burn_captions=True,
            transcript_snippet=highlight.get("transcript_snippet", ""),
            progress_callback=clip_progress,
        )

        if result_path:
            clips.append({
                "path": result_path,
                "filename": clip_filename,
                "highlight": highlight,
            })

    if progress_callback:
        progress_callback(f"Done! Generated {len(clips)} clips", 100)

    return {
        "highlights": highlights,
        "clips": clips,
        "total_clips": len(clips),
    }
