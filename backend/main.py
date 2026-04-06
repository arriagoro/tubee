"""
main.py — FastAPI server for Tubee
Handles file uploads, job submission, status polling, and download.

Endpoints:
  POST /upload                — Upload footage + optional music
  POST /edit                  — Submit prompt, trigger processing
  GET  /status/{job_id}       — Check job status
  GET  /download/{job_id}     — Download finished video
  GET  /jobs                  — List all jobs
  DELETE /jobs/{job_id}       — Delete a job and its files

Run with:
  uvicorn main:app --reload --port 8000
"""

import os
import uuid
import json
import shutil
import logging
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Directory setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
JOBS_DIR = BASE_DIR / "jobs"
GENERATED_DIR = BASE_DIR / "generated"

for d in [UPLOADS_DIR, OUTPUTS_DIR, JOBS_DIR, GENERATED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Job state management
# In production, use Redis or a database. For MVP, we use in-memory + JSON files.
# ---------------------------------------------------------------------------
jobs: Dict[str, Dict[str, Any]] = {}


def save_job(job_id: str) -> None:
    """Persist job state to disk."""
    job_file = JOBS_DIR / f"{job_id}.json"
    with open(job_file, "w") as f:
        json.dump(jobs[job_id], f, indent=2)


def load_jobs() -> None:
    """Load all jobs from disk on startup."""
    for job_file in JOBS_DIR.glob("*.json"):
        try:
            with open(job_file) as f:
                job = json.load(f)
                jobs[job["job_id"]] = job
        except Exception as e:
            logger.warning(f"Failed to load job {job_file}: {e}")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class EditRequest(BaseModel):
    job_id: str
    prompt: str
    target_duration: Optional[float] = None
    style: Optional[str] = None          # Style preset: cole_bennett, cinematic, vintage, clean, neon
    aspect_ratio: Optional[str] = None   # Aspect ratio: 9:16, 1:1, 4:5, 16:9, 4:3
    transition_style: Optional[str] = None  # Transition: hard_cut, whip_pan, circle_reveal, swipe, zoom_blur, glitch, mixed, fade
    export_quality: str = "1080p"        # Export quality: "1080p", "2k", "4k"
    output_format: str = "reels"         # Output format: "reels", "landscape", "square"
    frame_analysis: bool = True          # Extract frames for Kimi K2 vision analysis


class GenerateRequest(BaseModel):
    prompt: str
    duration: Optional[int] = 5           # 4, 8, or 16 seconds
    style: Optional[str] = "cinematic"    # cinematic, action, vlog, music_video, documentary
    aspect_ratio: Optional[str] = "9:16"  # 9:16, 16:9, 1:1


class CaptionRequest(BaseModel):
    job_id: str
    style: Optional[str] = "temitayo"     # temitayo, standard, minimal, bold
    word_by_word: Optional[bool] = False


class VoiceoverRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    job_id: Optional[str] = None          # Attach to existing video job


class VibeEditRequest(BaseModel):
    job_id: str
    prompt: str
    style: Optional[str] = "social_reel"   # social_reel, highlight, brand_promo, testimonial, before_after
    duration: Optional[int] = 15


class GenerateImageRequest(BaseModel):
    prompt: str
    style: Optional[str] = None
    aspect_ratio: Optional[str] = "9:16"


class EditImageRequest(BaseModel):
    job_id: Optional[str] = None          # Use image from a completed job
    image_url: Optional[str] = None       # Or provide a direct URL/path
    edit_prompt: str


class GenerateThumbnailRequest(BaseModel):
    job_id: str
    style_prompt: Optional[str] = None


class GenerateMusicRequest(BaseModel):
    prompt: str
    duration: Optional[int] = 30          # Duration in seconds


class UpscaleRequest(BaseModel):
    job_id: str
    scale: Optional[int] = 4              # 2 or 4


class JobStatus(BaseModel):
    job_id: str
    status: str         # "pending" | "uploading" | "processing" | "done" | "error"
    progress: int       # 0-100
    stage: str
    created_at: str
    updated_at: str
    prompt: Optional[str] = None
    video_files: List[str] = []
    music_file: Optional[str] = None
    output_path: Optional[str] = None
    duration: Optional[float] = None
    clips_used: Optional[int] = None
    edit_notes: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Tubee API",
    description="AI-powered video editor backend",
    version="1.0.0",
)

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Load existing jobs on startup."""
    load_jobs()
    logger.info(f"Tubee API started — loaded {len(jobs)} existing jobs")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"name": "Tubee API", "version": "1.0.0", "status": "running"}


@app.post("/upload", summary="Upload footage and optional music")
async def upload_files(
    files: List[UploadFile] = File(..., description="Video files + optional music file"),
) -> Dict[str, Any]:
    """
    Upload one or more video files and optionally a music file.
    Returns a job_id to use with POST /edit.

    The server automatically detects which files are video vs audio based on extension.
    """
    job_id = str(uuid.uuid4())
    job_upload_dir = UPLOADS_DIR / job_id
    job_upload_dir.mkdir(parents=True, exist_ok=True)

    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv", ".mxf"}
    audio_extensions = {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"}

    uploaded_videos = []
    uploaded_music = None

    for file in files:
        if not file.filename:
            continue

        ext = Path(file.filename).suffix.lower()
        safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
        dest = job_upload_dir / safe_name

        # Stream file to disk
        with open(dest, "wb") as f:
            content = await file.read()
            f.write(content)

        file_size_mb = dest.stat().st_size / (1024 * 1024)
        logger.info(f"[{job_id}] Uploaded: {safe_name} ({file_size_mb:.1f} MB)")

        if ext in video_extensions:
            uploaded_videos.append(str(dest))
        elif ext in audio_extensions:
            if uploaded_music:
                logger.warning(f"[{job_id}] Multiple music files uploaded, using first: {uploaded_music}")
            else:
                uploaded_music = str(dest)
        else:
            logger.warning(f"[{job_id}] Unknown file type: {safe_name} — treating as video")
            uploaded_videos.append(str(dest))

    if not uploaded_videos:
        shutil.rmtree(job_upload_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="No video files uploaded")

    # Create job record
    now = datetime.utcnow().isoformat()
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "stage": "Uploaded, waiting for prompt",
        "created_at": now,
        "updated_at": now,
        "prompt": None,
        "video_files": uploaded_videos,
        "music_file": uploaded_music,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    return {
        "job_id": job_id,
        "video_files": [Path(v).name for v in uploaded_videos],
        "music_file": Path(uploaded_music).name if uploaded_music else None,
        "message": f"Upload successful. Use POST /edit with job_id='{job_id}' to start processing.",
    }


@app.post("/edit", summary="Submit prompt and start video processing")
async def start_edit(
    request: EditRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Submit an edit prompt for a previously uploaded job.
    Processing runs asynchronously — poll GET /status/{job_id} for progress.
    """
    job_id = request.job_id
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = jobs[job_id]

    if job["status"] == "processing":
        raise HTTPException(status_code=409, detail="Job is already processing")

    if job["status"] == "done":
        raise HTTPException(status_code=409, detail="Job already completed. Upload new files for a new edit.")

    # Update job with prompt
    job["prompt"] = request.prompt
    job["status"] = "processing"
    job["stage"] = "Starting pipeline"
    job["progress"] = 0
    job["error"] = None
    job["updated_at"] = datetime.utcnow().isoformat()
    save_job(job_id)

    # Map frontend style names to backend preset names
    style_map = {
        "cinematic": "cinematic", "Cinematic": "cinematic",
        "music video": "cole_bennett", "Music Video": "cole_bennett",
        "retro": "vintage", "Retro": "vintage",
        "minimal": "clean", "Minimal": "clean",
        "hype": "neon", "Hype": "neon",
        "neon": "neon", "Neon": "neon",
    }
    backend_style = style_map.get(request.style) if request.style else None

    # Map frontend transition names to backend transition types
    transition_map = {
        "none": "hard_cut", "None": "hard_cut", "hard_cut": "hard_cut",
        "whip_pan": "whip_pan", "Whip Pan": "whip_pan",
        "circle_reveal": "circle_reveal", "Circle": "circle_reveal",
        "swipe": "swipe", "Swipe": "swipe",
        "zoom_blur": "zoom_blur", "Zoom Blur": "zoom_blur",
        "glitch": "glitch", "Glitch": "glitch",
        "mixed": "mixed", "Mixed": "mixed",
        "fade": "fade", "Fade": "fade",
    }
    backend_transition = transition_map.get(request.transition_style) if request.transition_style else None

    # Run processing in background thread (CPU-bound work)
    background_tasks.add_task(
        _run_processing_task,
        job_id=job_id,
        target_duration=request.target_duration,
        style_preset=backend_style,
        aspect_ratio=request.aspect_ratio,
        transition_style=backend_transition,
        export_quality=request.export_quality,
        output_format=request.output_format,
        frame_analysis=request.frame_analysis,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Edit started. Poll GET /status/{job_id} for progress.",
    }


