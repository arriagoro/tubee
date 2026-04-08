"""
voiceover.py — ElevenLabs voiceover module for Tubee
Generates speech from text using ElevenLabs API with macOS `say` fallback.
Can mix voiceover audio with existing video.
"""

import os
import subprocess
import tempfile
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional

import requests

logger = logging.getLogger(__name__)

FFMPEG = "/opt/homebrew/bin/ffmpeg"

# ElevenLabs API config
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel — professional, clear
DEFAULT_MODEL = "eleven_monolingual_v1"


def _get_api_key() -> Optional[str]:
    """Get ElevenLabs API key from environment."""
    return os.environ.get("ELEVENLABS_API_KEY")


# ---------------------------------------------------------------------------
# Voice listing
# ---------------------------------------------------------------------------

def list_voices() -> List[Dict]:
    """
    List available ElevenLabs voices.

    Returns:
        List of voice dicts with voice_id, name, category, description
    """
    api_key = _get_api_key()
    if not api_key:
        # Return a default list when no API key
        return [
            {
                "voice_id": "fallback_macos",
                "name": "macOS System Voice",
                "category": "system",
                "description": "Local text-to-speech (no API key required)",
            }
        ]

    try:
        response = requests.get(
            f"{ELEVENLABS_BASE_URL}/voices",
            headers={"xi-api-key": api_key},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        voices = []
        for v in data.get("voices", []):
            voices.append({
                "voice_id": v["voice_id"],
                "name": v["name"],
                "category": v.get("category", "unknown"),
                "description": v.get("labels", {}).get("description", ""),
                "preview_url": v.get("preview_url", ""),
            })

        logger.info(f"Listed {len(voices)} ElevenLabs voices")
        return voices

    except requests.RequestException as e:
        logger.error(f"Failed to list voices: {e}")
        return [{
            "voice_id": "fallback_macos",
            "name": "macOS System Voice (API error)",
            "category": "system",
            "description": "Fallback — ElevenLabs API unavailable",
        }]


# ---------------------------------------------------------------------------
# Speech generation
# ---------------------------------------------------------------------------

def generate_voiceover(
    text: str,
    voice_id: Optional[str] = None,
    output_path: Optional[str] = None,
    model_id: Optional[str] = None,
    stability: float = 0.5,
    similarity_boost: float = 0.75,
) -> Dict:
    """
    Generate speech from text using ElevenLabs API.
    Falls back to macOS `say` command if no API key is set.

    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID (default: Rachel)
        output_path: Where to save the audio file. Auto-generated if None.
        model_id: ElevenLabs model ID
        stability: Voice stability (0-1)
        similarity_boost: Similarity boost (0-1)

    Returns:
        Dict with output_path, duration, provider
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    # Generate output path if not provided
    if not output_path:
        output_path = tempfile.mktemp(suffix=".mp3", prefix="tubee_vo_")

    api_key = _get_api_key()

    if api_key:
        return _generate_elevenlabs(
            text=text,
            voice_id=voice_id or DEFAULT_VOICE_ID,
            output_path=output_path,
            api_key=api_key,
            model_id=model_id or DEFAULT_MODEL,
            stability=stability,
            similarity_boost=similarity_boost,
        )
    else:
        logger.warning("No ELEVENLABS_API_KEY set — falling back to macOS TTS")
        return _generate_macos_tts(text=text, output_path=output_path)


def _generate_elevenlabs(
    text: str,
    voice_id: str,
    output_path: str,
    api_key: str,
    model_id: str,
    stability: float,
    similarity_boost: float,
) -> Dict:
    """Generate speech via ElevenLabs API."""
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
        },
    }

    logger.info(f"Generating voiceover via ElevenLabs (voice: {voice_id})")

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=60, stream=True,
        )
        response.raise_for_status()

        # Stream response to file
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Get duration using ffprobe
        duration = _get_audio_duration(output_path)

        logger.info(f"ElevenLabs voiceover saved → {output_path} ({duration:.1f}s)")
        return {
            "output_path": output_path,
            "duration": duration,
            "provider": "elevenlabs",
            "voice_id": voice_id,
        }

    except requests.RequestException as e:
        logger.error(f"ElevenLabs API error: {e}")
        # Try fallback
        logger.info("Falling back to macOS TTS")
        return _generate_macos_tts(text=text, output_path=output_path)


def _generate_macos_tts(text: str, output_path: str) -> Dict:
    """Fallback: generate speech using macOS `say` command."""
    # macOS `say` outputs AIFF; we convert to MP3 with FFmpeg
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
        aiff_path = tmp.name

    try:
        # Generate AIFF with macOS say
        cmd_say = ["/usr/bin/say", "-o", aiff_path, text]
        result = subprocess.run(cmd_say, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"macOS say failed: {result.stderr}")

        # Convert to MP3
        if output_path.endswith(".mp3"):
            cmd_convert = [
                FFMPEG, "-y", "-i", aiff_path,
                "-codec:a", "libmp3lame", "-qscale:a", "2",
                output_path,
            ]
            result = subprocess.run(cmd_convert, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")
        else:
            # Just copy the AIFF
            import shutil
            shutil.copy2(aiff_path, output_path)

        duration = _get_audio_duration(output_path)

        logger.info(f"macOS TTS voiceover saved → {output_path} ({duration:.1f}s)")
        return {
            "output_path": output_path,
            "duration": duration,
            "provider": "macos_say",
            "voice_id": "system",
        }

    finally:
        if os.path.exists(aiff_path):
            os.unlink(aiff_path)


def _get_audio_duration(path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        cmd = [
            FFMPEG.replace("ffmpeg", "ffprobe"),
            "-v", "quiet", "-show_entries", "format=duration",
            "-of", "json", path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Mix voiceover with video
# ---------------------------------------------------------------------------

def add_voiceover_to_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    mix_volume: float = 0.8,
) -> Dict:
    """
    Mix voiceover audio with an existing video using FFmpeg.
    Original video audio is reduced, voiceover is overlaid.

    Args:
        video_path: Input video path
        audio_path: Voiceover audio path (MP3/WAV)
        output_path: Output video path
        mix_volume: Volume of original audio (0-1), voiceover is always 1.0

    Returns:
        Dict with output_path, duration
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    # Use FFmpeg amix filter to blend audio tracks
    # Original audio at mix_volume, voiceover at full volume
    cmd = [
        FFMPEG, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex",
        f"[0:a]volume={mix_volume}[orig];[1:a]volume=1.0[vo];[orig][vo]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]

    logger.info(f"Mixing voiceover into video (original vol: {mix_volume})")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        logger.error(f"FFmpeg mix failed: {result.stderr[:1000]}")
        raise RuntimeError(f"Voiceover mix failed: {result.stderr[:500]}")

    # Get output duration
    duration = _get_audio_duration(output_path)

    logger.info(f"Voiceover mixed → {output_path} ({duration:.1f}s)")
    return {
        "output_path": output_path,
        "duration": duration,
    }
