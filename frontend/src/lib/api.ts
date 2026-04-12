const RAILWAY = 'https://tubee-api.itsthatseason.com';
const NGROK = 'https://tubee-api.itsthatseason.com';
export const SKIP_NGROK = { 'ngrok-skip-browser-warning': 'true' };

async function getApiBase(): Promise<string> {
  try {
    // Video processing requires ffmpeg, so only use Railway when it's fully ready
    const r = await fetch(`${RAILWAY}/health`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) {
      const data = await r.json();
      if (data.ffmpeg === true) return RAILWAY;
    }
  } catch {}
  return NGROK;
}

async function getAuthApiBase(): Promise<string> {
  try {
    // Auth, subscriptions, checkout, and portal do NOT require ffmpeg
    const r = await fetch(`${RAILWAY}/health`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) return RAILWAY;
  } catch {}
  return NGROK;
}

// Cache the result
let _apiBase: string | null = null;
let _authApiBase: string | null = null;
let _isRailway: boolean = false;

export async function apiBase(): Promise<string> {
  if (!_apiBase) {
    _apiBase = await getApiBase();
    _isRailway = _apiBase === RAILWAY;
  }
  return _apiBase;
}

export async function authApiBase(): Promise<string> {
  if (!_authApiBase) {
    _authApiBase = await getAuthApiBase();
  }
  return _authApiBase;
}

export function isRailwayActive(): boolean {
  return _isRailway;
}

/** Force re-check on next call (e.g. after network change) */
export function resetApiBase(): void {
  _apiBase = null;
  _authApiBase = null;
  _isRailway = false;
}

// ─── Types ───────────────────────────────────────────────────────────────────

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
  const API_BASE = await apiBase();
  const formData = new FormData();
  files.forEach((file) => { formData.append('files', file); });
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', headers: SKIP_NGROK, body: formData });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Upload failed' })); throw new Error(err.detail || 'Upload failed'); }
  return res.json();
}

export async function uploadMusic(file: File): Promise<{ music_id: string }> {
  const API_BASE = await apiBase();
  const formData = new FormData();
  formData.append('files', file);
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', headers: SKIP_NGROK, body: formData });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Music upload failed' })); throw new Error(err.detail || 'Music upload failed'); }
  const data = await res.json();
  return { music_id: data.file_ids?.[0] };
}

export async function submitEdit(req: EditRequest): Promise<EditResponse> {
  const API_BASE = await apiBase();
  const res = await fetch(`${API_BASE}/edit`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...SKIP_NGROK }, body: JSON.stringify(req) });
  if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Edit submission failed' })); throw new Error(err.detail || 'Edit submission failed'); }
  return res.json();
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  const API_BASE = await apiBase();
  const res = await fetch(`${API_BASE}/status/${jobId}`, { headers: SKIP_NGROK });
  if (!res.ok) { throw new Error('Failed to fetch status'); }
  return res.json();
}

export async function getDownloadUrl(jobId: string): Promise<string> {
  const API_BASE = await apiBase();
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
  const API_BASE = await apiBase();
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
  const API_BASE = await apiBase();
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
  const API_BASE = await apiBase();
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
  const API_BASE = await apiBase();
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
  const API_BASE = await apiBase();
  const res = await fetch(`${API_BASE}/jobs`, { headers: SKIP_NGROK });
  if (!res.ok) throw new Error('Failed to list jobs');
  return res.json();
}

// ─── Auto-Clipper ────────────────────────────────────────────────────────────

export interface AutoClipRequest {
  job_id: string;
  num_clips?: number;
  clip_duration?: number;
  style?: string;
  format?: string;
}

export interface AutoClipResponse {
  job_id: string;
  status: string;
}

export interface ClipHighlight {
  start: number;
  end: number;
  duration: number;
  score: number;
  reason: string;
  type: string;
  transcript_snippet: string;
}

export interface ClipResult {
  index: number;
  filename: string;
  highlight: ClipHighlight;
  download_url: string;
}

export interface ClipsResponse {
  job_id: string;
  status: string;
  progress: number;
  stage: string;
  highlights: ClipHighlight[];
  clips: ClipResult[];
  total_clips: number;
}

export async function submitAutoClip(req: AutoClipRequest): Promise<AutoClipResponse> {
  const API_BASE = await apiBase();
  const res = await fetch(`${API_BASE}/auto-clip`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...SKIP_NGROK },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Auto-clip failed' }));
    throw new Error(err.detail || 'Auto-clip failed');
  }
  return res.json();
}

export async function getClips(jobId: string): Promise<ClipsResponse> {
  const API_BASE = await apiBase();
  const res = await fetch(`${API_BASE}/clips/${jobId}`, { headers: SKIP_NGROK });
  if (!res.ok) throw new Error('Failed to fetch clips');
  return res.json();
}

export function getClipDownloadUrl(apiBase: string, jobId: string, clipIndex: number): string {
  return `${apiBase}/clips/${jobId}/download/${clipIndex}`;
}

export function getAllClipsDownloadUrl(apiBase: string, jobId: string): string {
  return `${apiBase}/clips/${jobId}/download-all`;
}

// ─── Stripe Payments ─────────────────────────────────────────────────────────

export interface CheckoutSessionRequest {
  plan: 'starter' | 'pro';
  user_email: string;
  user_id: string;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
}

export async function createCheckoutSession(req: CheckoutSessionRequest): Promise<CheckoutSessionResponse> {
  const API_BASE = await authApiBase();
  const res = await fetch(`${API_BASE}/create-checkout-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...SKIP_NGROK },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Checkout failed' }));
    throw new Error(err.detail || 'Failed to create checkout session');
  }
  return res.json();
}

export interface SubscriptionStatusResponse {
  is_paid: boolean;
  plan: 'starter' | 'pro' | null;
  status: string;
  stripe_customer_id?: string;
}

export async function getSubscriptionStatus(userId: string): Promise<SubscriptionStatusResponse> {
  const API_BASE = await authApiBase();
  const res = await fetch(`${API_BASE}/subscription-status/${userId}`, {
    headers: SKIP_NGROK,
  });
  if (!res.ok) throw new Error('Failed to check subscription status');
  return res.json();
}

export interface PortalSessionResponse {
  portal_url: string;
}

export async function createPortalSession(userId: string): Promise<PortalSessionResponse> {
  const API_BASE = await authApiBase();
  const res = await fetch(`${API_BASE}/create-portal-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...SKIP_NGROK },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Portal session failed' }));
    throw new Error(err.detail || 'Failed to create portal session');
  }
  return res.json();
}