@app.get("/status/{job_id}", response_model=JobStatus, summary="Check job status")
async def get_status(job_id: str) -> JobStatus:
    """
    Get the current status and progress of a job.

    Status values:
    - pending: Uploaded, waiting for prompt
    - processing: Currently running the pipeline
    - done: Finished, ready to download
    - error: Failed — check 'error' field for details
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobStatus(**jobs[job_id])


@app.get("/download/{job_id}", summary="Download finished video")
async def download_video(job_id: str) -> FileResponse:
    """
    Download the finished video for a completed job.
    Returns the MP4 file directly.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = jobs[job_id]

    if job["status"] != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not done yet (status: {job['status']})"
        )

    output_path = job.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")

    filename = f"tubee_{job_id[:8]}.mp4"
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=filename,
    )


@app.get("/jobs", summary="List all jobs")
async def list_jobs() -> Dict[str, Any]:
    """List all jobs with their current status."""
    return {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": j["job_id"],
                "status": j["status"],
                "progress": j["progress"],
                "stage": j["stage"],
                "created_at": j["created_at"],
                "prompt": j.get("prompt"),
            }
            for j in sorted(jobs.values(), key=lambda x: x["created_at"], reverse=True)
        ],
    }


@app.delete("/jobs/{job_id}", summary="Delete a job")
async def delete_job(job_id: str) -> Dict[str, Any]:
    """Delete a job and all its associated files."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = jobs[job_id]

    if job["status"] == "processing":
        raise HTTPException(status_code=409, detail="Cannot delete a job that is currently processing")

    # Remove upload files
    upload_dir = UPLOADS_DIR / job_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)

    # Remove output file
    output_path = job.get("output_path")
    if output_path and os.path.exists(output_path):
        os.unlink(output_path)

    # Remove job record from disk
    job_file = JOBS_DIR / f"{job_id}.json"
    if job_file.exists():
        job_file.unlink()

    del jobs[job_id]

    return {"message": f"Job {job_id} deleted"}


# ---------------------------------------------------------------------------
# Generate endpoint — AI video generation
# ---------------------------------------------------------------------------

@app.post("/generate", summary="Generate a video from a text prompt")
async def generate_video_endpoint(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Generate a video using AI (Runway ML, Kling AI, or Luma Dream Machine).
    Processing runs asynchronously — poll GET /status/{job_id} for progress.
    """
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting AI video generation",
        "created_at": now,
        "updated_at": now,
        "prompt": request.prompt,
        "video_files": [],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_generate_task,
        job_id=job_id,
        prompt=request.prompt,
        duration=request.duration or 5,
        style=request.style or "cinematic",
        aspect_ratio=request.aspect_ratio or "9:16",
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Generation started. Poll GET /status/{job_id} for progress.",
    }


