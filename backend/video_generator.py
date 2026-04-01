"""
video_generator.py — AI Video Generation for Tubee
Integrates Runway ML, Kling AI, and Luma Dream Machine with graceful fallbacks.

Usage:
    from video_generator import generate_video
    result = generate_video("A cinematic drone shot over Miami at sunset", duration=5)

All API keys are read from environment variables (loaded via python-dotenv).
"""

import os
import time
import uuid
import logging
import requests
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Output directory for generated videos
BASE_DIR = Path(__file__).parent.parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


class VideoGenerationError(Exception):
    """Raised when all video generation providers fail."""
    pass


class NoAPIKeyError(VideoGenerationError):
    """Raised when no API keys are configured."""
    pass


# ---------------------------------------------------------------------------
# Runway ML (Primary)
# ---------------------------------------------------------------------------

def generate_with_runway(
    prompt: str,
    duration: int = 4,
    ratio: str = "9:16",
    model: str = "gen4_turbo",
    progress_callback: Optional[Callable] = None,
) -> str:
    """
    Generate video using Runway ML Gen-4.

    Args:
        prompt: Text description of the video to generate
        duration: Duration in seconds (5 or 10)
        ratio: Aspect ratio string (e.g. "9:16", "16:9", "1:1")
        model: Model to use (gen4_turbo)
        progress_callback: Optional callback(stage, pct)

    Returns:
        Path to the downloaded video file

    Raises:
        VideoGenerationError: If generation fails
    """
    api_key = os.environ.get("RUNWAY_API_KEY")
    if not api_key:
        raise NoAPIKeyError(
            "RUNWAY_API_KEY not set. Get your key at https://dev.runwayml.com/"
        )

    base_url = "https://api.dev.runwayml.com/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Runway-Version": "2024-11-06",
    }

    # Map duration to Runway's expected format
    runway_duration = 5 if duration <= 5 else 10

    if progress_callback:
        progress_callback("Creating Runway generation task", 10)

    # Create generation task
    payload = {
        "promptText": prompt,
        "model": model,
        "duration": runway_duration,
        "ratio": ratio.replace(":", ":"),  # Runway uses "1280:720" format
    }

    resp = requests.post(f"{base_url}/image_to_video", json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise VideoGenerationError(f"Runway API error ({resp.status_code}): {resp.text[:300]}")

    task_id = resp.json().get("id")
    if not task_id:
        raise VideoGenerationError(f"Runway returned no task ID: {resp.json()}")

    logger.info(f"Runway task created: {task_id}")

    # Poll for completion
    max_wait = 600  # 10 minutes max
    poll_interval = 5
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        poll_resp = requests.get(f"{base_url}/tasks/{task_id}", headers=headers, timeout=15)
        if poll_resp.status_code != 200:
            logger.warning(f"Runway poll error: {poll_resp.status_code}")
            continue

        data = poll_resp.json()
        status = data.get("status", "")

        if progress_callback:
            pct = min(10 + int(elapsed / max_wait * 80), 85)
            progress_callback(f"Runway generating ({status})", pct)

        if status == "SUCCEEDED":
            output_url = data.get("output", [None])[0]
            if not output_url:
                raise VideoGenerationError("Runway completed but no output URL")

            # Download the video
            output_path = str(GENERATED_DIR / f"runway_{uuid.uuid4().hex[:8]}.mp4")
            if progress_callback:
                progress_callback("Downloading from Runway", 90)

            dl_resp = requests.get(output_url, timeout=120)
            with open(output_path, "wb") as f:
                f.write(dl_resp.content)

            logger.info(f"Runway video downloaded: {output_path}")
            return output_path

        elif status == "FAILED":
            error_msg = data.get("failure", "Unknown error")
            raise VideoGenerationError(f"Runway generation failed: {error_msg}")

    raise VideoGenerationError("Runway generation timed out after 10 minutes")


# ---------------------------------------------------------------------------
# Kling AI (Secondary)
# ---------------------------------------------------------------------------

def generate_with_kling(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    progress_callback: Optional[Callable] = None,
) -> str:
    """
    Generate video using Kling AI.

    Args:
        prompt: Text description of the video
        duration: Duration in seconds (5 or 10)
        aspect_ratio: Aspect ratio (e.g. "9:16", "16:9", "1:1")
        progress_callback: Optional callback(stage, pct)

    Returns:
        Path to the downloaded video file
    """
    api_key = os.environ.get("KLING_API_KEY")
    if not api_key:
        raise NoAPIKeyError(
            "KLING_API_KEY not set. Get your key at https://klingai.com/"
        )

    base_url = "https://api.klingai.com/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if progress_callback:
        progress_callback("Creating Kling generation task", 10)

    # Create generation task
    payload = {
        "prompt": prompt,
        "duration": str(duration),
        "aspect_ratio": aspect_ratio,
        "mode": "std",  # standard mode
    }

    resp = requests.post(
        f"{base_url}/videos/text2video", json=payload, headers=headers, timeout=30
    )
    if resp.status_code not in (200, 201):
        raise VideoGenerationError(f"Kling API error ({resp.status_code}): {resp.text[:300]}")

    result = resp.json()
    task_id = result.get("data", {}).get("task_id") or result.get("task_id")
    if not task_id:
        raise VideoGenerationError(f"Kling returned no task ID: {result}")

    logger.info(f"Kling task created: {task_id}")

    # Poll for completion
    max_wait = 600
    poll_interval = 8
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        poll_resp = requests.get(
            f"{base_url}/videos/text2video/{task_id}",
            headers=headers, timeout=15
        )
        if poll_resp.status_code != 200:
            continue

        data = poll_resp.json().get("data", poll_resp.json())
        status = data.get("task_status", data.get("status", ""))

        if progress_callback:
            pct = min(10 + int(elapsed / max_wait * 80), 85)
            progress_callback(f"Kling generating ({status})", pct)

        if status in ("succeed", "completed", "SUCCEEDED"):
            # Get the video URL from results
            videos = data.get("task_result", {}).get("videos", [])
            if not videos:
                videos = data.get("videos", [])

            output_url = videos[0].get("url") if videos else None
            if not output_url:
                raise VideoGenerationError("Kling completed but no output URL")

            output_path = str(GENERATED_DIR / f"kling_{uuid.uuid4().hex[:8]}.mp4")
            if progress_callback:
                progress_callback("Downloading from Kling", 90)

            dl_resp = requests.get(output_url, timeout=120)
            with open(output_path, "wb") as f:
                f.write(dl_resp.content)

            logger.info(f"Kling video downloaded: {output_path}")
            return output_path

        elif status in ("failed", "FAILED"):
            error_msg = data.get("task_status_msg", "Unknown error")
            raise VideoGenerationError(f"Kling generation failed: {error_msg}")

    raise VideoGenerationError("Kling generation timed out after 10 minutes")


# ---------------------------------------------------------------------------
# Luma Dream Machine (Tertiary)
# ---------------------------------------------------------------------------

def generate_with_luma(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    progress_callback: Optional[Callable] = None,
) -> str:
    """
    Generate video using Luma Dream Machine.

    Args:
        prompt: Text description of the video
        duration: Duration in seconds
        aspect_ratio: Aspect ratio (e.g. "9:16", "16:9", "1:1")
        progress_callback: Optional callback(stage, pct)

    Returns:
        Path to the downloaded video file
    """
    api_key = os.environ.get("LUMA_API_KEY")
    if not api_key:
        raise NoAPIKeyError(
            "LUMA_API_KEY not set. Get your key at https://lumalabs.ai/"
        )

    base_url = "https://api.lumalabs.ai/dream-machine/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if progress_callback:
        progress_callback("Creating Luma generation task", 10)

    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
    }

    resp = requests.post(
        f"{base_url}/generations", json=payload, headers=headers, timeout=30
    )
    if resp.status_code not in (200, 201):
        raise VideoGenerationError(f"Luma API error ({resp.status_code}): {resp.text[:300]}")

    result = resp.json()
    gen_id = result.get("id")
    if not gen_id:
        raise VideoGenerationError(f"Luma returned no generation ID: {result}")

    logger.info(f"Luma generation created: {gen_id}")

    # Poll for completion
    max_wait = 600
    poll_interval = 6
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        poll_resp = requests.get(
            f"{base_url}/generations/{gen_id}",
            headers=headers, timeout=15
        )
        if poll_resp.status_code != 200:
            continue

        data = poll_resp.json()
        status = data.get("state", data.get("status", ""))

        if progress_callback:
            pct = min(10 + int(elapsed / max_wait * 80), 85)
            progress_callback(f"Luma generating ({status})", pct)

        if status in ("completed", "succeeded"):
            output_url = (
                data.get("assets", {}).get("video")
                or data.get("video", {}).get("url")
            )
            if not output_url:
                raise VideoGenerationError("Luma completed but no output URL")

            output_path = str(GENERATED_DIR / f"luma_{uuid.uuid4().hex[:8]}.mp4")
            if progress_callback:
                progress_callback("Downloading from Luma", 90)

            dl_resp = requests.get(output_url, timeout=120)
            with open(output_path, "wb") as f:
                f.write(dl_resp.content)

            logger.info(f"Luma video downloaded: {output_path}")
            return output_path

        elif status in ("failed",):
            error_msg = data.get("failure_reason", "Unknown error")
            raise VideoGenerationError(f"Luma generation failed: {error_msg}")

    raise VideoGenerationError("Luma generation timed out after 10 minutes")


