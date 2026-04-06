# 🎬 Tubee — AI-Powered Video Editor

Tubee is a local AI video editing app. Drop in raw footage, add an optional music track, type a prompt — and get a finished, beat-synced edit out the other side.

Built by Temitayo Agoro (Film Tuck Tubee) as Phase 1 of an AI video editing platform.

---

## How It Works

```
Raw Footage + Music
       ↓
  Scene Detection (PySceneDetect)
       ↓
  Beat Analysis (librosa)
       ↓
  AI Edit Decisions (Claude API)
       ↓
  Clip Assembly (FFmpeg + moviepy)
       ↓
  1080p MP4 Output
```

---

## Prerequisites

### 1. FFmpeg (required)
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Verify
ffmpeg -version
```

### 2. Python 3.10+
```bash
python --version  # Should be 3.10 or higher
```

---

## Installation

```bash
# Clone or download this project
cd /path/to/tubee

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

### Set Your Anthropic API Key

Tubee uses Claude for intelligent editing decisions. Without an API key, it falls back to a rule-based editor that still works — but Claude makes much smarter cuts.

**Option A: Environment variable (recommended)**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Option B: Edit the file directly**
Open `backend/ai_editor.py` and find:
```python
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
```
Replace `""` with your key string.

Get your API key at: https://console.anthropic.com/

---

## Usage

### Option 1: Watch Folder (Drop-and-Go)

The simplest way — just drop files into a folder.

```bash
# Start the watcher
python scripts/watch_folder.py
```

Then in another terminal / Finder:
```
~/tubee_input/
  prompt.txt        ← "Fast-paced highlight reel with energetic music"
  clip1.mp4
  clip2.mp4
  song.mp3          ← Optional
```

Tubee detects the files, processes them, and opens the output folder automatically.

**Output:** `~/tubee_output/{timestamp}/output.mp4`

---

### Option 2: REST API Server

The API gives you full control over uploads, jobs, and downloads.

```bash
# Start the server
cd backend
uvicorn main:app --reload --port 8000

# API docs available at:
# http://localhost:8000/docs
```

#### Step-by-step via API:

**1. Upload footage:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@clip1.mp4" \
  -F "files=@clip2.mp4" \
  -F "files=@song.mp3"
```
Response:
```json
{
  "job_id": "abc123...",
  "video_files": ["clip1.mp4", "clip2.mp4"],
  "music_file": "song.mp3"
}
```

**2. Submit edit prompt:**
```bash
curl -X POST http://localhost:8000/edit \
  -H "Content-Type: application/json" \
  -d '{"job_id": "abc123...", "prompt": "Create a cinematic highlight reel"}'
```

**3. Poll status:**
```bash
curl http://localhost:8000/status/abc123...
```
Response:
```json
{
  "job_id": "abc123...",
  "status": "processing",
  "progress": 55,
  "stage": "Asking AI for edit decisions"
}
```

**4. Download when done:**
```bash
curl -o my_edit.mp4 http://localhost:8000/download/abc123...
```

---

### Option 3: Run Pipeline Directly

```bash
cd backend
python processor.py output.mp4 clip1.mp4 clip2.mp4 \
  --music song.mp3 \
  --prompt "Energetic highlight reel, beat-synced cuts"
```

---

## Project Structure

```
tubee/
├── backend/
│   ├── main.py           # FastAPI server
│   ├── processor.py      # Main pipeline orchestrator
│   ├── scene_detect.py   # PySceneDetect wrapper
│   ├── beat_sync.py      # librosa beat detection
│   └── ai_editor.py      # Claude API integration
├── scripts/
│   └── watch_folder.py   # Drop-folder auto-processor
├── uploads/              # Auto-created: uploaded files
├── outputs/              # Auto-created: finished videos
├── jobs/                 # Auto-created: job state files
├── requirements.txt
└── README.md
```

---

## Output Specs

| Setting | Value |
|---------|-------|
| Resolution | 1920×1080 (1080p) |
| Format | MP4 |
| Video codec | H.264 (libx264) |
| Audio codec | AAC |
| Frame rate | 30 fps |
| Music volume | 80% |
| Original audio | 30% (when music present) |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload video + music files |
| `POST` | `/edit` | Submit prompt, start processing |
| `GET` | `/status/{job_id}` | Check job status (0–100%) |
| `GET` | `/download/{job_id}` | Download finished MP4 |
| `GET` | `/jobs` | List all jobs |
| `DELETE` | `/jobs/{job_id}` | Delete job + files |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |

---

## Troubleshooting

### "FFmpeg not found"
Make sure FFmpeg is installed and on your PATH: `brew install ffmpeg`

### Scene detection is slow
PySceneDetect downscales automatically. For large files, detection may take 30-60 seconds.

### "No Anthropic API key" warning
The app still works — it uses a rule-based editor. Cuts happen on downbeats (or every 3 seconds if no music). Set `ANTHROPIC_API_KEY` for smarter edits.

### librosa install fails
Try: `pip install librosa --no-build-isolation`
Or ensure you have: `brew install libsndfile`

### moviepy errors
moviepy requires FFmpeg to be installed at the system level (not just as a Python package).

---

## Roadmap (Phase 2+)

- [ ] Web UI (React frontend)
- [ ] Motion detection and auto-framing
- [ ] Color grading presets via Claude
- [ ] Multi-track timeline export
- [ ] Premiere Pro / DaVinci EDL export
- [ ] Mobile companion app (drop footage from iPhone)
- [ ] GPU-accelerated encoding

---

## License

Built by Temitayo Agoro — Film Tuck Tubee. All rights reserved.
# Force redeploy Mon Apr  6 19:20:00 EDT 2026