# ---------------------------------------------------------------------------
# Upscale endpoint — AI/FFmpeg video upscaling
# ---------------------------------------------------------------------------

@app.post("/upscale", summary="Upscale a video")
async def upscale_video_endpoint(
    request: UpscaleRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Upscale a completed video using Real-ESRGAN (AI) or FFmpeg lanczos fallback.
    Provide a job_id of a completed edit or generation job.
    Works locally — no API key required.
    """
    source_job_id = request.job_id
    if source_job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Source job {source_job_id} not found")

    source_job = jobs[source_job_id]
    if source_job["status"] != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Source job is not complete (status: {source_job['status']})"
        )

    source_path = source_job.get("output_path")
    if not source_path or not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Source video file not found")

    scale = request.scale or 4
    if scale not in (2, 4):
        raise HTTPException(status_code=400, detail="Scale must be 2 or 4")

    # Create a new job for the upscale
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": f"Starting {scale}x upscale",
        "created_at": now,
        "updated_at": now,
        "prompt": f"Upscale {scale}x from job {source_job_id[:8]}",
        "video_files": [],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_upscale_task,
        job_id=job_id,
        source_path=source_path,
        scale=scale,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": f"Upscale ({scale}x) started. Poll GET /status/{job_id} for progress.",
    }


# ---------------------------------------------------------------------------
# Vibe Edit endpoint — AI + Remotion
# ---------------------------------------------------------------------------

@app.post("/vibe-edit", summary="AI Vibe Edit — describe your video, AI builds it")
async def vibe_edit_endpoint(
    request: VibeEditRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    AI-powered 'Vibe Edit': describe what you want in natural language,
    AI generates Remotion code, renders it to a video.
    Requires a job_id with previously uploaded clips.
    Falls back to FFmpeg if Remotion render fails.
    """
    source_job_id = request.job_id
    if source_job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {source_job_id} not found")

    source_job = jobs[source_job_id]
    clips = source_job.get("video_files", [])
    if not clips:
        raise HTTPException(status_code=400, detail="No video files found for this job. Upload clips first.")

    style = request.style or "social_reel"
    valid_styles = ["social_reel", "highlight", "brand_promo", "testimonial", "before_after"]
    if style not in valid_styles:
        raise HTTPException(status_code=400, detail=f"Invalid style. Choose from: {valid_styles}")

    # Create a new job for the vibe edit output
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting Vibe Edit",
        "created_at": now,
        "updated_at": now,
        "prompt": request.prompt,
        "video_files": clips,
        "music_file": source_job.get("music_file"),
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
        "vibe_code": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_vibe_edit_task,
        job_id=job_id,
        prompt=request.prompt,
        clips=clips,
        style=style,
        music=source_job.get("music_file"),
        duration=request.duration or 15,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Vibe Edit started. Poll GET /status/{job_id} for progress.",
    }


