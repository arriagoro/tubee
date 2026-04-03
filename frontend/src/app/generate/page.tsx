'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

const API = 'https://unparcelling-unnecessitating-randa.ngrok-free.dev';
const HEADERS = { 'ngrok-skip-browser-warning': 'true' };

const DURATIONS = [
  { label: '4s', value: 4, desc: 'Quick clip' },
  { label: '8s', value: 8, desc: 'Standard' },
  { label: '16s', value: 16, desc: 'Extended' },
];

const ASPECT_RATIOS = [
  { label: '9:16', icon: '📱', desc: 'Reels/TikTok' },
  { label: '16:9', icon: '🖥️', desc: 'YouTube' },
  { label: '1:1', icon: '⬜', desc: 'Square' },
];

const STYLES = [
  { label: 'Cinematic', value: 'cinematic', icon: '🎬' },
  { label: 'Action', value: 'action', icon: '⚡' },
  { label: 'Vlog', value: 'vlog', icon: '📹' },
  { label: 'Music Video', value: 'music_video', icon: '🎵' },
  { label: 'Documentary', value: 'documentary', icon: '🎥' },
];

type Stage = 'idle' | 'generating' | 'polling' | 'done' | 'error';

export default function GeneratePage() {
  const [prompt, setPrompt] = useState('');
  const [duration, setDuration] = useState(4);
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [style, setStyle] = useState('cinematic');
  const [stage, setStage] = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

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
          setError(data.error || 'Generation failed');
        }
      } catch {
        // keep polling
      }
    }, 3000);
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) { setError('Enter a prompt describing the video'); return; }
    setError('');
    setStage('generating');
    setProgress(0);
    setStatusMsg('Submitting generation request…');

    try {
      const res = await fetch(`${API}/generate`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, duration, style, aspect_ratio: aspectRatio }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || `Request failed (${res.status})`);
      }

      const data = await res.json();
      setJobId(data.job_id);
      setStage('polling');
      setStatusMsg('AI is generating your video…');
      startPolling(data.job_id);
    } catch (err: unknown) {
      setStage('error');
      setError(err instanceof Error ? err.message : 'Something went wrong');
    }
  };

  const handleDownload = () => {
    if (!jobId) return;
    const a = document.createElement('a');
    a.href = `${API}/download/${jobId}`;
    a.download = `tubee-generated-${jobId.slice(0, 8)}.mp4`;
    a.click();
  };

  const handleReset = () => {
    setPrompt(''); setDuration(4); setStyle('cinematic');
    setStage('idle'); setProgress(0); setStatusMsg('');
    setJobId(null); setError('');
    if (pollRef.current) clearInterval(pollRef.current);
  };

  const isWorking = stage === 'generating' || stage === 'polling';

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
        <div style={{
          flex: 1, padding: '14px 0', textAlign: 'center',
          background: '#00AAFF', color: '#fff', fontWeight: 700, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          ✨ Generate
        </div>
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
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, color: '#00AAFF' }}>
          ✨ AI Video Generator
        </h1>
        <p style={{ color: '#8899BB', fontSize: 14, marginTop: 4 }}>
          Describe a video and let AI create it for you
        </p>
      </div>

      {/* ── Prompt ───────────────────────────────────────── */}
      <textarea
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        placeholder="Describe the video you want to create…&#10;&#10;e.g. A cinematic drone shot flying over Miami Beach at golden hour, palm trees swaying, warm teal and orange color grade"
        disabled={isWorking}
        rows={4}
        style={{
          width: '100%', padding: 16, marginBottom: 20,
          background: '#0D1526', border: '1px solid rgba(0,170,255,0.15)', borderRadius: 12,
          color: '#fff', fontSize: 16, resize: 'vertical',
          outline: 'none', boxSizing: 'border-box',
          fontFamily: 'inherit', lineHeight: 1.5,
        }}
      />

      {/* ── Duration ─────────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>DURATION</p>
        <div style={{ display: 'flex', gap: 8 }}>
          {DURATIONS.map(d => (
            <button
              key={d.value}
              onClick={() => setDuration(d.value)}
              disabled={isWorking}
              style={{
                flex: 1, padding: '12px 8px', borderRadius: 12, border: 'none',
                background: duration === d.value ? '#00AAFF' : '#0D1526',
                color: duration === d.value ? '#fff' : '#8899BB',
                fontSize: 15, fontWeight: duration === d.value ? 700 : 500,
                cursor: isWorking ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
              }}
            >
              <div>{d.label}</div>
              <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>{d.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* ── Aspect Ratio ────────────────────────────────── */}
      <div style={{ marginBottom: 20 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>FORMAT</p>
        <div style={{ display: 'flex', gap: 8 }}>
          {ASPECT_RATIOS.map(ar => (
            <button
              key={ar.label}
              onClick={() => setAspectRatio(ar.label)}
              disabled={isWorking}
              style={{
                flex: 1, padding: '12px 8px', borderRadius: 12, border: 'none',
                background: aspectRatio === ar.label ? '#00AAFF' : '#0D1526',
                color: aspectRatio === ar.label ? '#fff' : '#8899BB',
                fontSize: 14, fontWeight: aspectRatio === ar.label ? 700 : 500,
                cursor: isWorking ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
              }}
            >
              <div style={{ fontSize: 20 }}>{ar.icon}</div>
              <div>{ar.label}</div>
              <div style={{ fontSize: 11, opacity: 0.7 }}>{ar.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* ── Style ────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>STYLE</p>
        <div style={{
          display: 'flex', gap: 8, overflowX: 'auto',
          paddingBottom: 8, WebkitOverflowScrolling: 'touch',
        }}>
          {STYLES.map(s => (
            <button
              key={s.value}
              onClick={() => setStyle(s.value)}
              disabled={isWorking}
              style={{
                flexShrink: 0, padding: '10px 18px',
                borderRadius: 99, border: 'none',
                background: style === s.value ? '#00AAFF' : '#0D1526',
                color: style === s.value ? '#fff' : '#8899BB',
                fontSize: 14, fontWeight: style === s.value ? 700 : 500,
                cursor: isWorking ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {s.icon} {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Error ────────────────────────────────────────── */}
      {error && (
        <div style={{
          background: '#2a0a0a', border: '1px solid #f44', borderRadius: 12,
          padding: 14, marginBottom: 16, color: '#f88', fontSize: 14,
          whiteSpace: 'pre-wrap',
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
          <p style={{ color: '#4a5a7a', fontSize: 12, marginTop: 8, textAlign: 'center' }}>
            AI generation can take 1-5 minutes depending on the provider
          </p>
        </div>
      )}

      {/* ── Done ─────────────────────────────────────────── */}
      {stage === 'done' && (
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <p style={{ fontSize: 20, color: '#00AAFF', fontWeight: 700, marginBottom: 16 }}>
            🎉 Your video is ready!
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
            Generate Another
          </button>
        </div>
      )}

      {/* ── Submit Button ────────────────────────────────── */}
      {stage !== 'done' && (
        <button
          onClick={handleGenerate}
          disabled={isWorking || !prompt.trim()}
          style={{
            width: '100%', padding: 20,
            background: isWorking || !prompt.trim() ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)',
            color: isWorking || !prompt.trim() ? '#4a5a7a' : '#fff',
            border: 'none', borderRadius: 14,
            fontSize: 20, fontWeight: 700,
            cursor: isWorking || !prompt.trim() ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            boxShadow: !isWorking && prompt.trim() ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
          }}
        >
          {isWorking ? '⏳ Generating…' : '✨ Generate Video'}
        </button>
      )}
    </div>
  );
}
