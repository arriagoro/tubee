const API_BASE = 'https://tubee-production.up.railway.app';
const SKIP_NGROK = { 'ngrok-skip-browser-warning': 'true' };

export interface UploadResponse {
  file_ids: string[];
}

export interface EditRequest {
  file_ids: string[];
  music_id?: string;
  prompt: string;
  style: string;
}

export interface EditResponse {
  job_id: string;
}

export interface StatusResponse {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  stage: string;
  error?: string;
}

export async function uploadFiles(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => { formData.append('files', file); });
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', headers: SKIP_NGROK, body: formData });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Upload failed' })); throw new Error(err.detail || 'Upload failed'); }
  return res.json();
}

export async function uploadMusic(file: File): Promise<{ music_id: string }> {
  const formData = new FormData();
  formData.append('files', file);
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', headers: SKIP_NGROK, body: formData });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Music upload failed' })); throw new Error(err.detail || 'Music upload failed'); }
  const data = await res.json();
  return { music_id: data.file_ids?.[0] };
}

export async function submitEdit(req: EditRequest): Promise<EditResponse> {
  const res = await fetch(`${API_BASE}/edit`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...SKIP_NGROK }, body: JSON.stringify(req) });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Edit submission failed' })); throw new Error(err.detail || 'Edit submission failed'); }
  return res.json();
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/status/${jobId}`, { headers: SKIP_NGROK });
  if (!res.ok) { throw new Error('Failed to fetch status'); }
  return res.json();
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/download/${jobId}`;
}

// ─── Video Generation ────────────────────────────────────────────────────────

export interface GenerateRequest {
  prompt: string;
  duration?: number;
  style?: string;
  aspect_ratio?: string;
}

export interface GenerateResponse {
  job_id: string;
  status: string;
  message: string;
}

export async function submitGenerate(req: GenerateRequest): Promise<GenerateResponse> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...SKIP_NGROK },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Generation failed' }));
    throw new Error(err.detail || 'Generation failed');
  }
  return res.json();
}

// ─── Video Upscaling ─────────────────────────────────────────────────────────

export interface UpscaleRequest {
  job_id: string;
  scale?: number;
}

export interface UpscaleResponse {
  job_id: string;
  status: string;
  message: string;
}

export async function submitUpscale(req: UpscaleRequest): Promise<UpscaleResponse> {
  const res = await fetch(`${API_BASE}/upscale`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...SKIP_NGROK },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upscale failed' }));
    throw new Error(err.detail || 'Upscale failed');
  }
  return res.json();
}

// ─── Vibe Edit ───────────────────────────────────────────────────────────────

export interface VibeEditRequest {
  job_id: string;
  prompt: string;
  style?: string;
  duration?: number;
}

export interface VibeEditResponse {
  job_id: string;
  status: string;
  message: string;
}

export async function submitVibeEdit(req: VibeEditRequest): Promise<VibeEditResponse> {
  const res = await fetch(`${API_BASE}/vibe-edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...SKIP_NGROK },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Vibe Edit failed' }));
    throw new Error(err.detail || 'Vibe Edit failed');
  }
  return res.json();
}

export async function getVibeCode(jobId: string): Promise<{ job_id: string; code: string | null; status: string }> {
  const res = await fetch(`${API_BASE}/vibe-code/${jobId}`, { headers: SKIP_NGROK });
  if (!res.ok) throw new Error('Failed to fetch vibe code');
  return res.json();
}

// ─── List Jobs ───────────────────────────────────────────────────────────────

export interface JobSummary {
  job_id: string;
  status: string;
  progress: number;
  stage: string;
  created_at: string;
  prompt: string | null;
}

export async function listJobs(): Promise<{ total: number; jobs: JobSummary[] }> {
  const res = await fetch(`${API_BASE}/jobs`, { headers: SKIP_NGROK });
  if (!res.ok) throw new Error('Failed to list jobs');
  return res.json();
}