@app.get("/vibe-code/{job_id}", summary="Get generated Remotion code for a vibe edit")
async def get_vibe_code(job_id: str) -> Dict[str, Any]:
    """Return the AI-generated Remotion code for a vibe edit job."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = jobs[job_id]
    return {
        "job_id": job_id,
        "code": job.get("vibe_code"),
        "status": job["status"],
    }


# ---------------------------------------------------------------------------
# Background processing
# ---------------------------------------------------------------------------

def _run_processing_task(job_id: str, target_duration: Optional[float] = None, style_preset: Optional[str] = None, aspect_ratio: Optional[str] = None, transition_style: Optional[str] = None, export_quality: Optional[str] = None, output_format: Optional[str] = None, frame_analysis: bool = True) -> None:
    """
    Background thread that runs the full processing pipeline.
    Updates job status as it progresses.
    """
    import sys
    import os
    # Ensure backend module is importable
    sys.path.insert(0, str(Path(__file__).parent))

    from processor import process_job

    job = jobs[job_id]
    output_path = str(OUTPUTS_DIR / f"{job_id}.mp4")

    def progress_callback(stage: str, pct: int):
        jobs[job_id]["stage"] = stage
        jobs[job_id]["progress"] = pct
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

    try:
        result = process_job(
            video_files=job["video_files"],
            music_file=job.get("music_file"),
            user_prompt=job["prompt"],
            output_path=output_path,
            job_id=job_id,
            progress_callback=progress_callback,
            style_preset=style_preset,
            aspect_ratio=aspect_ratio,
            transition_style=transition_style,
            export_quality=export_quality,
            output_format=output_format,
            frame_analysis=frame_analysis,
        )

        # Success
        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": result["output_path"],
            "duration": result["duration"],
            "clips_used": result["clips_used"],
            "edit_notes": result["edit_notes"],
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Processing complete: {result['duration']:.1f}s video")

    except Exception as e:
        logger.error(f"[{job_id}] Processing failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


def _run_generate_task(job_id: str, prompt: str, duration: int, style: str, aspect_ratio: str) -> None:
    """Background task: AI video generation."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from video_generator import generate_video, VideoGenerationError, NoAPIKeyError

    def progress_callback(stage: str, pct: int):
        jobs[job_id]["stage"] = stage
        jobs[job_id]["progress"] = pct
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

    try:
        result = generate_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            style=style,
            progress_callback=progress_callback,
        )

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": result["output_path"],
            "edit_notes": f"Generated with {result['provider']}",
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Video generation complete via {result['provider']}")

    except Exception as e:
        logger.error(f"[{job_id}] Generation failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


def _run_upscale_task(job_id: str, source_path: str, scale: int) -> None:
    """Background task: video upscaling."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from upscaler import upscale_video

    output_path = str(OUTPUTS_DIR / f"{job_id}_upscaled.mp4")

    def progress_callback(stage: str, pct: int):
        jobs[job_id]["stage"] = stage
        jobs[job_id]["progress"] = pct
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

    try:
        result = upscale_video(
            input_path=source_path,
            output_path=output_path,
            scale=scale,
            progress_callback=progress_callback,
        )

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": result["output_path"],
            "edit_notes": f"Upscaled {result['original_resolution']} → {result['upscaled_resolution']} ({result['method']})",
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Upscale complete: {result['original_resolution']} → {result['upscaled_resolution']}")

    except Exception as e:
        logger.error(f"[{job_id}] Upscale failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


# ---------------------------------------------------------------------------
# Captions endpoint
# ---------------------------------------------------------------------------

@app.post("/captions", summary="Add captions to a video")
async def add_captions_endpoint(
    request: CaptionRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Add auto-generated captions to a completed video job.
    Uses Whisper for transcription and FFmpeg for burning captions.
    """
    source_job_id = request.job_id
    if source_job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Source job {source_job_id} not found")

    source_job = jobs[source_job_id]
    if source_job["status"] != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Source job is not complete (status: {source_job['status']})"
        )

    source_path = source_job.get("output_path")
    if not source_path or not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Source video file not found")

    style = request.style or "temitayo"
    if style not in ("temitayo", "standard", "minimal", "bold"):
        raise HTTPException(status_code=400, detail=f"Invalid style: {style}")

    # Create new job for captioned output
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting caption generation",
        "created_at": now,
        "updated_at": now,
        "prompt": f"Captions ({style}) from job {source_job_id[:8]}",
        "video_files": [],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_captions_task,
        job_id=job_id,
        source_path=source_path,
        style=style,
        word_by_word=request.word_by_word or False,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": f"Caption generation started ({style}). Poll GET /status/{job_id} for progress.",
    }


