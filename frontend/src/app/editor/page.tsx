'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';
import { apiBase, authApiBase, isRailwayActive, SKIP_NGROK } from '@/lib/api';

const HEADERS = SKIP_NGROK;

type Stage = 'idle' | 'uploading' | 'editing' | 'polling' | 'done' | 'error';

const STYLE_OPTIONS = [
  { value: 'cinematic', label: 'Cinematic' },
  { value: 'music video', label: 'Music Video' },
  { value: 'hype', label: 'Hype' },
  { value: 'retro', label: 'Retro' },
  { value: 'minimal', label: 'Clean' },
];

const DURATION_OPTIONS = [
  { value: 15, label: '15s' },
  { value: 30, label: '30s' },
  { value: 45, label: '45s' },
  { value: 60, label: '60s' },
];

const TRANSITION_OPTIONS = [
  { value: 'mixed', label: 'Smart Mix' },
  { value: 'hard_cut', label: 'Hard Cuts' },
  { value: 'whip_pan', label: 'Whip Pan' },
  { value: 'zoom_blur', label: 'Zoom Blur' },
  { value: 'glitch', label: 'Glitch' },
  { value: 'fade', label: 'Fade' },
];

const FORMAT_OPTIONS = [
  { value: 'reels', label: '9:16 Reels' },
  { value: 'square', label: '1:1 Square' },
  { value: 'landscape', label: '16:9 Landscape' },
];

const QUALITY_OPTIONS = [
  { value: '1080p', label: '1080p' },
  { value: '2k', label: '2K' },
  { value: '4k', label: '4K' },
];

const PROMPT_TEMPLATES = [
  {
    label: 'Viral reel',
    prompt: 'Make this a fast viral reel with a strong first-second hook, 1-2 second cuts, pattern interrupts, and clean beat-synced transitions.',
  },
  {
    label: 'Talking head',
    prompt: 'Turn this into a sharp talking-head reel with the best line first, remove dead air, keep pacing tight, and make it feel premium but natural.',
  },
  {
    label: 'Product hype',
    prompt: 'Create a punchy product-focused edit with quick reveals, snap zooms, bold energy, and a strong closing payoff.',
  },
  {
    label: 'Cinematic mini',
    prompt: 'Edit this like a short cinematic story with a hook first, polished pacing, motion-matched cuts, and one memorable ending beat.',
  },
];

const HOOK_OPTIONS = [
  { value: 'best-shot', label: 'Best shot first' },
  { value: 'fastest-hook', label: 'Fastest hook' },
  { value: 'best-line', label: 'Best line first' },
];

