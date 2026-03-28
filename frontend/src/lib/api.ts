const API_BASE = '/api';

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
  files.forEach((file) => {
    formData.append('files', file);
  });

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }

  return res.json();
}

export async function uploadMusic(file: File): Promise<{ music_id: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Music upload failed' }));
    throw new Error(err.detail || 'Music upload failed');
  }

  const data = await res.json();
  return { music_id: data.file_ids?.[0] || data.music_id };
}

export async function submitEdit(req: EditRequest): Promise<EditResponse> {
  const res = await fetch(`${API_BASE}/edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Edit submission failed' }));
    throw new Error(err.detail || 'Edit submission failed');
  }

  return res.json();
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/status/${jobId}`);

  if (!res.ok) {
    throw new Error('Failed to fetch status');
  }

  return res.json();
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/download/${jobId}`;
}