@app.post("/captions/upload", summary="Upload a video and add captions")
async def upload_and_caption(
    file: UploadFile = File(...),
    style: str = Form("temitayo"),
    word_by_word: bool = Form(False),
    background_tasks: BackgroundTasks = None,
) -> Dict[str, Any]:
    """Upload a video file directly and add captions to it."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    job_id = str(uuid.uuid4())
    job_upload_dir = UPLOADS_DIR / job_id
    job_upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
    dest = job_upload_dir / safe_name

    with open(dest, "wb") as f:
        content = await file.read()
        f.write(content)

    now = datetime.utcnow().isoformat()
    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting caption generation",
        "created_at": now,
        "updated_at": now,
        "prompt": f"Captions ({style}) — uploaded video",
        "video_files": [str(dest)],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_captions_task,
        job_id=job_id,
        source_path=str(dest),
        style=style,
        word_by_word=word_by_word,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": f"Caption generation started. Poll GET /status/{job_id} for progress.",
    }


# ---------------------------------------------------------------------------
# Voiceover endpoint
# ---------------------------------------------------------------------------

@app.post("/voiceover", summary="Generate voiceover from text")
async def generate_voiceover_endpoint(
    request: VoiceoverRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Generate voiceover audio from text using ElevenLabs.
    Optionally attach to an existing video job.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting voiceover generation",
        "created_at": now,
        "updated_at": now,
        "prompt": f"Voiceover: {request.text[:80]}...",
        "video_files": [],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    attach_video_path = None
    if request.job_id and request.job_id in jobs:
        source_job = jobs[request.job_id]
        if source_job.get("status") == "done" and source_job.get("output_path"):
            attach_video_path = source_job["output_path"]

    background_tasks.add_task(
        _run_voiceover_task,
        job_id=job_id,
        text=request.text,
        voice_id=request.voice_id,
        attach_video_path=attach_video_path,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Voiceover generation started. Poll GET /status/{job_id} for progress.",
    }


@app.get("/voices", summary="List available voices")
async def list_voices_endpoint() -> Dict[str, Any]:
    """List available ElevenLabs voices."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from voiceover import list_voices
    voices = list_voices()
    return {"voices": voices}


# ---------------------------------------------------------------------------
# Background tasks: captions and voiceover
# ---------------------------------------------------------------------------

