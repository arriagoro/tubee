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

for d in [UPLOADS_DIR, OUTPUTS_DIR, JOBS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

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

    # Run processing in background thread (CPU-bound work)
    background_tasks.add_task(
        _run_processing_task,
        job_id=job_id,
        target_duration=request.target_duration,
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
# Background processing
# ---------------------------------------------------------------------------

def _run_processing_task(job_id: str, target_duration: Optional[float] = None) -> None:
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


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
