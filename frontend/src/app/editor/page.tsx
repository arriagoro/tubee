'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

const API = 'https://unparcelling-unnecessitating-randa.ngrok-free.dev';
const HEADERS = { 'ngrok-skip-browser-warning': 'true' };

const STYLES = [
  'Cinematic', 'Fast Cuts', 'Smooth', 'Vlog', 'Music Video',
  'Documentary', 'Retro', 'Minimal', 'Hype', 'Storytelling',
];

const ASPECT_RATIOS = [
  { label: '9:16', icon: '📱', desc: 'Reels/TikTok' },
  { label: '1:1', icon: '⬜', desc: 'Feed Square' },
  { label: '4:5', icon: '📷', desc: 'IG Portrait' },
  { label: '16:9', icon: '🖥️', desc: 'YouTube' },
];

type Stage = 'idle' | 'uploading' | 'editing' | 'polling' | 'done' | 'error';

export default function EditorPage() {
  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [musicFile, setMusicFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('Cinematic');
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [stage, setStage] = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const videoInputRef = useRef<HTMLInputElement>(null);
  const musicInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) setVideoFiles(files);
  };

  const handleMusicSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) setMusicFile(files[0]);
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
        } else if (data.status === 'failed' || data.status === 'error') {
          if (pollRef.current) clearInterval(pollRef.current);
          setStage('error');
          setError(data.error || 'Edit failed');
        }
      } catch {
        // keep polling, might be transient
      }
    }, 2000);
  };

  const handleSubmit = async () => {
    if (videoFiles.length === 0) { setError('Select at least one video'); return; }
    setError('');
    setStage('uploading');
    setProgress(0);
    setStatusMsg('Uploading files…');

    try {
      const form = new FormData();
      videoFiles.forEach(f => form.append('files', f));
      if (musicFile) form.append('files', musicFile);

      const upRes = await fetch(`${API}/upload`, {
        method: 'POST',
        headers: HEADERS,
        body: form,
      });
      if (!upRes.ok) throw new Error(`Upload failed (${upRes.status})`);
      const upData = await upRes.json();
      const id = upData.job_id;
      setJobId(id);

      setStage('editing');
      setStatusMsg('Starting edit…');
      const editRes = await fetch(`${API}/edit`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: id, prompt, style, aspect_ratio: aspectRatio }),
      });
      if (!editRes.ok) throw new Error(`Edit request failed (${editRes.status})`);

      setStage('polling');
      setStatusMsg('Processing…');
      startPolling(id);
    } catch (err: unknown) {
      setStage('error');
      setError(err instanceof Error ? err.message : 'Something went wrong');
    }
  };

  const handleDownload = () => {
    if (!jobId) return;
    const a = document.createElement('a');
    a.href = `${API}/download/${jobId}`;
    a.download = `tubee-edit-${jobId}.mp4`;
    a.click();
  };

  const handleReset = () => {
    setVideoFiles([]); setMusicFile(null); setPrompt(''); setStyle('Cinematic');
    setStage('idle'); setProgress(0); setStatusMsg(''); setJobId(null); setError('');
    if (pollRef.current) clearInterval(pollRef.current);
  };

  const isWorking = stage === 'uploading' || stage === 'editing' || stage === 'polling';

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
        <div style={{
          flex: 1, padding: '14px 0', textAlign: 'center',
          background: '#00AAFF', color: '#fff', fontWeight: 700, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          ✂️ Edit
        </div>
        <Link href="/generate" style={{
          flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
          background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          ✨ Generate
        </Link>
        <Link href="/captions" style={{
          flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
          background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          💬 Captions
        </Link>
        <Link href="/upscale" style={{
          flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
          background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
        }}>
          🔍 Upscale
        </Link>
      </nav>

      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, color: '#00AAFF' }}>
          ✂️ Tubee Editor
        </h1>
        <p style={{ color: '#8899BB', fontSize: 14, marginTop: 4 }}>AI-powered video editing</p>
      </div>

      {/* ── Video Select ─────────────────────────────────── */}
      <input
        ref={videoInputRef}
        type="file"
        multiple
        accept="video/*,*/*"
        onChange={handleVideoSelect}
        style={{ display: 'none' }}
      />
      <button
        onClick={() => videoInputRef.current?.click()}
        disabled={isWorking}
        style={{
          width: '100%', padding: '20px', marginBottom: 12,
          background: videoFiles.length > 0 ? 'rgba(0,170,255,0.1)' : '#0D1526',
          border: videoFiles.length > 0 ? '2px solid #00AAFF' : '2px dashed rgba(0,170,255,0.3)',
          borderRadius: 16, color: '#fff', fontSize: 18, fontWeight: 600,
          cursor: isWorking ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s',
        }}
      >
        {videoFiles.length === 0 ? (
          <>📹 Select Videos</>
        ) : (
          <span style={{ color: '#00AAFF' }}>
            ✅ {videoFiles.length} video{videoFiles.length > 1 ? 's' : ''} ready
          </span>
        )}
      </button>

      {/* ── Music Select ─────────────────────────────────── */}
      <input
        ref={musicInputRef}
        type="file"
        accept="audio/*,*/*"
        onChange={handleMusicSelect}
        style={{ display: 'none' }}
      />
      <button
        onClick={() => musicInputRef.current?.click()}
        disabled={isWorking}
        style={{
          width: '100%', padding: '16px', marginBottom: 20,
          background: musicFile ? 'rgba(0,170,255,0.1)' : '#0D1526',
          border: musicFile ? '2px solid #00AAFF' : '2px dashed rgba(0,170,255,0.15)',
          borderRadius: 16, color: musicFile ? '#00AAFF' : '#8899BB',
          fontSize: 16, fontWeight: 500,
          cursor: isWorking ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s',
        }}
      >
        {musicFile ? `🎵 ${musicFile.name}` : '🎵 Add Music (optional)'}
      </button>

      {/* ── Prompt ───────────────────────────────────────── */}
      <textarea
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        placeholder="Describe your edit… e.g. Fast-paced highlight reel with beat drops"
        disabled={isWorking}
        rows={3}
        style={{
          width: '100%', padding: 16, marginBottom: 16,
          background: '#0D1526', border: '1px solid rgba(0,170,255,0.15)', borderRadius: 12,
          color: '#fff', fontSize: 16, resize: 'vertical',
          outline: 'none', boxSizing: 'border-box',
          fontFamily: 'inherit',
        }}
      />

      {/* ── Style Pills ──────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>STYLE</p>
        <div style={{
          display: 'flex', gap: 8, overflowX: 'auto',
          paddingBottom: 8, WebkitOverflowScrolling: 'touch',
        }}>
          {STYLES.map(s => (
            <button
              key={s}
              onClick={() => setStyle(s)}
              disabled={isWorking}
              style={{
                flexShrink: 0, padding: '10px 18px',
                borderRadius: 99, border: 'none',
                background: style === s ? '#00AAFF' : '#0D1526',
                color: style === s ? '#fff' : '#8899BB',
                fontSize: 14, fontWeight: style === s ? 700 : 500,
                cursor: isWorking ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* ── Aspect Ratio ────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>FORMAT</p>
        <div style={{
          display: 'flex', gap: 8, overflowX: 'auto',
          paddingBottom: 8, WebkitOverflowScrolling: 'touch',
        }}>
          {ASPECT_RATIOS.map(ar => (
            <button
              key={ar.label}
              onClick={() => setAspectRatio(ar.label)}
              disabled={isWorking}
              style={{
                flexShrink: 0, padding: '10px 16px',
                borderRadius: 99, border: 'none',
                background: aspectRatio === ar.label ? '#00AAFF' : '#0D1526',
                color: aspectRatio === ar.label ? '#fff' : '#8899BB',
                fontSize: 13, fontWeight: aspectRatio === ar.label ? 700 : 500,
                cursor: isWorking ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {ar.icon} {ar.label}
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
              borderRadius: 99,
              transition: 'width 0.5s ease',
            }} />
          </div>
        </div>
      )}

      {/* ── Done ─────────────────────────────────────────── */}
      {stage === 'done' && (
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <p style={{ fontSize: 20, color: '#00AAFF', fontWeight: 700, marginBottom: 16 }}>
            🎉 Your edit is ready!
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
            ⬇️ Download Video
          </button>
          <button
            onClick={handleReset}
            style={{
              width: '100%', padding: 14, background: 'transparent',
              color: '#8899BB', border: '1px solid rgba(0,170,255,0.15)', borderRadius: 14,
              fontSize: 15, cursor: 'pointer',
            }}
          >
            Start New Edit
          </button>
        </div>
      )}

      {/* ── Submit Button ────────────────────────────────── */}
      {stage !== 'done' && (
        <button
          onClick={handleSubmit}
          disabled={isWorking || videoFiles.length === 0}
          style={{
            width: '100%', padding: 20,
            background: isWorking || videoFiles.length === 0 ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)',
            color: isWorking || videoFiles.length === 0 ? '#4a5a7a' : '#fff',
            border: 'none', borderRadius: 14,
            fontSize: 20, fontWeight: 700,
            cursor: isWorking || videoFiles.length === 0 ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            boxShadow: !isWorking && videoFiles.length > 0 ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
          }}
        >
          {isWorking ? '⏳ Working…' : '✂️ Create Edit'}
        </button>
      )}
    </div>
  );
}