def _run_captions_task(job_id: str, source_path: str, style: str, word_by_word: bool) -> None:
    """Background task: auto-caption a video."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from captions import add_captions_to_video

    output_path = str(OUTPUTS_DIR / f"{job_id}_captioned.mp4")

    def progress_callback(stage: str, pct: int):
        jobs[job_id]["stage"] = stage
        jobs[job_id]["progress"] = pct
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

    try:
        result = add_captions_to_video(
            video_path=source_path,
            output_path=output_path,
            style=style,
            word_by_word=word_by_word,
            progress_callback=progress_callback,
        )

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": result["output_path"],
            "edit_notes": f"Captions ({style}){' word-by-word' if word_by_word else ''} — {result['segments_count']} segments",
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Captions complete: {result['segments_count']} segments")

    except Exception as e:
        logger.error(f"[{job_id}] Captions failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


def _run_voiceover_task(job_id: str, text: str, voice_id: Optional[str], attach_video_path: Optional[str]) -> None:
    """Background task: generate voiceover and optionally attach to video."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from voiceover import generate_voiceover, add_voiceover_to_video

    def progress_callback(stage: str, pct: int):
        jobs[job_id]["stage"] = stage
        jobs[job_id]["progress"] = pct
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

    try:
        progress_callback("Generating speech", 20)

        audio_output = str(GENERATED_DIR / f"{job_id}_voiceover.mp3")
        vo_result = generate_voiceover(
            text=text,
            voice_id=voice_id,
            output_path=audio_output,
        )

        progress_callback("Speech generated", 60)

        final_output = vo_result["output_path"]
        edit_notes = f"Voiceover via {vo_result['provider']} ({vo_result['duration']:.1f}s)"

        if attach_video_path and os.path.exists(attach_video_path):
            progress_callback("Mixing with video", 70)
            video_output = str(OUTPUTS_DIR / f"{job_id}_with_voiceover.mp4")
            mix_result = add_voiceover_to_video(
                video_path=attach_video_path,
                audio_path=vo_result["output_path"],
                output_path=video_output,
            )
            final_output = mix_result["output_path"]
            edit_notes += f" — mixed into video ({mix_result['duration']:.1f}s)"

        progress_callback("Complete", 100)

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": final_output,
            "edit_notes": edit_notes,
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Voiceover complete: {edit_notes}")

    except Exception as e:
        logger.error(f"[{job_id}] Voiceover failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


# ---------------------------------------------------------------------------
# Background task: Vibe Edit
# ---------------------------------------------------------------------------

def _run_vibe_edit_task(
    job_id: str,
    prompt: str,
    clips: List[str],
    style: str,
    music: Optional[str],
    duration: int,
) -> None:
    """Background task: AI vibe edit pipeline."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from remotion_renderer import vibe_edit

    output_path = str(OUTPUTS_DIR / f"{job_id}_vibe.mp4")

    def progress_callback(stage: str, pct: int):
        jobs[job_id]["stage"] = stage
        jobs[job_id]["progress"] = pct
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

    try:
        result = vibe_edit(
            prompt=prompt,
            clips=clips,
            style=style,
            music=music,
            duration=duration,
            output_path=output_path,
            progress_callback=progress_callback,
        )

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": result["output_path"],
            "duration": result["duration"],
            "clips_used": result["clips_used"],
            "edit_notes": f"Vibe Edit ({style}) via {result['method']}",
            "vibe_code": result.get("generated_code"),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Vibe Edit complete via {result['method']}")

    except Exception as e:
        logger.error(f"[{job_id}] Vibe Edit failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


# ---------------------------------------------------------------------------
# Image Generation endpoint
# ---------------------------------------------------------------------------

@app.post("/generate-image", summary="Generate an image from a text prompt")
async def generate_image_endpoint(
    request: GenerateImageRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Generate an image using Google Imagen 4.0.
    Processing runs asynchronously — poll GET /status/{job_id} for progress.
    """
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    enhanced_prompt = request.prompt
    if request.style:
        enhanced_prompt = f"{request.style} style. {request.prompt}"

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting image generation",
        "created_at": now,
        "updated_at": now,
        "prompt": enhanced_prompt,
        "video_files": [],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_image_generation_task,
        job_id=job_id,
        prompt=enhanced_prompt,
        aspect_ratio=request.aspect_ratio or "9:16",
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Image generation started. Poll GET /status/{job_id} for progress.",
    }


