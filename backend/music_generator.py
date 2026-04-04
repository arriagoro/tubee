"""
music_generator.py — AI Music Generation for Tubee
Uses Google Lyria 3 Pro to generate background music for video edits.

Usage:
    from music_generator import generate_music
    path = generate_music("Upbeat electronic beat for a travel vlog", duration_seconds=30)
"""

import os
import time
import uuid
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


class MusicGenerationError(Exception):
    """Raised when music generation fails."""
    pass


class NoAPIKeyError(MusicGenerationError):
    """Raised when no API key is configured."""
    pass


def generate_music(
    prompt: str,
    duration_seconds: int = 30,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate background music using Google Lyria 3 Pro via Gemini API.

    Args:
        prompt: Description of the music to generate
            (e.g. "Upbeat electronic beat", "Chill lo-fi hip hop", "Epic cinematic score")
        duration_seconds: Target duration in seconds (default: 30)
        output_path: Optional path to save the audio file

    Returns:
        Path to the saved audio file (WAV)

    Raises:
        MusicGenerationError: If generation fails
        NoAPIKeyError: If GEMINI_API_KEY is not set
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise NoAPIKeyError(
            "GEMINI_API_KEY not set. Get your key at https://aistudio.google.com/"
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise MusicGenerationError(
            "google-genai SDK not installed. Run: pip install google-genai"
        )

    if not output_path:
        output_path = str(GENERATED_DIR / f"music_{uuid.uuid4().hex[:8]}.wav")

    client = genai.Client(api_key=api_key)

    logger.info(f"Lyria 3 Pro: generating music — {prompt[:80]}... ({duration_seconds}s)")

    # Try Lyria models in order
    models = [
        "lyria-3-pro-preview",
    ]

    last_error = None

    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=f"Generate a {duration_seconds}-second music track: {prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                ),
            )

            # Extract audio from response
            audio_bytes = None
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if part.inline_data.mime_type and 'audio' in part.inline_data.mime_type:
                            audio_bytes = part.inline_data.data
                            break

            if not audio_bytes:
                last_error = f"Lyria ({model_name}) returned no audio"
                logger.warning(last_error)
                continue

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"Lyria music saved: {output_path} (model: {model_name})")
            return output_path

        except (NoAPIKeyError, MusicGenerationError):
            raise
        except Exception as e:
            last_error = f"Lyria ({model_name}): {e}"
            logger.warning(last_error)
            continue

    raise MusicGenerationError(f"Music generation failed. Last error: {last_error}")
