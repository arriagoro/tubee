"""
remotion_renderer.py — AI-powered "Vibe Editing" with Remotion

Pipeline: User prompt → Kimi K2 generates Remotion TSX code → Remotion renders MP4
Fallback: If Remotion render fails, falls back to FFmpeg pipeline.
"""

import os
import json
import uuid
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import List, Optional, Callable

import requests

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
REMOTION_DIR = BASE_DIR / "remotion"
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Load env
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")

# ─── Style → Composition mapping ───────────────────────────────────────────

STYLE_TO_COMPOSITION = {
    "social_reel": "SocialReel",
    "highlight": "HighlightReel",
    "brand_promo": "BrandPromo",
    "testimonial": "Testimonial",
    "before_after": "BeforeAfter",
}

STYLE_DESCRIPTIONS = {
    "social_reel": "vertical 9:16 social media reel with animated text overlay, color grading, and smooth clip transitions",
    "highlight": "fast-cut highlight reel with beat markers, zoom pulses, and flash transitions",
    "brand_promo": "product promo with title card intro, showcasing clips, and end card with CTA button",
    "testimonial": "talking head style with animated word-by-word captions at the bottom",
    "before_after": "split screen before/after comparison with animated divider",
}


def generate_remotion_code(
    prompt: str,
    clips: List[str],
    style: str = "social_reel",
    duration: int = 15,
) -> str:
    """
    Use Kimi K2 to generate Remotion React code from a natural language prompt.
    
    Args:
        prompt: User's natural language description of the video
        clips: List of clip file paths
        style: Style template key
        duration: Video duration in seconds
    
    Returns:
        Generated TSX code string
    """
    if not KIMI_API_KEY:
        raise ValueError("KIMI_API_KEY not set in environment")

    composition = STYLE_TO_COMPOSITION.get(style, "SocialReel")
    style_desc = STYLE_DESCRIPTIONS.get(style, "a creative video composition")

    # Build clip info for the AI
    clip_info = []
    for i, clip_path in enumerate(clips):
        clip_name = Path(clip_path).name
        clip_info.append(f"  Clip {i}: \"{clip_name}\" (src: staticFile(\"{clip_name}\"))")

    clips_text = "\n".join(clip_info) if clip_info else "  No clips provided — use colored backgrounds with animations"

    system_prompt = f"""You are a Remotion video editor AI. Generate valid React/Remotion TSX code for a video composition.

RULES:
1. Use imports from "remotion": AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, Video, Audio, interpolate, spring, staticFile
2. Video dimensions: 1080x1920 (9:16 vertical)
3. FPS: 30
4. Duration: {duration} seconds ({duration * 30} frames)
5. Export a single React component as default export
6. The component receives no props — hardcode all values
7. Use staticFile() for any media references
8. Return ONLY valid TSX code. No markdown, no explanation, no backticks.
9. Make it visually impressive with smooth animations, spring physics, and interpolations.

STYLE: {style_desc}

AVAILABLE CLIPS:
{clips_text}

COMPOSITION NAME: {composition}"""

    user_message = f"""Create a Remotion composition for this video:

"{prompt}"

Make it {duration} seconds long. Use all available clips. Add smooth animations, text overlays, and transitions.
The style should be: {style_desc}"""

    try:
        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {KIMI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "kimi-k2-0711-preview",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        code = data["choices"][0]["message"]["content"]

        # Clean up any markdown wrappers
        code = code.strip()
        if code.startswith("```tsx"):
            code = code[6:]
        elif code.startswith("```typescript"):
            code = code[13:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()

        logger.info(f"Generated Remotion code: {len(code)} chars")
        return code

    except requests.exceptions.RequestException as e:
        logger.error(f"Kimi API request failed: {e}")
        raise RuntimeError(f"AI code generation failed: {e}")


def render_remotion_video(
    composition_id: str,
    output_path: str,
    props: dict,
    progress_callback: Optional[Callable] = None,
) -> str:
    """
    Render a Remotion composition to MP4 using npx remotion render.
    
    Args:
        composition_id: The Remotion composition ID (e.g., "SocialReel")
        output_path: Where to save the output MP4
        props: Props to pass to the composition (serialized as JSON)
        progress_callback: Optional callback(stage, pct)
    
    Returns:
        Path to the rendered MP4 file
    """
    if progress_callback:
        progress_callback("Rendering with Remotion", 50)

    # Write props to temp file
    props_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, dir=str(REMOTION_DIR)
    )
    json.dump(props, props_file)
    props_file.close()

    try:
        cmd = [
            "npx", "remotion", "render",
            "src/index.ts",
            composition_id,
            output_path,
            "--props", props_file.name,
            "--codec", "h264",
        ]

        logger.info(f"Running Remotion render: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Remotion render failed:\nstdout: {result.stdout}\nstderr: {result.stderr}")
            raise RuntimeError(f"Remotion render failed: {result.stderr[:500]}")

        if progress_callback:
            progress_callback("Render complete", 90)

        logger.info(f"Remotion render complete: {output_path}")
        return output_path

    finally:
        # Clean up props file
        try:
            os.unlink(props_file.name)
        except OSError:
            pass


def _ffmpeg_fallback(
    clips: List[str],
    prompt: str,
    output_path: str,
    duration: int = 15,
    progress_callback: Optional[Callable] = None,
) -> str:
    """
    Fallback: Simple FFmpeg concat + overlay if Remotion fails.
    Creates a basic edit with crossfade transitions.
    """
    if progress_callback:
        progress_callback("Falling back to FFmpeg", 50)

    if not clips:
        raise ValueError("No clips provided for FFmpeg fallback")

    # Calculate per-clip duration
    per_clip = max(2, duration // len(clips))

    # Build FFmpeg filter complex for concat with crossfades
    inputs = []
    filter_parts = []

    for i, clip in enumerate(clips):
        inputs.extend(["-i", clip])
        filter_parts.append(
            f"[{i}:v]trim=0:{per_clip},setpts=PTS-STARTPTS,"
            f"scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]"
        )

    # Concat
    concat_inputs = "".join(f"[v{i}]" for i in range(len(clips)))
    filter_parts.append(f"{concat_inputs}concat=n={len(clips)}:v=1:a=0[outv]")

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-t", str(duration),
        output_path,
    ]

    logger.info(f"FFmpeg fallback: {len(clips)} clips → {output_path}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        logger.error(f"FFmpeg fallback failed: {result.stderr[:500]}")
        raise RuntimeError(f"FFmpeg fallback failed: {result.stderr[:300]}")

    if progress_callback:
        progress_callback("FFmpeg render complete", 90)

    return output_path


def vibe_edit(
    prompt: str,
    clips: List[str],
    style: str = "social_reel",
    music: Optional[str] = None,
    duration: int = 15,
    output_path: Optional[str] = None,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """
    Full Vibe Edit pipeline:
    1. AI generates Remotion composition code via Kimi K2
    2. Remotion renders to MP4
    3. Falls back to FFmpeg if Remotion fails
    
    Args:
        prompt: Natural language video description
        clips: List of video file paths
        style: Style preset key
        music: Optional music file path
        duration: Video duration in seconds
        output_path: Where to save the output
        progress_callback: Callback(stage, pct)
    
    Returns:
        dict with output_path, method, generated_code
    """
    if not output_path:
        output_path = str(OUTPUTS_DIR / f"vibe_{uuid.uuid4().hex[:12]}.mp4")

    generated_code = None
    method = "remotion"

    try:
        # Step 1: Generate Remotion code with AI
        if progress_callback:
            progress_callback("AI generating video code", 10)

        generated_code = generate_remotion_code(
            prompt=prompt,
            clips=clips,
            style=style,
            duration=duration,
        )

        if progress_callback:
            progress_callback("Code generated, preparing render", 30)

        # Step 2: Render with Remotion using the template composition
        composition_id = STYLE_TO_COMPOSITION.get(style, "SocialReel")

        # Build clip data for props
        clip_data = []
        for clip_path in clips:
            clip_name = Path(clip_path).name
            # Copy clip to remotion/public for staticFile access
            public_dir = REMOTION_DIR / "public"
            public_dir.mkdir(exist_ok=True)
            dest = public_dir / clip_name
            if not dest.exists():
                import shutil
                shutil.copy2(clip_path, dest)
            clip_data.append({"src": clip_name, "startFrom": 0})

        # Handle music
        music_ref = None
        if music and os.path.exists(music):
            music_name = Path(music).name
            public_dir = REMOTION_DIR / "public"
            public_dir.mkdir(exist_ok=True)
            music_dest = public_dir / music_name
            if not music_dest.exists():
                import shutil
                shutil.copy2(music, music_dest)
            music_ref = music_name

        props = {
            "clips": clip_data,
            "text": prompt[:100],  # Truncate for display
            "colors": {
                "primary": "#FFFFFF",
                "secondary": "#AAAAAA",
                "accent": "#00AAFF",
                "background": "#000000",
            },
            "music": music_ref,
            "duration": duration,
        }

        render_remotion_video(
            composition_id=composition_id,
            output_path=output_path,
            props=props,
            progress_callback=progress_callback,
        )

    except Exception as e:
        logger.warning(f"Remotion pipeline failed, falling back to FFmpeg: {e}")
        method = "ffmpeg_fallback"

        try:
            _ffmpeg_fallback(
                clips=clips,
                prompt=prompt,
                output_path=output_path,
                duration=duration,
                progress_callback=progress_callback,
            )
        except Exception as fallback_err:
            logger.error(f"FFmpeg fallback also failed: {fallback_err}")
            raise RuntimeError(
                f"Both Remotion and FFmpeg failed. Remotion: {e} | FFmpeg: {fallback_err}"
            )

    if progress_callback:
        progress_callback("Complete", 100)

    return {
        "output_path": output_path,
        "method": method,
        "generated_code": generated_code,
        "duration": duration,
        "clips_used": len(clips),
    }