@app.post("/edit-image", summary="Edit an existing image with AI")
async def edit_image_endpoint(
    request: EditImageRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Edit an image using Nano Banana Pro (Gemini-powered image editing).
    Provide a job_id of a completed image generation, or an image_url/path.
    """
    source_image = None
    if request.job_id and request.job_id in jobs:
        source_job = jobs[request.job_id]
        if source_job.get("output_path") and os.path.exists(source_job["output_path"]):
            source_image = source_job["output_path"]
    elif request.image_url:
        source_image = request.image_url

    if not source_image:
        raise HTTPException(status_code=400, detail="No source image found. Provide a valid job_id or image_url.")

    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting image editing",
        "created_at": now,
        "updated_at": now,
        "prompt": request.edit_prompt,
        "video_files": [],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_image_edit_task,
        job_id=job_id,
        image_path=source_image,
        edit_prompt=request.edit_prompt,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Image editing started. Poll GET /status/{job_id} for progress.",
    }


@app.post("/generate-thumbnail", summary="Generate a thumbnail from a completed video")
async def generate_thumbnail_endpoint(
    request: GenerateThumbnailRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Auto-generate a thumbnail from a completed video's best frame.
    Uses Nano Banana Pro to enhance and style the frame.
    """
    source_job_id = request.job_id
    if source_job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Source job {source_job_id} not found")

    source_job = jobs[source_job_id]
    if source_job["status"] != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Source job is not complete (status: {source_job['status']})"
        )

    source_path = source_job.get("output_path")
    if not source_path or not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Source video/image file not found")

    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting thumbnail generation",
        "created_at": now,
        "updated_at": now,
        "prompt": request.style_prompt or "YouTube thumbnail",
        "video_files": [],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_thumbnail_task,
        job_id=job_id,
        source_path=source_path,
        style_prompt=request.style_prompt,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Thumbnail generation started. Poll GET /status/{job_id} for progress.",
    }


@app.post("/generate-image-to-video", summary="Generate video from an image")
async def generate_image_to_video_endpoint(
    image: UploadFile = File(...),
    prompt: str = Form(""),
    duration: int = Form(5),
    style: str = Form("cinematic"),
    aspect_ratio: str = Form("9:16"),
    background_tasks: BackgroundTasks = None,
) -> Dict[str, Any]:
    """
    Generate a video from an uploaded image using Kling AI image-to-video.
    Processing runs asynchronously — poll GET /status/{job_id} for progress.
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image file provided")

    job_id = str(uuid.uuid4())
    job_upload_dir = UPLOADS_DIR / job_id
    job_upload_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded image
    safe_name = "".join(c for c in image.filename if c.isalnum() or c in "._- ")
    image_dest = job_upload_dir / safe_name
    with open(image_dest, "wb") as f:
        content = await image.read()
        f.write(content)

    now = datetime.utcnow().isoformat()

    # Enhance prompt with style
    style_prefixes = {
        "cinematic": "Cinematic, film-quality, dramatic lighting.",
        "action": "Fast-paced, dynamic camera movement, high energy.",
        "vlog": "Natural, warm colors, authentic and personal.",
        "music_video": "Stylized, rhythmic movement, vivid colors.",
        "documentary": "Documentary style, natural lighting, observational.",
    }
    prefix = style_prefixes.get(style, "")
    enhanced_prompt = f"{prefix} {prompt}".strip() if prefix else prompt

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting image-to-video generation",
        "created_at": now,
        "updated_at": now,
        "prompt": enhanced_prompt,
        "video_files": [],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_image_to_video_task,
        job_id=job_id,
        image_path=str(image_dest),
        prompt=enhanced_prompt,
        duration=duration,
        aspect_ratio=aspect_ratio,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Image-to-video generation started. Poll GET /status/{job_id} for progress.",
    }


@app.post("/generate-music", summary="Generate background music with AI")
async def generate_music_endpoint(
    request: GenerateMusicRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Generate background music using Google Lyria 3 Pro.
    Great for adding music to Tubee edits when the user has no music.
    """
    job_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "stage": "Starting music generation",
        "created_at": now,
        "updated_at": now,
        "prompt": request.prompt,
        "video_files": [],
        "music_file": None,
        "output_path": None,
        "duration": None,
        "clips_used": None,
        "edit_notes": None,
        "error": None,
    }
    save_job(job_id)

    background_tasks.add_task(
        _run_music_generation_task,
        job_id=job_id,
        prompt=request.prompt,
        duration=request.duration or 30,
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Music generation started. Poll GET /status/{job_id} for progress.",
    }


# ---------------------------------------------------------------------------
# Background tasks: Image, Thumbnail, Music
# ---------------------------------------------------------------------------

