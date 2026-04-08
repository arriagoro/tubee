'use client';
import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';
import { apiBase, SKIP_NGROK } from '@/lib/api';
const HEADERS = SKIP_NGROK;
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
const VIDEO_STYLES = [
  { label: '⭐ Veo 3.1', value: 'cinematic', icon: '🎬', badge: 'Best Quality' },
  { label: 'Action', value: 'action', icon: '⚡', badge: null },
  { label: 'Vlog', value: 'vlog', icon: '📹', badge: null },
  { label: 'Music Video', value: 'music_video', icon: '🎵', badge: null },
  { label: 'Documentary', value: 'documentary', icon: '🎥', badge: null },
];
const IMAGE_STYLES = [
  { label: 'Photorealistic', value: 'photorealistic' },
  { label: 'Digital Art', value: 'digital art' },
  { label: 'Cinematic', value: 'cinematic' },
  { label: 'Anime', value: 'anime' },
  { label: 'Watercolor', value: 'watercolor' },
];
type Stage = 'idle' | 'generating' | 'polling' | 'done' | 'error';
type Tab = 'video' | 'image' | 'music';
type VideoMode = 'text-to-video' | 'image-to-video';
export default function GeneratePage() {
  const [activeTab, setActiveTab] = useState<Tab>('video');
  const [videoMode, setVideoMode] = useState<VideoMode>('text-to-video');
  // Video state
  const [prompt, setPrompt] = useState('');
  const [duration, setDuration] = useState(8);
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [style, setStyle] = useState('cinematic');
  const [stage, setStage] = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState('');
  // Image-to-Video state
  const [i2vImage, setI2vImage] = useState<File | null>(null);
  const [i2vPreview, setI2vPreview] = useState<string | null>(null);
  const [i2vPrompt, setI2vPrompt] = useState('');
  const [i2vDuration, setI2vDuration] = useState(5);
  const [i2vAspect, setI2vAspect] = useState('9:16');
  const [i2vStyle, setI2vStyle] = useState('cinematic');
  const [i2vStage, setI2vStage] = useState<Stage>('idle');
  const [i2vProgress, setI2vProgress] = useState(0);
  const [i2vStatusMsg, setI2vStatusMsg] = useState('');
  const [i2vJobId, setI2vJobId] = useState<string | null>(null);
  const [i2vError, setI2vError] = useState('');
  const i2vFileRef = useRef<HTMLInputElement>(null);
  // Image state
  const [imagePrompt, setImagePrompt] = useState('');
  const [imageStyle, setImageStyle] = useState('photorealistic');
  const [imageAspect, setImageAspect] = useState('9:16');
  const [imageStage, setImageStage] = useState<Stage>('idle');
  const [imageProgress, setImageProgress] = useState(0);
  const [imageStatusMsg, setImageStatusMsg] = useState('');
  const [imageJobId, setImageJobId] = useState<string | null>(null);
  const [imageError, setImageError] = useState('');
  // Music state
  const [musicPrompt, setMusicPrompt] = useState('');
  const [musicDuration, setMusicDuration] = useState(30);
  const [musicStage, setMusicStage] = useState<Stage>('idle');
  const [musicProgress, setMusicProgress] = useState(0);
  const [musicStatusMsg, setMusicStatusMsg] = useState('');
  const [musicJobId, setMusicJobId] = useState<string | null>(null);
  const [musicError, setMusicError] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { user } = useAuth();
  const [API, setAPI] = useState('');
  useEffect(() => {
    apiBase().then(base => setAPI(base));
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);
  const startPolling = (id: string, type: Tab | 'i2v') => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/status/${id}`, { headers: HEADERS });
        const data = await res.json();
        const setters = {
          video: { setProgress, setStatusMsg, setStage },
          image: { setProgress: setImageProgress, setStatusMsg: setImageStatusMsg, setStage: setImageStage },
          music: { setProgress: setMusicProgress, setStatusMsg: setMusicStatusMsg, setStage: setMusicStage },
          i2v: { setProgress: setI2vProgress, setStatusMsg: setI2vStatusMsg, setStage: setI2vStage },
        }[type];
        setters.setProgress(data.progress ?? 0);
        setters.setStatusMsg(data.stage ?? data.status ?? '');
        if (data.status === 'completed' || data.status === 'done') {
          if (pollRef.current) clearInterval(pollRef.current);
          setters.setStage('done');
          setters.setProgress(100);
          // trial check removed)
        } else if (data.status === 'failed' || data.status === 'error') {
          if (pollRef.current) clearInterval(pollRef.current);
          setters.setStage('error');
          if (type === 'video') setError(data.error || 'Generation failed');
          if (type === 'image') setImageError(data.error || 'Generation failed');
          if (type === 'music') setMusicError(data.error || 'Generation failed');
          if (type === 'i2v') setI2vError(data.error || 'Generation failed');
        }
      } catch {
        // keep polling
      }
    }, 3000);
  };
  // Video generation
  const handleGenerate = async () => {
    if (!prompt.trim()) { setError('Enter a prompt describing the video'); return; }
    // trial check removed
    setError('');
    setStage('generating');
    setProgress(0);
    setStatusMsg('Submitting to Veo 3.1…');
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
      setStatusMsg('Veo 3.1 is generating your video…');
      startPolling(data.job_id, 'video');
    } catch (err: unknown) {
      setStage('error');
      setError(err instanceof Error ? err.message : 'Something went wrong');
    }
  };
  // Image generation
  const handleGenerateImage = async () => {
    if (!imagePrompt.trim()) { setImageError('Enter a prompt describing the image'); return; }
    // trial check removed
    setImageError('');
    setImageStage('generating');
    setImageProgress(0);
    setImageStatusMsg('Submitting to Imagen 4.0…');
    try {
      const res = await fetch(`${API}/generate-image`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: imagePrompt, style: imageStyle, aspect_ratio: imageAspect }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      setImageJobId(data.job_id);
      setImageStage('polling');
      setImageStatusMsg('Imagen 4.0 is generating your image…');
      startPolling(data.job_id, 'image');
    } catch (err: unknown) {
      setImageStage('error');
      setImageError(err instanceof Error ? err.message : 'Something went wrong');
    }
  };
  // Music generation
  const handleGenerateMusic = async () => {
    if (!musicPrompt.trim()) { setMusicError('Enter a prompt describing the music'); return; }
    // trial check removed
    setMusicError('');
    setMusicStage('generating');
    setMusicProgress(0);
    setMusicStatusMsg('Submitting to Lyria 3 Pro…');
    try {
      const res = await fetch(`${API}/generate-music`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: musicPrompt, duration: musicDuration }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      setMusicJobId(data.job_id);
      setMusicStage('polling');
      setMusicStatusMsg('Lyria 3 Pro is generating your music…');
      startPolling(data.job_id, 'music');
    } catch (err: unknown) {
      setMusicStage('error');
      setMusicError(err instanceof Error ? err.message : 'Something went wrong');
    }
  };
  // Image-to-Video: handle image upload
  const handleI2vImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setI2vImage(file);
    const url = URL.createObjectURL(file);
    setI2vPreview(url);
  };

  // Image-to-Video generation
  const handleGenerateI2v = async () => {
    if (!i2vImage) { setI2vError('Upload an image first'); return; }
    setI2vError('');
    setI2vStage('generating');
    setI2vProgress(0);
    setI2vStatusMsg('Submitting to Kling AI…');
    try {
      const formData = new FormData();
      formData.append('image', i2vImage);
      formData.append('prompt', i2vPrompt);
      formData.append('duration', String(i2vDuration));
      formData.append('style', i2vStyle);
      formData.append('aspect_ratio', i2vAspect);
      const res = await fetch(`${API}/generate-image-to-video`, {
        method: 'POST',
        headers: { ...HEADERS },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(err.detail || `Request failed (${res.status})`);
      }
      const data = await res.json();
      setI2vJobId(data.job_id);
      setI2vStage('polling');
      setI2vStatusMsg('Kling AI is generating your video from image…');
      startPolling(data.job_id, 'i2v');
    } catch (err: unknown) {
      setI2vStage('error');
      setI2vError(err instanceof Error ? err.message : 'Something went wrong');
    }
  };

  const handleDownload = (id: string | null, prefix: string) => {
    if (!id) return;
    const a = document.createElement('a');
    a.href = `${API}/download/${id}`;
    a.download = `tubee-${prefix}-${id.slice(0, 8)}`;
    a.click();
  };
  const isVideoWorking = stage === 'generating' || stage === 'polling';
  const isImageWorking = imageStage === 'generating' || imageStage === 'polling';
  const isMusicWorking = musicStage === 'generating' || musicStage === 'polling';
  const isI2vWorking = i2vStage === 'generating' || i2vStage === 'polling';
  const tabStyle = (active: boolean) => ({
    flex: 1, padding: '10px 4px', textAlign: 'center' as const, border: 'none',
    background: active ? 'rgba(0,170,255,0.15)' : 'transparent',
    color: active ? '#00AAFF' : '#8899BB', fontWeight: active ? 700 : 500,
    fontSize: 14, cursor: 'pointer', borderBottom: active ? '2px solid #00AAFF' : '2px solid transparent',
    transition: 'all 0.15s',
  });
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
        <Link href="/clipper" style={{
          flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
          background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
          borderRight: '1px solid rgba(0,170,255,0.15)',
        }}>
          🎬 Clipper
        </Link>
      </nav>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 20 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, color: '#00AAFF' }}>
          ✨ AI Generator
        </h1>
        <p style={{ color: '#8899BB', fontSize: 14, marginTop: 4 }}>
          Powered by Google Veo 3.1, Imagen 4.0 & Lyria 3 Pro
        </p>
      </div>
      {/* Trial Banner & Upgrade Modal */}
      
      
      {/* Sub-tabs: Video | Image | Music */}
      <div style={{
        display: 'flex', gap: 0, marginBottom: 24, borderRadius: 10,
        overflow: 'hidden', border: '1px solid rgba(0,170,255,0.12)',
      }}>
        <button onClick={() => setActiveTab('video')} style={tabStyle(activeTab === 'video')}>
          🎬 Video
        </button>
        <button onClick={() => setActiveTab('image')} style={tabStyle(activeTab === 'image')}>
          🖼️ Image
        </button>
        <button onClick={() => setActiveTab('music')} style={tabStyle(activeTab === 'music')}>
          🎵 Music
        </button>
      </div>
      {/* ══════════════════════════════════════════════════ */}
      {/* VIDEO TAB */}
      {/* ══════════════════════════════════════════════════ */}
      {activeTab === 'video' && (
        <>
          {/* Video Mode Toggle: Text to Video | Image to Video */}
          <div style={{
            display: 'flex', gap: 0, marginBottom: 16, borderRadius: 10,
            overflow: 'hidden', border: '1px solid rgba(0,170,255,0.12)',
          }}>
            <button
              onClick={() => setVideoMode('text-to-video')}
              style={{
                flex: 1, padding: '10px 4px', textAlign: 'center', border: 'none',
                background: videoMode === 'text-to-video' ? 'rgba(0,170,255,0.15)' : 'transparent',
                color: videoMode === 'text-to-video' ? '#00AAFF' : '#8899BB',
                fontWeight: videoMode === 'text-to-video' ? 700 : 500,
                fontSize: 14, cursor: 'pointer',
                borderBottom: videoMode === 'text-to-video' ? '2px solid #00AAFF' : '2px solid transparent',
                transition: 'all 0.15s',
              }}
            >
              ✍️ Text to Video
            </button>
            <button
              onClick={() => setVideoMode('image-to-video')}
              style={{
                flex: 1, padding: '10px 4px', textAlign: 'center', border: 'none',
                background: videoMode === 'image-to-video' ? 'rgba(0,170,255,0.15)' : 'transparent',
                color: videoMode === 'image-to-video' ? '#00AAFF' : '#8899BB',
                fontWeight: videoMode === 'image-to-video' ? 700 : 500,
                fontSize: 14, cursor: 'pointer',
                borderBottom: videoMode === 'image-to-video' ? '2px solid #00AAFF' : '2px solid transparent',
                transition: 'all 0.15s',
              }}
            >
              📸 Image to Video
            </button>
          </div>

          {/* ── IMAGE TO VIDEO MODE ── */}
          {videoMode === 'image-to-video' && (
            <>
              {/* Provider badge */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                marginBottom: 16, padding: '10px 14px',
                background: 'rgba(0,170,255,0.08)', borderRadius: 10,
                border: '1px solid rgba(0,170,255,0.2)',
              }}>
                <span style={{ fontSize: 18 }}>📸</span>
                <span style={{ color: '#00AAFF', fontWeight: 700, fontSize: 15 }}>Kling AI</span>
                <span style={{
                  fontSize: 11, fontWeight: 700, padding: '2px 8px',
                  borderRadius: 6, background: 'rgba(0,170,255,0.2)', color: '#00D4FF',
                }}>Image to Video</span>
              </div>

              {/* Image Upload */}
              <input
                type="file"
                ref={i2vFileRef}
                accept="image/jpeg,image/png,image/webp"
                style={{ display: 'none' }}
                onChange={handleI2vImageUpload}
              />
              <button
                onClick={() => i2vFileRef.current?.click()}
                disabled={isI2vWorking}
                style={{
                  width: '100%', padding: i2vPreview ? '12px' : '40px 16px',
                  marginBottom: 16,
                  background: '#0D1526', border: '2px dashed rgba(0,170,255,0.3)',
                  borderRadius: 12, color: '#8899BB', fontSize: 16,
                  cursor: isI2vWorking ? 'not-allowed' : 'pointer',
                  transition: 'all 0.15s', textAlign: 'center',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                }}
              >
                {i2vPreview ? (
                  <>
                    <img
                      src={i2vPreview}
                      alt="Upload preview"
                      style={{
                        maxWidth: '100%', maxHeight: 200, borderRadius: 8,
                        objectFit: 'contain',
                      }}
                    />
                    <span style={{ fontSize: 13, color: '#556677' }}>
                      {i2vImage?.name} — tap to change
                    </span>
                  </>
                ) : (
                  <>
                    <span style={{ fontSize: 32 }}>📸</span>
                    <span>Upload Image</span>
                    <span style={{ fontSize: 12, color: '#556677' }}>JPG, PNG, or WebP</span>
                  </>
                )}
              </button>

              {/* Prompt */}
              <textarea
                value={i2vPrompt}
                onChange={e => setI2vPrompt(e.target.value)}
                placeholder="Describe how to animate this image…&#10;&#10;e.g. Slow zoom in, clouds moving in the background, gentle camera pan to the right"
                disabled={isI2vWorking}
                rows={3}
                style={{
                  width: '100%', padding: 16, marginBottom: 20,
                  background: '#0D1526', border: '1px solid rgba(0,170,255,0.15)', borderRadius: 12,
                  color: '#fff', fontSize: 16, resize: 'vertical',
                  outline: 'none', boxSizing: 'border-box',
                  fontFamily: 'inherit', lineHeight: 1.5,
                }}
              />

              {/* Duration */}
              <div style={{ marginBottom: 20 }}>
                <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>DURATION</p>
                <div style={{ display: 'flex', gap: 8 }}>
                  {[{ label: '5s', value: 5, desc: 'Standard' }, { label: '10s', value: 10, desc: 'Extended' }].map(d => (
                    <button
                      key={d.value}
                      onClick={() => setI2vDuration(d.value)}
                      disabled={isI2vWorking}
                      style={{
                        flex: 1, padding: '12px 8px', borderRadius: 12, border: 'none',
                        background: i2vDuration === d.value ? '#00AAFF' : '#0D1526',
                        color: i2vDuration === d.value ? '#fff' : '#8899BB',
                        fontSize: 15, fontWeight: i2vDuration === d.value ? 700 : 500,
                        cursor: isI2vWorking ? 'not-allowed' : 'pointer',
                        transition: 'all 0.15s',
                      }}
                    >
                      <div>{d.label}</div>
                      <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>{d.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Format */}
              <div style={{ marginBottom: 20 }}>
                <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>FORMAT</p>
                <div style={{ display: 'flex', gap: 8 }}>
                  {ASPECT_RATIOS.map(ar => (
                    <button
                      key={ar.label}
                      onClick={() => setI2vAspect(ar.label)}
                      disabled={isI2vWorking}
                      style={{
                        flex: 1, padding: '12px 8px', borderRadius: 12, border: 'none',
                        background: i2vAspect === ar.label ? '#00AAFF' : '#0D1526',
                        color: i2vAspect === ar.label ? '#fff' : '#8899BB',
                        fontSize: 14, fontWeight: i2vAspect === ar.label ? 700 : 500,
                        cursor: isI2vWorking ? 'not-allowed' : 'pointer',
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

              {/* Style */}
              <div style={{ marginBottom: 24 }}>
                <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>STYLE</p>
                <div style={{
                  display: 'flex', gap: 8, overflowX: 'auto',
                  paddingBottom: 8, WebkitOverflowScrolling: 'touch',
                }}>
                  {VIDEO_STYLES.map(s => (
                    <button
                      key={s.value}
                      onClick={() => setI2vStyle(s.value)}
                      disabled={isI2vWorking}
                      style={{
                        flexShrink: 0, padding: '10px 18px',
                        borderRadius: 99, border: 'none',
                        background: i2vStyle === s.value ? '#00AAFF' : '#0D1526',
                        color: i2vStyle === s.value ? '#fff' : '#8899BB',
                        fontSize: 14, fontWeight: i2vStyle === s.value ? 700 : 500,
                        cursor: isI2vWorking ? 'not-allowed' : 'pointer',
                        transition: 'all 0.15s',
                        display: 'flex', alignItems: 'center', gap: 6,
                      }}
                    >
                      {s.icon} {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Error */}
              {i2vError && (
                <div style={{
                  background: '#2a0a0a', border: '1px solid #f44', borderRadius: 12,
                  padding: 14, marginBottom: 16, color: '#f88', fontSize: 14,
                }}>
                  ⚠️ {i2vError}
                </div>
              )}

              {/* Progress */}
              {isI2vWorking && (
                <div style={{ marginBottom: 20 }}>
                  <div style={{
                    display: 'flex', justifyContent: 'space-between',
                    marginBottom: 8, fontSize: 14,
                  }}>
                    <span style={{ color: '#00AAFF' }}>{i2vStatusMsg}</span>
                    <span style={{ color: '#8899BB' }}>{i2vProgress}%</span>
                  </div>
                  <div style={{
                    width: '100%', height: 8, background: '#0D1526', borderRadius: 99,
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      width: `${Math.max(i2vProgress, 3)}%`, height: '100%',
                      background: 'linear-gradient(90deg, #00AAFF, #00D4FF)',
                      borderRadius: 99, transition: 'width 0.5s ease',
                    }} />
                  </div>
                  <p style={{ color: '#4a5a7a', fontSize: 12, marginTop: 8, textAlign: 'center' }}>
                    Image-to-video generation can take 1-5 minutes
                  </p>
                </div>
              )}

              {/* Done */}
              {i2vStage === 'done' && (
                <div style={{ textAlign: 'center', marginBottom: 20 }}>
                  <p style={{ fontSize: 20, color: '#00AAFF', fontWeight: 700, marginBottom: 16 }}>
                    🎉 Your video is ready!
                  </p>
                  <button
                    onClick={() => handleDownload(i2vJobId, 'i2v-video')}
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
                    onClick={() => {
                      setI2vImage(null); setI2vPreview(null); setI2vPrompt('');
                      setI2vStage('idle'); setI2vProgress(0);
                      setI2vStatusMsg(''); setI2vJobId(null); setI2vError('');
                    }}
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

              {/* Submit */}
              {i2vStage !== 'done' && (
                <button
                  onClick={handleGenerateI2v}
                  disabled={isI2vWorking || !i2vImage}
                  style={{
                    width: '100%', padding: 20,
                    background: isI2vWorking || !i2vImage ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                    color: isI2vWorking || !i2vImage ? '#4a5a7a' : '#fff',
                    border: 'none', borderRadius: 14,
                    fontSize: 20, fontWeight: 700,
                    cursor: isI2vWorking || !i2vImage ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s',
                    boxShadow: !isI2vWorking && i2vImage ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
                  }}
                >
                  {isI2vWorking ? '⏳ Generating with Kling AI…' : '✨ Generate Video'}
                </button>
              )}
            </>
          )}

          {/* ── TEXT TO VIDEO MODE ── */}
          {videoMode === 'text-to-video' && (<>
          {/* Provider badge */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            marginBottom: 16, padding: '10px 14px',
            background: 'rgba(0,170,255,0.08)', borderRadius: 10,
            border: '1px solid rgba(0,170,255,0.2)',
          }}>
            <span style={{ fontSize: 18 }}>⭐</span>
            <span style={{ color: '#00AAFF', fontWeight: 700, fontSize: 15 }}>Google Veo 3.1</span>
            <span style={{
              fontSize: 11, fontWeight: 700, padding: '2px 8px',
              borderRadius: 6, background: 'rgba(0,170,255,0.2)', color: '#00D4FF',
            }}>Best Quality</span>
            <span style={{ color: '#556677', fontSize: 12, marginLeft: 'auto' }}>
              + Kling, Runway, Luma fallbacks
            </span>
          </div>
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Describe the video you want to create…&#10;&#10;e.g. A cinematic drone shot flying over Miami Beach at golden hour, palm trees swaying, warm teal and orange color grade"
            disabled={isVideoWorking}
            rows={4}
            style={{
              width: '100%', padding: 16, marginBottom: 20,
              background: '#0D1526', border: '1px solid rgba(0,170,255,0.15)', borderRadius: 12,
              color: '#fff', fontSize: 16, resize: 'vertical',
              outline: 'none', boxSizing: 'border-box',
              fontFamily: 'inherit', lineHeight: 1.5,
            }}
          />
          {/* Duration */}
          <div style={{ marginBottom: 20 }}>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>DURATION</p>
            <div style={{ display: 'flex', gap: 8 }}>
              {DURATIONS.map(d => (
                <button
                  key={d.value}
                  onClick={() => setDuration(d.value)}
                  disabled={isVideoWorking}
                  style={{
                    flex: 1, padding: '12px 8px', borderRadius: 12, border: 'none',
                    background: duration === d.value ? '#00AAFF' : '#0D1526',
                    color: duration === d.value ? '#fff' : '#8899BB',
                    fontSize: 15, fontWeight: duration === d.value ? 700 : 500,
                    cursor: isVideoWorking ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  <div>{d.label}</div>
                  <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>{d.desc}</div>
                </button>
              ))}
            </div>
          </div>
          {/* Aspect Ratio */}
          <div style={{ marginBottom: 20 }}>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>FORMAT</p>
            <div style={{ display: 'flex', gap: 8 }}>
              {ASPECT_RATIOS.map(ar => (
                <button
                  key={ar.label}
                  onClick={() => setAspectRatio(ar.label)}
                  disabled={isVideoWorking}
                  style={{
                    flex: 1, padding: '12px 8px', borderRadius: 12, border: 'none',
                    background: aspectRatio === ar.label ? '#00AAFF' : '#0D1526',
                    color: aspectRatio === ar.label ? '#fff' : '#8899BB',
                    fontSize: 14, fontWeight: aspectRatio === ar.label ? 700 : 500,
                    cursor: isVideoWorking ? 'not-allowed' : 'pointer',
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
          {/* Style */}
          <div style={{ marginBottom: 24 }}>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>STYLE</p>
            <div style={{
              display: 'flex', gap: 8, overflowX: 'auto',
              paddingBottom: 8, WebkitOverflowScrolling: 'touch',
            }}>
              {VIDEO_STYLES.map(s => (
                <button
                  key={s.value}
                  onClick={() => setStyle(s.value)}
                  disabled={isVideoWorking}
                  style={{
                    flexShrink: 0, padding: '10px 18px',
                    borderRadius: 99, border: 'none',
                    background: style === s.value ? '#00AAFF' : '#0D1526',
                    color: style === s.value ? '#fff' : '#8899BB',
                    fontSize: 14, fontWeight: style === s.value ? 700 : 500,
                    cursor: isVideoWorking ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s',
                    display: 'flex', alignItems: 'center', gap: 6,
                  }}
                >
                  {s.icon} {s.label}
                  {s.badge && (
                    <span style={{
                      fontSize: 10, fontWeight: 700, padding: '2px 6px',
                      borderRadius: 6,
                      background: style === s.value ? 'rgba(255,255,255,0.2)' : 'rgba(0,170,255,0.15)',
                      color: style === s.value ? '#fff' : '#00AAFF',
                    }}>
                      {s.badge}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
          {/* Error */}
          {error && (
            <div style={{
              background: '#2a0a0a', border: '1px solid #f44', borderRadius: 12,
              padding: 14, marginBottom: 16, color: '#f88', fontSize: 14,
            }}>
              ⚠️ {error}
            </div>
          )}
          {/* Progress */}
          {isVideoWorking && (
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
                Veo 3.1 generation can take 1-5 minutes
              </p>
            </div>
          )}
          {/* Done */}
          {stage === 'done' && (
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <p style={{ fontSize: 20, color: '#00AAFF', fontWeight: 700, marginBottom: 16 }}>
                🎉 Your video is ready!
              </p>
              <button
                onClick={() => handleDownload(jobId, 'video')}
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
                onClick={() => {
                  setPrompt(''); setStage('idle'); setProgress(0);
                  setStatusMsg(''); setJobId(null); setError('');
                }}
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
          {/* Submit */}
          {stage !== 'done' && (
            <button
              onClick={handleGenerate}
              disabled={isVideoWorking || !prompt.trim()}
              style={{
                width: '100%', padding: 20,
                background: isVideoWorking || !prompt.trim() ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                color: isVideoWorking || !prompt.trim() ? '#4a5a7a' : '#fff',
                border: 'none', borderRadius: 14,
                fontSize: 20, fontWeight: 700,
                cursor: isVideoWorking || !prompt.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                boxShadow: !isVideoWorking && prompt.trim() ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
              }}
            >
              {isVideoWorking ? '⏳ Generating with Veo 3.1…' : '✨ Generate Video'}
            </button>
          )}
          </>)}
        </>
      )}
      {/* ══════════════════════════════════════════════════ */}
      {/* IMAGE TAB */}
      {/* ══════════════════════════════════════════════════ */}
      {activeTab === 'image' && (
        <>
          {/* Provider badge */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            marginBottom: 16, padding: '10px 14px',
            background: 'rgba(0,170,255,0.08)', borderRadius: 10,
            border: '1px solid rgba(0,170,255,0.2)',
          }}>
            <span style={{ fontSize: 18 }}>🖼️</span>
            <span style={{ color: '#00AAFF', fontWeight: 700, fontSize: 15 }}>Google Imagen 4.0</span>
            <span style={{
              fontSize: 11, fontWeight: 700, padding: '2px 8px',
              borderRadius: 6, background: 'rgba(0,170,255,0.2)', color: '#00D4FF',
            }}>NEW</span>
          </div>
          <textarea
            value={imagePrompt}
            onChange={e => setImagePrompt(e.target.value)}
            placeholder="Describe the image you want to create…&#10;&#10;e.g. A vibrant Miami skyline at sunset with neon reflections on the water"
            disabled={isImageWorking}
            rows={4}
            style={{
              width: '100%', padding: 16, marginBottom: 20,
              background: '#0D1526', border: '1px solid rgba(0,170,255,0.15)', borderRadius: 12,
              color: '#fff', fontSize: 16, resize: 'vertical',
              outline: 'none', boxSizing: 'border-box',
              fontFamily: 'inherit', lineHeight: 1.5,
            }}
          />
          {/* Image Style */}
          <div style={{ marginBottom: 20 }}>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>STYLE</p>
            <div style={{
              display: 'flex', gap: 8, overflowX: 'auto',
              paddingBottom: 8, WebkitOverflowScrolling: 'touch',
            }}>
              {IMAGE_STYLES.map(s => (
                <button
                  key={s.value}
                  onClick={() => setImageStyle(s.value)}
                  disabled={isImageWorking}
                  style={{
                    flexShrink: 0, padding: '10px 18px',
                    borderRadius: 99, border: 'none',
                    background: imageStyle === s.value ? '#00AAFF' : '#0D1526',
                    color: imageStyle === s.value ? '#fff' : '#8899BB',
                    fontSize: 14, fontWeight: imageStyle === s.value ? 700 : 500,
                    cursor: isImageWorking ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
          {/* Image Aspect Ratio */}
          <div style={{ marginBottom: 24 }}>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>FORMAT</p>
            <div style={{ display: 'flex', gap: 8 }}>
              {ASPECT_RATIOS.map(ar => (
                <button
                  key={ar.label}
                  onClick={() => setImageAspect(ar.label)}
                  disabled={isImageWorking}
                  style={{
                    flex: 1, padding: '12px 8px', borderRadius: 12, border: 'none',
                    background: imageAspect === ar.label ? '#00AAFF' : '#0D1526',
                    color: imageAspect === ar.label ? '#fff' : '#8899BB',
                    fontSize: 14, fontWeight: imageAspect === ar.label ? 700 : 500,
                    cursor: isImageWorking ? 'not-allowed' : 'pointer',
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
          {/* Error */}
          {imageError && (
            <div style={{
              background: '#2a0a0a', border: '1px solid #f44', borderRadius: 12,
              padding: 14, marginBottom: 16, color: '#f88', fontSize: 14,
            }}>
              ⚠️ {imageError}
            </div>
          )}
          {/* Progress */}
          {isImageWorking && (
            <div style={{ marginBottom: 20 }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                marginBottom: 8, fontSize: 14,
              }}>
                <span style={{ color: '#00AAFF' }}>{imageStatusMsg}</span>
                <span style={{ color: '#8899BB' }}>{imageProgress}%</span>
              </div>
              <div style={{
                width: '100%', height: 8, background: '#0D1526', borderRadius: 99,
                overflow: 'hidden',
              }}>
                <div style={{
                  width: `${Math.max(imageProgress, 3)}%`, height: '100%',
                  background: 'linear-gradient(90deg, #00AAFF, #00D4FF)',
                  borderRadius: 99, transition: 'width 0.5s ease',
                }} />
              </div>
            </div>
          )}
          {/* Done */}
          {imageStage === 'done' && (
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <p style={{ fontSize: 20, color: '#00AAFF', fontWeight: 700, marginBottom: 16 }}>
                🎉 Your image is ready!
              </p>
              <button
                onClick={() => handleDownload(imageJobId, 'image')}
                style={{
                  width: '100%', padding: 18,
                  background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                  color: '#fff', border: 'none', borderRadius: 14,
                  fontSize: 18, fontWeight: 700, cursor: 'pointer',
                  marginBottom: 12,
                  boxShadow: '0 0 20px rgba(0,170,255,0.3)',
                }}
              >
                ⬇️ Download Image
              </button>
              <button
                onClick={() => {
                  setImagePrompt(''); setImageStage('idle'); setImageProgress(0);
                  setImageStatusMsg(''); setImageJobId(null); setImageError('');
                }}
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
          {/* Submit */}
          {imageStage !== 'done' && (
            <button
              onClick={handleGenerateImage}
              disabled={isImageWorking || !imagePrompt.trim()}
              style={{
                width: '100%', padding: 20,
                background: isImageWorking || !imagePrompt.trim() ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                color: isImageWorking || !imagePrompt.trim() ? '#4a5a7a' : '#fff',
                border: 'none', borderRadius: 14,
                fontSize: 20, fontWeight: 700,
                cursor: isImageWorking || !imagePrompt.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                boxShadow: !isImageWorking && imagePrompt.trim() ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
              }}
            >
              {isImageWorking ? '⏳ Generating with Imagen 4.0…' : '🖼️ Generate Image'}
            </button>
          )}
        </>
      )}
      {/* ══════════════════════════════════════════════════ */}
      {/* MUSIC TAB */}
      {/* ══════════════════════════════════════════════════ */}
      {activeTab === 'music' && (
        <>
          {/* Provider badge */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            marginBottom: 16, padding: '10px 14px',
            background: 'rgba(0,170,255,0.08)', borderRadius: 10,
            border: '1px solid rgba(0,170,255,0.2)',
          }}>
            <span style={{ fontSize: 18 }}>🎵</span>
            <span style={{ color: '#00AAFF', fontWeight: 700, fontSize: 15 }}>Google Lyria 3 Pro</span>
            <span style={{
              fontSize: 11, fontWeight: 700, padding: '2px 8px',
              borderRadius: 6, background: 'rgba(0,170,255,0.2)', color: '#00D4FF',
            }}>NEW</span>
          </div>
          <textarea
            value={musicPrompt}
            onChange={e => setMusicPrompt(e.target.value)}
            placeholder="Describe the music you want…&#10;&#10;e.g. Upbeat electronic beat for a travel vlog, energetic but not overwhelming"
            disabled={isMusicWorking}
            rows={4}
            style={{
              width: '100%', padding: 16, marginBottom: 20,
              background: '#0D1526', border: '1px solid rgba(0,170,255,0.15)', borderRadius: 12,
              color: '#fff', fontSize: 16, resize: 'vertical',
              outline: 'none', boxSizing: 'border-box',
              fontFamily: 'inherit', lineHeight: 1.5,
            }}
          />
          {/* Duration */}
          <div style={{ marginBottom: 24 }}>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>DURATION</p>
            <div style={{ display: 'flex', gap: 8 }}>
              {[15, 30, 60].map(d => (
                <button
                  key={d}
                  onClick={() => setMusicDuration(d)}
                  disabled={isMusicWorking}
                  style={{
                    flex: 1, padding: '12px 8px', borderRadius: 12, border: 'none',
                    background: musicDuration === d ? '#00AAFF' : '#0D1526',
                    color: musicDuration === d ? '#fff' : '#8899BB',
                    fontSize: 15, fontWeight: musicDuration === d ? 700 : 500,
                    cursor: isMusicWorking ? 'not-allowed' : 'pointer',
                    transition: 'all 0.15s',
                  }}
                >
                  {d}s
                </button>
              ))}
            </div>
          </div>
          {/* Error */}
          {musicError && (
            <div style={{
              background: '#2a0a0a', border: '1px solid #f44', borderRadius: 12,
              padding: 14, marginBottom: 16, color: '#f88', fontSize: 14,
            }}>
              ⚠️ {musicError}
            </div>
          )}
          {/* Progress */}
          {isMusicWorking && (
            <div style={{ marginBottom: 20 }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                marginBottom: 8, fontSize: 14,
              }}>
                <span style={{ color: '#00AAFF' }}>{musicStatusMsg}</span>
                <span style={{ color: '#8899BB' }}>{musicProgress}%</span>
              </div>
              <div style={{
                width: '100%', height: 8, background: '#0D1526', borderRadius: 99,
                overflow: 'hidden',
              }}>
                <div style={{
                  width: `${Math.max(musicProgress, 3)}%`, height: '100%',
                  background: 'linear-gradient(90deg, #00AAFF, #00D4FF)',
                  borderRadius: 99, transition: 'width 0.5s ease',
                }} />
              </div>
            </div>
          )}
          {/* Done */}
          {musicStage === 'done' && (
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <p style={{ fontSize: 20, color: '#00AAFF', fontWeight: 700, marginBottom: 16 }}>
                🎉 Your music is ready!
              </p>
              <button
                onClick={() => handleDownload(musicJobId, 'music')}
                style={{
                  width: '100%', padding: 18,
                  background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                  color: '#fff', border: 'none', borderRadius: 14,
                  fontSize: 18, fontWeight: 700, cursor: 'pointer',
                  marginBottom: 12,
                  boxShadow: '0 0 20px rgba(0,170,255,0.3)',
                }}
              >
                ⬇️ Download Music
              </button>
              <button
                onClick={() => {
                  setMusicPrompt(''); setMusicStage('idle'); setMusicProgress(0);
                  setMusicStatusMsg(''); setMusicJobId(null); setMusicError('');
                }}
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
          {/* Submit */}
          {musicStage !== 'done' && (
            <button
              onClick={handleGenerateMusic}
              disabled={isMusicWorking || !musicPrompt.trim()}
              style={{
                width: '100%', padding: 20,
                background: isMusicWorking || !musicPrompt.trim() ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                color: isMusicWorking || !musicPrompt.trim() ? '#4a5a7a' : '#fff',
                border: 'none', borderRadius: 14,
                fontSize: 20, fontWeight: 700,
                cursor: isMusicWorking || !musicPrompt.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                boxShadow: !isMusicWorking && musicPrompt.trim() ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
              }}
            >
              {isMusicWorking ? '⏳ Generating with Lyria 3 Pro…' : '🎵 Generate Music'}
            </button>
          )}
        </>
      )}
    </div>
  );
}
