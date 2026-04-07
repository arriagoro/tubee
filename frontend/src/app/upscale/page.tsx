'use client';
import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';
import { apiBase, SKIP_NGROK } from '@/lib/api';
const HEADERS = SKIP_NGROK;
type Stage = 'idle' | 'loading-jobs' | 'upscaling' | 'polling' | 'done' | 'error';
interface Job {
  job_id: string;
  status: string;
  prompt: string | null;
  stage: string;
  created_at: string;
}
export default function UpscalePage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [scale, setScale] = useState(4);
  const [stage, setStage] = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [upscaleJobId, setUpscaleJobId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { user } = useAuth();
  const [API, setAPI] = useState('');
  useEffect(() => {
    apiBase().then(base => {
      setAPI(base);
      loadJobsWithBase(base);
    });
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);
  const loadJobsWithBase = async (base: string) => {
    setStage('loading-jobs');
    try {
      const res = await fetch(`${base}/jobs`, { headers: HEADERS });
      const data = await res.json();
      const completedJobs = (data.jobs || []).filter((j: Job) => j.status === 'done');
      setJobs(completedJobs);
      setStage('idle');
    } catch {
      setStage('idle');
    }
  };
  const loadJobs = async () => {
    const base = await apiBase();
    await loadJobsWithBase(base);
  };
  const startPolling = (id: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/status/${id}`, { headers: HEADERS });
        const data = await res.json();
        setProgress(data.progress ?? 0);
        setStatusMsg(data.stage ?? data.status ?? '');
        if (data.status === 'completed' || data.status === 'done') {
          if (pollRef.current) clearInterval(pollRef.current);
          setStage('done');
          setProgress(100);
          // trial check removed)
        } else if (data.status === 'failed' || data.status === 'error') {
          if (pollRef.current) clearInterval(pollRef.current);
          setStage('error');
          setError(data.error || 'Upscale failed');
        }
      } catch {
        // keep polling
      }
    }, 3000);
  };
  const handleUpscale = async () => {
    if (!selectedJob) { setError('Select a video to upscale'); return; }
    // trial check removed
    setError('');
    setStage('upscaling');
    setProgress(0);
    setStatusMsg('Starting upscale…');
    try {
      const res = await fetch(`${API}/upscale`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: selectedJob, scale }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      setUpscaleJobId(data.job_id);
      setStage('polling');
      setStatusMsg('Upscaling video…');
      startPolling(data.job_id);
    } catch (err: unknown) {
      setStage('error');
      setError(err instanceof Error ? err.message : 'Something went wrong');
    }
  };
  const handleDownload = () => {
    if (!upscaleJobId) return;
    const a = document.createElement('a');
    a.href = `${API}/download/${upscaleJobId}`;
    a.download = `tubee-upscaled-${upscaleJobId.slice(0, 8)}.mp4`;
    a.click();
  };
  const handleReset = () => {
    setSelectedJob(null); setScale(4);
    setStage('idle'); setProgress(0); setStatusMsg('');
    setUpscaleJobId(null); setError('');
    if (pollRef.current) clearInterval(pollRef.current);
    loadJobs();
  };
  const isWorking = stage === 'upscaling' || stage === 'polling';
  return (
    <div style={{
      minHeight: '100vh', background: '#0A0F1E', color: '#fff',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '20px', paddingBottom: '120px',
    }}>
      {/* Navigation */}
      <nav style={{
        display: 'flex', gap: 0, marginBottom: 32, borderRadius: 14,
        overflow: 'hidden', border: '1px solid rgba(0,170,255,0.15)',
      }}>
        <Link href="/editor" style={{
          flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
          background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          ✂️ Edit
        </Link>
        <Link href="/generate" style={{
          flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
          background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          ✨ Generate
        </Link>
        <Link href="/vibe" style={{
          flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
          background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          🎨 Vibe
        </Link>
        <Link href="/captions" style={{
          flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
          background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          💬 Captions
        </Link>
        <Link href="/clipper" style={{
          flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
          background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          🎬 Clipper
        </Link>
        <div style={{
          flex: 1, padding: '14px 0', textAlign: 'center',
          background: '#00AAFF', color: '#fff', fontWeight: 700, fontSize: 15,
        }}>
          🔍 Upscale
        </div>
      </nav>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, color: '#00AAFF' }}>
          🔍 Video Upscaler
        </h1>
        <p style={{ color: '#8899BB', fontSize: 14, marginTop: 4 }}>
          Upscale your videos to 4K with AI • No API key needed
        </p>
      </div>
      {/* Trial Banner & Upgrade Modal */}
      
      
      {/* ── Select Video ─────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>SELECT A COMPLETED VIDEO</p>
        {jobs.length === 0 ? (
          <div style={{
            padding: 20, background: '#0D1526', borderRadius: 12,
            border: '1px dashed rgba(0,170,255,0.3)', textAlign: 'center', color: '#4a5a7a',
          }}>
            No completed videos found. Edit or generate a video first.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {jobs.map(job => (
              <button
                key={job.job_id}
                onClick={() => setSelectedJob(job.job_id)}
                disabled={isWorking}
                style={{
                  padding: '14px 16px', borderRadius: 12, border: 'none',
                  background: selectedJob === job.job_id ? 'rgba(0,170,255,0.1)' : '#0D1526',
                  outline: selectedJob === job.job_id ? '2px solid #00AAFF' : '1px solid rgba(0,170,255,0.15)',
                  color: '#fff', textAlign: 'left',
                  cursor: isWorking ? 'not-allowed' : 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
                  {job.prompt ? job.prompt.slice(0, 60) + (job.prompt.length > 60 ? '…' : '') : `Job ${job.job_id.slice(0, 8)}`}
                </div>
                <div style={{ fontSize: 12, color: '#4a5a7a' }}>
                  {new Date(job.created_at).toLocaleString()} • {job.job_id.slice(0, 8)}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
      {/* ── Scale ────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>UPSCALE FACTOR</p>
        <div style={{ display: 'flex', gap: 8 }}>
          {[
            { value: 2, label: '2×', desc: '1080p → 4K' },
            { value: 4, label: '4×', desc: '720p → 4K' },
          ].map(s => (
            <button
              key={s.value}
              onClick={() => setScale(s.value)}
              disabled={isWorking}
              style={{
                flex: 1, padding: '14px 8px', borderRadius: 12, border: 'none',
                background: scale === s.value ? '#00AAFF' : '#0D1526',
                color: scale === s.value ? '#fff' : '#8899BB',
                fontSize: 18, fontWeight: scale === s.value ? 700 : 500,
                cursor: isWorking ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
              }}
            >
              <div>{s.label}</div>
              <div style={{ fontSize: 12, opacity: 0.7, marginTop: 2 }}>{s.desc}</div>
            </button>
          ))}
        </div>
      </div>
      {/* ── Error ────────────────────────────────────────── */}
      {error && (
        <div style={{
          background: '#2a0a0a', border: '1px solid #f44', borderRadius: 12,
          padding: 14, marginBottom: 16, color: '#f88', fontSize: 14,
        }}>
          ⚠️ {error}
        </div>
      )}
      {/* ── Progress ─────────────────────────────────────── */}
      {isWorking && (
        <div style={{ marginBottom: 20 }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            marginBottom: 8, fontSize: 14,
          }}>
            <span style={{ color: '#00AAFF' }}>{statusMsg}</span>
            <span style={{ color: '#8899BB' }}>{progress}%</span>
          </div>
          <div style={{
            width: '100%', height: 8, background: '#0D1526', borderRadius: 99,
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${Math.max(progress, 3)}%`, height: '100%',
              background: 'linear-gradient(90deg, #00AAFF, #00D4FF)',
              borderRadius: 99, transition: 'width 0.5s ease',
            }} />
          </div>
        </div>
      )}
      {/* ── Done ─────────────────────────────────────────── */}
      {stage === 'done' && (
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <p style={{ fontSize: 20, color: '#00AAFF', fontWeight: 700, marginBottom: 16 }}>
            🎉 Upscaled video is ready!
          </p>
          <button
            onClick={handleDownload}
            style={{
              width: '100%', padding: 18,
              background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
              color: '#fff', border: 'none', borderRadius: 14,
              fontSize: 18, fontWeight: 700, cursor: 'pointer',
              marginBottom: 12,
              boxShadow: '0 0 20px rgba(0,170,255,0.3)',
            }}
          >
            ⬇️ Download Upscaled Video
          </button>
          <button
            onClick={handleReset}
            style={{
              width: '100%', padding: 14, background: 'transparent',
              color: '#8899BB', border: '1px solid rgba(0,170,255,0.15)', borderRadius: 14,
              fontSize: 15, cursor: 'pointer',
            }}
          >
            Upscale Another
          </button>
        </div>
      )}
      {/* ── Submit Button ────────────────────────────────── */}
      {stage !== 'done' && (
        <button
          onClick={handleUpscale}
          disabled={isWorking || !selectedJob}
          style={{
            width: '100%', padding: 20,
            background: isWorking || !selectedJob ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)',
            color: isWorking || !selectedJob ? '#4a5a7a' : '#fff',
            border: 'none', borderRadius: 14,
            fontSize: 20, fontWeight: 700,
            cursor: isWorking || !selectedJob ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            boxShadow: !isWorking && selectedJob ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
          }}
        >
          {isWorking ? '⏳ Upscaling…' : `🔍 Upscale ${scale}×`}
        </button>
      )}
    </div>
  );
}