def _run_image_to_video_task(job_id: str, image_path: str, prompt: str, duration: int, aspect_ratio: str) -> None:
    """Background task: AI image-to-video generation via Kling."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    from video_generator import generate_image_to_video, VideoGenerationError, NoAPIKeyError

    def progress_callback(stage: str, pct: int):
        jobs[job_id]["stage"] = stage
        jobs[job_id]["progress"] = pct
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

    try:
        output_path = generate_image_to_video(
            image_path=image_path,
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
            progress_callback=progress_callback,
        )

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": output_path,
            "edit_notes": "Generated with Kling AI (image-to-video)",
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Image-to-video generation complete")

    except Exception as e:
        logger.error(f"[{job_id}] Image-to-video generation failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


def _run_image_generation_task(job_id: str, prompt: str, aspect_ratio: str) -> None:
    """Background task: AI image generation."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from image_generator import generate_image_with_imagen

    try:
        jobs[job_id]["stage"] = "Generating image with Imagen 4.0"
        jobs[job_id]["progress"] = 30
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

        output_path = generate_image_with_imagen(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
        )

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": output_path,
            "edit_notes": "Generated with Imagen 4.0",
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Image generation complete")

    except Exception as e:
        logger.error(f"[{job_id}] Image generation failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


def _run_image_edit_task(job_id: str, image_path: str, edit_prompt: str) -> None:
    """Background task: AI image editing."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from image_generator import edit_image_with_nano_banana

    try:
        jobs[job_id]["stage"] = "Editing image with AI"
        jobs[job_id]["progress"] = 30
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

        output_path = edit_image_with_nano_banana(
            image_path=image_path,
            edit_prompt=edit_prompt,
        )

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": output_path,
            "edit_notes": "Edited with Nano Banana Pro",
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Image edit complete")

    except Exception as e:
        logger.error(f"[{job_id}] Image edit failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


def _run_thumbnail_task(job_id: str, source_path: str, style_prompt: Optional[str]) -> None:
    """Background task: thumbnail generation from video frame."""
    import sys
    import subprocess as _sp
    sys.path.insert(0, str(Path(__file__).parent))
    from image_generator import generate_thumbnail

    try:
        ext = Path(source_path).suffix.lower()
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv"}

        if ext in video_exts:
            jobs[job_id]["stage"] = "Extracting best frame from video"
            jobs[job_id]["progress"] = 20
            jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
            save_job(job_id)

            frame_path = str(GENERATED_DIR / f"{job_id}_frame.png")

            # Get video duration
            probe_cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", source_path,
            ]
            probe_result = _sp.run(probe_cmd, capture_output=True, text=True)
            duration = 5.0
            if probe_result.returncode == 0:
                fmt = json.loads(probe_result.stdout).get("format", {})
                duration = float(fmt.get("duration", 5.0))

            seek_time = duration / 3.0
            extract_cmd = [
                "ffmpeg", "-y", "-ss", str(seek_time),
                "-i", source_path, "-frames:v", "1",
                "-q:v", "2", frame_path,
            ]
            _sp.run(extract_cmd, capture_output=True, timeout=30)

            if not os.path.exists(frame_path):
                raise Exception("Failed to extract frame from video")
        else:
            frame_path = source_path

        jobs[job_id]["stage"] = "Generating thumbnail with AI"
        jobs[job_id]["progress"] = 50
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

        output_path = generate_thumbnail(
            video_frame_path=frame_path,
            style_prompt=style_prompt,
        )

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": output_path,
            "edit_notes": "Thumbnail generated with AI",
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Thumbnail generation complete")

    except Exception as e:
        logger.error(f"[{job_id}] Thumbnail generation failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


def _run_music_generation_task(job_id: str, prompt: str, duration: int) -> None:
    """Background task: AI music generation."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from music_generator import generate_music

    try:
        jobs[job_id]["stage"] = "Generating music with Lyria 3 Pro"
        jobs[job_id]["progress"] = 30
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        save_job(job_id)

        output_path = generate_music(
            prompt=prompt,
            duration_seconds=duration,
        )

        jobs[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Complete",
            "output_path": output_path,
            "music_file": output_path,
            "edit_notes": f"Music generated with Lyria 3 Pro ({duration}s)",
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)
        logger.info(f"[{job_id}] Music generation complete")

    except Exception as e:
        logger.error(f"[{job_id}] Music generation failed: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "stage": "Failed",
            "error": str(e),
            "updated_at": datetime.utcnow().isoformat(),
        })
        save_job(job_id)


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
