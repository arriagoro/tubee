"""
image_generator.py — AI Image Generation & Editing for Tubee
Uses Google Imagen 4.0 for generation and Nano Banana Pro for editing.

Usage:
    from image_generator import generate_image_with_imagen, edit_image_with_nano_banana, generate_thumbnail
    path = generate_image_with_imagen("A vibrant Miami sunset over the ocean")
    edited = edit_image_with_nano_banana(path, "Add dramatic lens flare")
    thumb = generate_thumbnail("frame.png", "Bold YouTube thumbnail style")
"""

import os
import uuid
import logging
import base64
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


class ImageGenerationError(Exception):
    """Raised when image generation fails."""
    pass


class NoAPIKeyError(ImageGenerationError):
    """Raised when no API key is configured."""
    pass


def _get_gemini_client():
    """Get an authenticated google-genai client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise NoAPIKeyError(
            "GEMINI_API_KEY not set. Get your key at https://aistudio.google.com/"
        )
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except ImportError:
        raise ImageGenerationError(
            "google-genai SDK not installed. Run: pip install google-genai"
        )


def generate_image_with_imagen(
    prompt: str,
    output_path: Optional[str] = None,
    aspect_ratio: str = "9:16",
    number_of_images: int = 1,
) -> str:
    """
    Generate an image using Google Imagen 4.0.

    Args:
        prompt: Text description of the image to generate
        output_path: Optional path to save the image (default: auto-generated)
        aspect_ratio: Aspect ratio ("1:1", "9:16", "16:9", "4:3", "3:4")
        number_of_images: Number of images to generate (1-4)

    Returns:
        Path to the saved PNG file

    Raises:
        ImageGenerationError: If generation fails
    """
    client = _get_gemini_client()
    from google.genai import types

    if not output_path:
        output_path = str(GENERATED_DIR / f"imagen_{uuid.uuid4().hex[:8]}.png")

    logger.info(f"Imagen 4.0: generating image for prompt: {prompt[:80]}...")

    try:
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=number_of_images,
                aspect_ratio=aspect_ratio,
                output_mime_type="image/png",
            ),
        )

        if not response.generated_images:
            raise ImageGenerationError("Imagen 4.0 returned no images")

        # Save the first image
        image = response.generated_images[0]
        image_bytes = image.image.image_bytes

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        logger.info(f"Imagen 4.0 image saved: {output_path}")
        return output_path

    except (NoAPIKeyError, ImageGenerationError):
        raise
    except Exception as e:
        raise ImageGenerationError(f"Imagen 4.0 generation failed: {e}")


def edit_image_with_nano_banana(
    image_path: str,
    edit_prompt: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Edit an existing image using Nano Banana Pro (AI image editing via Gemini).

    Great for: thumbnail editing, color correction, object removal/addition,
    style transfer, text overlay guidance.

    Args:
        image_path: Path to the source image to edit
        edit_prompt: Description of the edits to apply
        output_path: Optional path to save the edited image

    Returns:
        Path to the saved edited PNG file

    Raises:
        ImageGenerationError: If editing fails
    """
    if not os.path.exists(image_path):
        raise ImageGenerationError(f"Source image not found: {image_path}")

    client = _get_gemini_client()
    from google.genai import types

    if not output_path:
        output_path = str(GENERATED_DIR / f"edited_{uuid.uuid4().hex[:8]}.png")

    logger.info(f"Nano Banana Pro: editing {image_path} — {edit_prompt[:80]}...")

    try:
        # Read source image
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # Determine MIME type
        ext = Path(image_path).suffix.lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".webp": "image/webp", ".gif": "image/gif"}
        mime_type = mime_map.get(ext, "image/png")

        # Use Gemini's image editing model
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[
                types.Content(
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                mime_type=mime_type,
                                data=image_bytes,
                            )
                        ),
                        types.Part(text=f"Edit this image: {edit_prompt}. Return only the edited image."),
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract image from response
        edited_bytes = None
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    if part.inline_data.mime_type and 'image' in part.inline_data.mime_type:
                        edited_bytes = part.inline_data.data
                        break

        if not edited_bytes:
            raise ImageGenerationError("Nano Banana Pro returned no edited image")

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(edited_bytes)

        logger.info(f"Nano Banana Pro edit saved: {output_path}")
        return output_path

    except (NoAPIKeyError, ImageGenerationError):
        raise
    except Exception as e:
        raise ImageGenerationError(f"Nano Banana Pro editing failed: {e}")


def generate_thumbnail(
    video_frame_path: str,
    style_prompt: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate a YouTube/Instagram thumbnail from a video frame.

    Uses Nano Banana Pro (via Gemini) to enhance and style a frame
    into an eye-catching thumbnail.

    Args:
        video_frame_path: Path to a video frame image (PNG/JPG)
        style_prompt: Optional style description (default: bold thumbnail style)
        output_path: Optional path to save the thumbnail

    Returns:
        Path to the saved thumbnail PNG

    Raises:
        ImageGenerationError: If thumbnail generation fails
    """
    if not os.path.exists(video_frame_path):
        raise ImageGenerationError(f"Video frame not found: {video_frame_path}")

    if not style_prompt:
        style_prompt = (
            "Transform this into an eye-catching YouTube/Instagram thumbnail. "
            "Make it bold, vibrant, high contrast. Add dramatic lighting. "
            "Make it look professional and click-worthy."
        )

    if not output_path:
        output_path = str(GENERATED_DIR / f"thumbnail_{uuid.uuid4().hex[:8]}.png")

    logger.info(f"Generating thumbnail from {video_frame_path}")

    return edit_image_with_nano_banana(
        image_path=video_frame_path,
        edit_prompt=style_prompt,
        output_path=output_path,
    )