export default function EditorPage() {
  const [subscriptionChecked, setSubscriptionChecked] = useState(false);

  useEffect(() => {
    const checkPayment = async () => {
      try {
        const { data: { user: currentUser } } = await (await import('@/lib/supabase')).supabase.auth.getUser();
        if (!currentUser) {
          window.location.replace('/auth/login');
          return;
        }

        const API = await authApiBase();
        const res = await fetch(`${API}/subscription-status/${currentUser.id}`, {
          headers: HEADERS,
        });

        if (res.ok) {
          const data = await res.json();
          if (!data.is_paid) {
            window.location.replace('/pricing');
            return;
          }
        } else {
          window.location.replace('/pricing');
          return;
        }
      } catch {
        window.location.replace('/pricing');
        return;
      }

      setSubscriptionChecked(true);
    };

    checkPayment();
  }, []);

  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [musicFile, setMusicFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('cinematic');
  const [targetDuration, setTargetDuration] = useState<number>(30);
  const [transitionStyle, setTransitionStyle] = useState('mixed');
  const [hookStyle, setHookStyle] = useState('best-shot');
  const [outputFormat, setOutputFormat] = useState('reels');
  const [exportQuality, setExportQuality] = useState('1080p');
  const [stage, setStage] = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [API, setAPI] = useState('');
  const [apiReady, setApiReady] = useState(false);

  const videoInputRef = useRef<HTMLInputElement>(null);
  const musicInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    apiBase().then(base => {
      setAPI(base);
      setApiReady(true);
    });
  }, []);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError('');
    let files = Array.from(e.target.files || []);
    if (files.length > 8) {
      setError('Maximum 8 videos per edit');
      files = files.slice(0, 8);
    }
    setVideoFiles(files);
  };

  const handleMusicSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError('');
    const file = Array.from(e.target.files || [])[0] || null;
    setMusicFile(file);
  };

  const startPolling = (id: string) => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/status/${id}`, { headers: HEADERS });
        const data = await res.json();

        setProgress(data.progress ?? 0);
        setStatusMsg(data.stage ?? data.status ?? 'Processing…');

        if (data.status === 'completed' || data.status === 'done') {
          if (pollRef.current) clearInterval(pollRef.current);
          setStage('done');
          setProgress(100);
          setStatusMsg('Done');
        } else if (data.status === 'failed' || data.status === 'error') {
          if (pollRef.current) clearInterval(pollRef.current);
          setStage('error');
          setError(data.error || 'Edit failed');
        }
      } catch {
        // transient polling issues are ignored
      }
    }, 2000);
  };

  const handleSubmit = async () => {
    if (videoFiles.length === 0) {
      setError('Select at least one video');
      return;
    }

    if (!prompt.trim()) {
      setError('Describe the edit you want');
      return;
    }

    setError('');
    setStage('uploading');
    setProgress(0);
    setStatusMsg('Uploading files…');

    try {
      const form = new FormData();
      videoFiles.forEach(file => form.append('files', file));
      if (musicFile) form.append('files', musicFile);

      const controller = new AbortController();
      const uploadTimeout = setTimeout(() => controller.abort(), 600000);

      let upRes: Response;
      try {
        upRes = await fetch(`${API}/upload`, {
          method: 'POST',
          headers: HEADERS,
          body: form,
          signal: controller.signal,
        });
      } finally {
        clearTimeout(uploadTimeout);
      }

      if (!upRes.ok) {
        throw new Error(`Upload failed (${upRes.status}) — try with smaller files or fewer clips`);
      }

      const upData = await upRes.json();
      const id = upData.job_id;
      setJobId(id);

      setStage('editing');
      setStatusMsg('Creating your reel…');

      const editRes = await fetch(`${API}/edit`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: id,
          prompt: `${prompt.trim()}\n\nOpening hook preference: ${hookStyle}. Prioritize this in the first 1-2 seconds.`,
          target_duration: targetDuration,
          style: selectedStyle,
          export_quality: exportQuality,
          output_format: outputFormat,
          transition_style: transitionStyle,
          frame_analysis: true,
        }),
      });

      if (!editRes.ok) {
        throw new Error(`Edit request failed (${editRes.status})`);
      }

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
    setVideoFiles([]);
    setMusicFile(null);
    setPrompt('');
    setSelectedStyle('cinematic');
    setTargetDuration(30);
    setTransitionStyle('mixed');
    setHookStyle('best-shot');
    setOutputFormat('reels');
    setExportQuality('1080p');
    setStage('idle');
    setProgress(0);
    setStatusMsg('');
    setJobId(null);
    setError('');
    if (pollRef.current) clearInterval(pollRef.current);
  };

  const isWorking = stage === 'uploading' || stage === 'editing' || stage === 'polling';
  const { user } = useAuth();

  if (!subscriptionChecked || !user) {
    return (
      <div style={{ minHeight: '100vh', background: '#0A0F1E' }} />
    );
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#0A0F1E',
        color: '#fff',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        padding: '20px',
        paddingBottom: '120px',
      }}
    >
      <nav
        style={{
          display: 'flex',
          gap: 0,
          marginBottom: 32,
          borderRadius: 14,
          overflow: 'hidden',
          border: '1px solid rgba(0,170,255,0.15)',
          position: 'relative',
        }}
      >
        {apiReady && (
          <div
            style={{
              position: 'absolute',
              top: 4,
              right: 8,
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              fontSize: 10,
              color: '#556677',
              zIndex: 10,
            }}
          >
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: isRailwayActive() ? '#00FF88' : '#FFD700',
              }}
            />
            {isRailwayActive() ? 'Railway' : 'ngrok'}
          </div>
        )}

        <div
          style={{
            flex: 1,
            padding: '14px 0',
            textAlign: 'center',
            background: '#00AAFF',
            color: '#fff',
            fontWeight: 700,
            fontSize: 15,
            borderRight: '1px solid rgba(0,170,255,0.15)',
          }}
        >
          ✂️ Edit
        </div>
        <Link
          href="/generate"
          style={{
            flex: 1,
            padding: '14px 0',
            textAlign: 'center',
            textDecoration: 'none',
            background: '#0D1526',
            color: '#8899BB',
            fontWeight: 600,
            fontSize: 15,
            borderRight: '1px solid rgba(0,170,255,0.15)',
          }}
        >
          ✨ Generate
        </Link>
        <Link
          href="/captions"
          style={{
            flex: 1,
            padding: '14px 0',
            textAlign: 'center',
            textDecoration: 'none',
            background: '#0D1526',
            color: '#8899BB',
            fontWeight: 600,
            fontSize: 15,
            borderRight: '1px solid rgba(0,170,255,0.15)',
          }}
        >
          💬 Captions
        </Link>
        <Link
          href="/clipper"
          style={{
            flex: 1,
            padding: '14px 0',
            textAlign: 'center',
            textDecoration: 'none',
            background: '#0D1526',
            color: '#8899BB',
            fontWeight: 600,
            fontSize: 15,
          }}
        >
          🎬 Clipper
        </Link>
      </nav>

      <div style={{ maxWidth: 760, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <h1 style={{ fontSize: 34, fontWeight: 800, margin: 0, color: '#fff' }}>
            Turn clips into a great reel
          </h1>
          <p style={{ color: '#8EA2C8', fontSize: 17, marginTop: 12, lineHeight: 1.5 }}>
            Upload your footage, describe the vibe, and Tubee handles the edit.
          </p>
        </div>

        <div
          style={{
            background: 'linear-gradient(180deg, rgba(13,21,38,0.98), rgba(10,15,30,0.98))',
            border: '1px solid rgba(0,170,255,0.18)',
            borderRadius: 24,
            padding: 24,
            boxShadow: '0 20px 80px rgba(0,0,0,0.35)',
          }}
        >
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
              width: '100%',
              padding: '24px',
              marginBottom: 14,
              background: videoFiles.length > 0 ? 'rgba(0,170,255,0.1)' : '#0D1526',
              border: videoFiles.length > 0 ? '2px solid #00AAFF' : '2px dashed rgba(0,170,255,0.35)',
              borderRadius: 18,
              color: '#fff',
              fontSize: 20,
              fontWeight: 700,
              cursor: isWorking ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            {videoFiles.length === 0 ? '📹 Select Videos (max 8)' : `✅ ${videoFiles.length}/8 videos selected`}
          </button>

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
              width: '100%',
              padding: '18px',
              marginBottom: 18,
              background: musicFile ? 'rgba(0,170,255,0.1)' : '#0D1526',
              border: musicFile ? '2px solid #00AAFF' : '1px solid rgba(0,170,255,0.18)',
              borderRadius: 18,
              color: musicFile ? '#DDF5FF' : '#A9B8D0',
              fontSize: 17,
              fontWeight: 600,
              cursor: isWorking ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            {musicFile ? `🎵 ${musicFile.name}` : '🎵 Add Music (optional)'}
          </button>

          <div style={{ marginBottom: 18 }}>
            <div style={{ color: '#8EA2C8', fontSize: 13, marginBottom: 10, fontWeight: 600 }}>Quick start</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
              {PROMPT_TEMPLATES.map((template) => (
                <button
                  key={template.label}
                  type="button"
                  onClick={() => setPrompt(template.prompt)}
                  disabled={isWorking}
                  style={{
                    padding: '10px 14px',
                    borderRadius: 999,
                    border: '1px solid rgba(166,255,77,0.22)',
                    background: 'rgba(166,255,77,0.08)',
                    color: '#D9FFAF',
                    fontSize: 13,
                    fontWeight: 700,
                    cursor: isWorking ? 'not-allowed' : 'pointer',
                  }}
                >
                  {template.label}
                </button>
              ))}
            </div>

            <div style={{ color: '#8EA2C8', fontSize: 13, marginBottom: 10, fontWeight: 600 }}>Style</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              {STYLE_OPTIONS.map((option) => {
                const active = selectedStyle === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setSelectedStyle(option.value)}
                    disabled={isWorking}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 999,
                      border: active ? '1px solid #00AAFF' : '1px solid rgba(0,170,255,0.18)',
                      background: active ? 'rgba(0,170,255,0.12)' : '#0D1526',
                      color: active ? '#DDF5FF' : '#8EA2C8',
                      fontSize: 14,
                      fontWeight: 700,
                      cursor: isWorking ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>

            <div style={{ color: '#8EA2C8', fontSize: 13, marginBottom: 10, fontWeight: 600 }}>Target length</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              {DURATION_OPTIONS.map((option) => {
                const active = targetDuration === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setTargetDuration(option.value)}
                    disabled={isWorking}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 999,
                      border: active ? '1px solid #00AAFF' : '1px solid rgba(0,170,255,0.18)',
                      background: active ? 'rgba(0,170,255,0.12)' : '#0D1526',
                      color: active ? '#DDF5FF' : '#8EA2C8',
                      fontSize: 14,
                      fontWeight: 700,
                      cursor: isWorking ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>

            <div style={{ color: '#8EA2C8', fontSize: 13, marginBottom: 10, fontWeight: 600 }}>Transition feel</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              {TRANSITION_OPTIONS.map((option) => {
                const active = transitionStyle === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setTransitionStyle(option.value)}
                    disabled={isWorking}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 999,
                      border: active ? '1px solid #00AAFF' : '1px solid rgba(0,170,255,0.18)',
                      background: active ? 'rgba(0,170,255,0.12)' : '#0D1526',
                      color: active ? '#DDF5FF' : '#8EA2C8',
                      fontSize: 14,
                      fontWeight: 700,
                      cursor: isWorking ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>

            <div style={{ color: '#8EA2C8', fontSize: 13, marginBottom: 10, fontWeight: 600 }}>Opening hook</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              {HOOK_OPTIONS.map((option) => {
                const active = hookStyle === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setHookStyle(option.value)}
                    disabled={isWorking}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 999,
                      border: active ? '1px solid #A6FF4D' : '1px solid rgba(166,255,77,0.22)',
                      background: active ? 'rgba(166,255,77,0.12)' : '#0D1526',
                      color: active ? '#F2FFD8' : '#B9C7A4',
                      fontSize: 14,
                      fontWeight: 700,
                      cursor: isWorking ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>

            <div style={{ color: '#8EA2C8', fontSize: 13, marginBottom: 10, fontWeight: 600 }}>Format</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              {FORMAT_OPTIONS.map((option) => {
                const active = outputFormat === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setOutputFormat(option.value)}
                    disabled={isWorking}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 999,
                      border: active ? '1px solid #00AAFF' : '1px solid rgba(0,170,255,0.18)',
                      background: active ? 'rgba(0,170,255,0.12)' : '#0D1526',
                      color: active ? '#DDF5FF' : '#8EA2C8',
                      fontSize: 14,
                      fontWeight: 700,
                      cursor: isWorking ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>

            <div style={{ color: '#8EA2C8', fontSize: 13, marginBottom: 10, fontWeight: 600 }}>Quality</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
              {QUALITY_OPTIONS.map((option) => {
                const active = exportQuality === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setExportQuality(option.value)}
                    disabled={isWorking}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 999,
                      border: active ? '1px solid #00AAFF' : '1px solid rgba(0,170,255,0.18)',
                      background: active ? 'rgba(0,170,255,0.12)' : '#0D1526',
                      color: active ? '#DDF5FF' : '#8EA2C8',
                      fontSize: 14,
                      fontWeight: 700,
                      cursor: isWorking ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>

          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Describe your edit... e.g. 'Fast 20-second Instagram Reel, energetic cuts, hook at the start'"
            disabled={isWorking}
            rows={6}
            style={{
              width: '100%',
              padding: 20,
              marginBottom: 8,
              background: '#09111F',
              border: '1px solid rgba(0,170,255,0.18)',
              borderRadius: 18,
              color: '#fff',
              fontSize: 17,
              lineHeight: 1.6,
              resize: 'vertical',
              outline: 'none',
              boxSizing: 'border-box',
              fontFamily: 'inherit',
              minHeight: 170,
            }}
          />

          <div style={{ color: '#6E84AA', fontSize: 13, marginBottom: 18, lineHeight: 1.5 }}>
            Quick tip: strongest short-form edits open with the best shot in the first second, use 1-3 second cuts, and add a reveal, freeze, or zoom moment to reset attention.
          </div>

          {error && (
            <div
              style={{
                background: 'rgba(255, 80, 80, 0.1)',
                border: '1px solid rgba(255, 80, 80, 0.45)',
                borderRadius: 14,
                padding: 14,
                marginBottom: 16,
                color: '#FF9A9A',
                fontSize: 14,
              }}
            >
              ⚠️ {error}
            </div>
          )}

          {isWorking && (
            <div style={{ marginBottom: 18 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: 8,
                  fontSize: 14,
                }}
              >
                <span style={{ color: '#7CD8FF' }}>{statusMsg}</span>
                <span style={{ color: '#8EA2C8' }}>{progress}%</span>
              </div>
              <div
                style={{
                  width: '100%',
                  height: 10,
                  background: '#09111F',
                  borderRadius: 999,
                  overflow: 'hidden',
                  border: '1px solid rgba(0,170,255,0.12)',
                }}
              >
                <div
                  style={{
                    width: `${Math.max(progress, 4)}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, #00AAFF, #A6FF4D)',
                    borderRadius: 999,
                    transition: 'width 0.5s ease',
                  }}
                />
              </div>
            </div>
          )}

          {stage === 'done' ? (
            <div>
              <button
                onClick={handleDownload}
                style={{
                  width: '100%',
                  padding: 20,
                  background: 'linear-gradient(90deg, #00AAFF, #A6FF4D)',
                  color: '#06101D',
                  border: 'none',
                  borderRadius: 18,
                  fontSize: 20,
                  fontWeight: 800,
                  cursor: 'pointer',
                  marginBottom: 12,
                  boxShadow: '0 18px 40px rgba(0,170,255,0.24)',
                }}
              >
                ⬇️ Download Video
              </button>
              <button
                onClick={handleReset}
                style={{
                  width: '100%',
                  padding: 15,
                  background: 'transparent',
                  color: '#8EA2C8',
                  border: '1px solid rgba(0,170,255,0.18)',
                  borderRadius: 16,
                  fontSize: 15,
                  cursor: 'pointer',
                }}
              >
                Start New Edit
              </button>
            </div>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isWorking || videoFiles.length === 0 || !prompt.trim()}
              style={{
                width: '100%',
                padding: 22,
                background:
                  isWorking || videoFiles.length === 0 || !prompt.trim()
                    ? '#1A2740'
                    : 'linear-gradient(90deg, #00AAFF, #A6FF4D)',
                color: isWorking || videoFiles.length === 0 || !prompt.trim() ? '#5E7496' : '#06101D',
                border: 'none',
                borderRadius: 18,
                fontSize: 21,
                fontWeight: 800,
                cursor: isWorking || videoFiles.length === 0 || !prompt.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
                boxShadow:
                  !isWorking && videoFiles.length > 0 && prompt.trim()
                    ? '0 18px 40px rgba(0,170,255,0.24)'
                    : 'none',
              }}
            >
              {isWorking ? '⏳ Creating Edit…' : 'Create Edit'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