# ---------------------------------------------------------------------------
# Main generate_video function — tries providers in order
# ---------------------------------------------------------------------------

def generate_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    style: str = "cinematic",
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Generate a video from a text prompt. Tries providers in order:
    Runway ML → Kling AI → Luma Dream Machine

    Args:
        prompt: Text description of the video to generate
        duration: Duration in seconds (4, 8, or 16)
        aspect_ratio: Aspect ratio ("9:16", "16:9", "1:1")
        style: Style modifier (cinematic, action, vlog, music_video, documentary)
        progress_callback: Optional callback(stage: str, pct: int)

    Returns:
        dict with keys: output_path, provider, prompt

    Raises:
        VideoGenerationError: If all providers fail
        NoAPIKeyError: If no API keys are configured
    """
    # Enhance prompt with style
    style_prefixes = {
        "cinematic": "Cinematic, film-quality, shallow depth of field, dramatic lighting.",
        "action": "Fast-paced, dynamic camera movement, high energy, action-packed.",
        "vlog": "Natural, handheld feel, warm colors, authentic and personal.",
        "music_video": "Stylized, rhythmic movement, vivid colors, music video aesthetic.",
        "documentary": "Documentary style, natural lighting, observational, authentic.",
    }
    style_key = style.lower().replace(" ", "_")
    prefix = style_prefixes.get(style_key, "")
    enhanced_prompt = f"{prefix} {prompt}".strip() if prefix else prompt

    # Track which providers we tried and their errors
    providers = [
        ("Runway ML", lambda: generate_with_runway(
            enhanced_prompt, duration=duration, ratio=aspect_ratio,
            progress_callback=progress_callback,
        )),
        ("Kling AI", lambda: generate_with_kling(
            enhanced_prompt, duration=duration, aspect_ratio=aspect_ratio,
            progress_callback=progress_callback,
        )),
        ("Luma Dream Machine", lambda: generate_with_luma(
            enhanced_prompt, duration=duration, aspect_ratio=aspect_ratio,
            progress_callback=progress_callback,
        )),
    ]

    errors = []
    no_key_errors = []

    for name, gen_fn in providers:
        try:
            if progress_callback:
                progress_callback(f"Trying {name}…", 5)

            output_path = gen_fn()

            if progress_callback:
                progress_callback("Generation complete", 100)

            return {
                "output_path": output_path,
                "provider": name,
                "prompt": enhanced_prompt,
            }

        except NoAPIKeyError as e:
            no_key_errors.append((name, str(e)))
            logger.info(f"{name}: No API key — skipping")
            continue

        except VideoGenerationError as e:
            errors.append((name, str(e)))
            logger.warning(f"{name} failed: {e}")
            continue

        except Exception as e:
            errors.append((name, str(e)))
            logger.error(f"{name} unexpected error: {e}", exc_info=True)
            continue

    # All providers failed — build a helpful error message
    if len(no_key_errors) == len(providers):
        # No API keys configured at all
        key_info = "\n".join([
            "No video generation API keys configured. Set at least one:",
            "",
            "  RUNWAY_API_KEY  → https://dev.runwayml.com/",
            "  KLING_API_KEY   → https://klingai.com/",
            "  LUMA_API_KEY    → https://lumalabs.ai/",
            "",
            "Add the key to your .env file and restart the server.",
        ])
        raise NoAPIKeyError(key_info)

    error_details = "; ".join([f"{name}: {err}" for name, err in errors + no_key_errors])
    raise VideoGenerationError(f"All video generation providers failed. {error_details}")
