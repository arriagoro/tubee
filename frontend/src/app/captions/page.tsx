'use client';
import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';
import { apiBase, SKIP_NGROK } from '@/lib/api';
const HEADERS = SKIP_NGROK;
const CAPTION_STYLES = [
  {
    id: 'temitayo',
    label: 'Temitayo',
    icon: '🔵',
    desc: 'Bold electric blue, ALL CAPS',
    preview: { color: '#00AAFF', bg: '#0D1526', fontWeight: 800, textTransform: 'uppercase' as const },
  },
  {
    id: 'standard',
    label: 'Standard',
    icon: '⬜',
    desc: 'White text, black outline',
    preview: { color: '#ffffff', bg: '#0D1526', fontWeight: 600, textTransform: 'none' as const },
  },
  {
    id: 'minimal',
    label: 'Minimal',
    icon: '✨',
    desc: 'Small, clean, subtle',
    preview: { color: 'rgba(255,255,255,0.8)', bg: '#0D1526', fontWeight: 400, textTransform: 'none' as const },
  },
  {
    id: 'bold',
    label: 'Bold',
    icon: '💪',
    desc: 'Large, heavy stroke',
    preview: { color: '#ffffff', bg: '#0D1526', fontWeight: 900, textTransform: 'none' as const },
  },
];
type Stage = 'idle' | 'loading-jobs' | 'uploading' | 'processing' | 'polling' | 'done' | 'error';
interface Job {
  job_id: string;
  status: string;
  prompt: string | null;
  stage: string;
  created_at: string;
}
export default function CaptionsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [captionStyle, setCaptionStyle] = useState('temitayo');
  const [wordByWord, setWordByWord] = useState(false);
  const [stage, setStage] = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [captionJobId, setCaptionJobId] = useState<string | null>(null);
  const [error, setError] = useState('');
  // Voiceover state
  const [voText, setVoText] = useState('');
  const [voVoiceId, setVoVoiceId] = useState('');
  const [voices, setVoices] = useState<{ voice_id: string; name: string }[]>([]);
  const [voJobId, setVoJobId] = useState<string | null>(null);
  const [voStage, setVoStage] = useState<'idle' | 'generating' | 'polling' | 'done' | 'error'>('idle');
  const [voProgress, setVoProgress] = useState(0);
  const [voStatusMsg, setVoStatusMsg] = useState('');
  const [voError, setVoError] = useState('');
  const [voAttachJob, setVoAttachJob] = useState<string | null>(null);
  const { user } = useAuth();
  const [API, setAPI] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const voPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  useEffect(() => {
    apiBase().then(base => {
      setAPI(base);
      loadJobsWithBase(base);
      loadVoicesWithBase(base);
    });
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (voPollRef.current) clearInterval(voPollRef.current);
    };
  }, []);
  const loadJobsWithBase = async (base: string) => {
    try {
      const res = await fetch(`${base}/jobs`, { headers: HEADERS });
      const data = await res.json();
      const completedJobs = (data.jobs || []).filter((j: Job) => j.status === 'done');
      setJobs(completedJobs);
    } catch { /* silent */ }
  };
  const loadJobs = async () => {
    const base = await apiBase();
    await loadJobsWithBase(base);
  };
  const loadVoicesWithBase = async (base: string) => {
    try {
      const res = await fetch(`${base}/voices`, { headers: HEADERS });
      const data = await res.json();
      setVoices(data.voices || []);
    } catch { /* silent */ }
  };
  const loadVoices = async () => {
    const base = await apiBase();
    await loadVoicesWithBase(base);
  };
  const startPolling = (id: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/status/${id}`, { headers: HEADERS });
        const data = await res.json();
        setProgress(data.progress ?? 0);
        setStatusMsg(data.stage ?? data.status ?? '');
        if (data.status === 'done') {
          if (pollRef.current) clearInterval(pollRef.current);
          setStage('done');
          setProgress(100);
          // trial check removed)
        } else if (data.status === 'error') {
          if (pollRef.current) clearInterval(pollRef.current);
          setStage('error');
          setError(data.error || 'Caption generation failed');
        }
      } catch { /* keep polling */ }
    }, 3000);
  };
  const handleCaptionFromJob = async () => {
    if (!selectedJob) { setError('Select a completed video'); return; }
    // trial check removed
    setError('');
    setStage('processing');
    setProgress(0);
    setStatusMsg('Starting caption generation…');
    try {
      const res = await fetch(`${API}/captions`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: selectedJob,
          style: captionStyle,
          word_by_word: wordByWord,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to start captioning');
      setCaptionJobId(data.job_id);
      setStage('polling');
      startPolling(data.job_id);
    } catch (err: any) {
      setStage('error');
      setError(err.message || 'Failed to start captioning');
    }
  };
  const handleCaptionFromUpload = async () => {
    if (!uploadFile) { setError('Select a video file to upload'); return; }
    // trial check removed
    setError('');
    setStage('uploading');
    setProgress(0);
    setStatusMsg('Uploading video…');
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('style', captionStyle);
      formData.append('word_by_word', String(wordByWord));
      const res = await fetch(`${API}/captions/upload`, {
        method: 'POST',
        headers: HEADERS,
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setCaptionJobId(data.job_id);
      setStage('polling');
      startPolling(data.job_id);
    } catch (err: any) {
      setStage('error');
      setError(err.message || 'Upload failed');
    }
  };
  const startVoPolling = (id: string) => {
    if (voPollRef.current) clearInterval(voPollRef.current);
    voPollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/status/${id}`, { headers: HEADERS });
        const data = await res.json();
        setVoProgress(data.progress ?? 0);
        setVoStatusMsg(data.stage ?? '');
        if (data.status === 'done') {
          if (voPollRef.current) clearInterval(voPollRef.current);
          setVoStage('done');
          setVoProgress(100);
        } else if (data.status === 'error') {
          if (voPollRef.current) clearInterval(voPollRef.current);
          setVoStage('error');
          setVoError(data.error || 'Voiceover failed');
        }
      } catch { /* keep polling */ }
    }, 3000);
  };
  const handleVoiceover = async () => {
    if (!voText.trim()) { setVoError('Enter some text'); return; }
    setVoError('');
    setVoStage('generating');
    setVoProgress(0);
    setVoStatusMsg('Starting voiceover…');
    try {
      const body: any = { text: voText };
      if (voVoiceId) body.voice_id = voVoiceId;
      if (voAttachJob) body.job_id = voAttachJob;
      const res = await fetch(`${API}/voiceover`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed');
      setVoJobId(data.job_id);
      setVoStage('polling');
      startVoPolling(data.job_id);
    } catch (err: any) {
      setVoStage('error');
      setVoError(err.message || 'Failed');
    }
  };
  const resetCaptions = () => {
    setStage('idle');
    setProgress(0);
    setStatusMsg('');
    setCaptionJobId(null);
    setError('');
    setUploadFile(null);
    setSelectedJob(null);
    loadJobs();
  };
  const resetVoiceover = () => {
    setVoStage('idle');
    setVoProgress(0);
    setVoStatusMsg('');
    setVoJobId(null);
    setVoError('');
    setVoText('');
  };
  return (
    <div style={{
      minHeight: '100vh', background: '#0A0F1E', color: '#fff',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    }}>
      <div style={{ maxWidth: 520, margin: '0 auto', padding: '24px 16px 80px' }}>
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
          <div style={{
            flex: 1, padding: '14px 0', textAlign: 'center',
            background: '#00AAFF', color: '#fff', fontWeight: 700, fontSize: 15,
            borderRight: '1px solid rgba(0,170,255,0.15)',
          }}>
            💬 Captions
          </div>
          <Link href="/clipper" style={{
            flex: 1, padding: '14px 0', textAlign: 'center', textDecoration: 'none',
            background: '#0D1526', color: '#8899BB', fontWeight: 600, fontSize: 15,
            borderRight: '1px solid rgba(0,170,255,0.15)',
          }}>
            🎬 Clipper
          </Link>
        </nav>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, color: '#00AAFF' }}>
            💬 Auto-Captions
          </h1>
          <p style={{ color: '#8899BB', fontSize: 14, marginTop: 6 }}>
            Transcribe & burn captions into your video — powered by Whisper + FFmpeg
          </p>
        </div>
        {/* Trial Banner & Upgrade Modal */}
        
        
        {/* ─── CAPTIONS SECTION ──────────────────────────────── */}
        {(stage === 'idle' || stage === 'loading-jobs') && (
          <>
            {/* Source selection */}
            <div style={{
              background: '#0D1526', borderRadius: 16, padding: 20,
              border: '1px solid rgba(0,170,255,0.15)', marginBottom: 16,
            }}>
              <h3 style={{ margin: '0 0 12px', fontSize: 15, color: '#8899BB' }}>
                📹 Select Video
              </h3>
              {/* Upload option */}
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                style={{ display: 'none' }}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) { setUploadFile(f); setSelectedJob(null); }
                }}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                style={{
                  width: '100%', padding: '14px', borderRadius: 12,
                  border: uploadFile ? '2px solid #00AAFF' : '2px dashed rgba(0,170,255,0.3)',
                  background: uploadFile ? 'rgba(0,170,255,0.1)' : '#0A0F1E',
                  color: uploadFile ? '#00AAFF' : '#4a5a7a',
                  fontSize: 14, cursor: 'pointer', marginBottom: 12,
                }}
              >
                {uploadFile ? `📁 ${uploadFile.name}` : '📤 Upload a video file'}
              </button>
              {/* OR divider */}
              <div style={{
                textAlign: 'center', color: '#2a3a5a', fontSize: 12,
                margin: '8px 0', fontWeight: 600,
              }}>
                — OR select from completed jobs —
              </div>
              {/* Completed jobs */}
              <div style={{ maxHeight: 180, overflowY: 'auto' }}>
                {jobs.length === 0 ? (
                  <p style={{ color: '#3a4a6a', fontSize: 13, textAlign: 'center', padding: 12 }}>
                    No completed videos yet
                  </p>
                ) : (
                  jobs.map((j) => (
                    <button
                      key={j.job_id}
                      onClick={() => { setSelectedJob(j.job_id); setUploadFile(null); }}
                      style={{
                        width: '100%', padding: '10px 12px', borderRadius: 10,
                        border: selectedJob === j.job_id ? '2px solid #00AAFF' : '1px solid rgba(0,170,255,0.15)',
                        background: selectedJob === j.job_id ? 'rgba(0,170,255,0.1)' : '#0A0F1E',
                        color: selectedJob === j.job_id ? '#00AAFF' : '#8899BB',
                        fontSize: 13, cursor: 'pointer', marginBottom: 6,
                        textAlign: 'left', display: 'block',
                      }}
                    >
                      <span style={{ fontWeight: 600 }}>
                        {j.prompt ? j.prompt.slice(0, 50) : j.job_id.slice(0, 8)}
                      </span>
                      <span style={{ float: 'right', color: '#3a4a6a', fontSize: 11 }}>
                        {new Date(j.created_at).toLocaleDateString()}
                      </span>
                    </button>
                  ))
                )}
              </div>
            </div>
            {/* Caption style selector */}
            <div style={{
              background: '#0D1526', borderRadius: 16, padding: 20,
              border: '1px solid rgba(0,170,255,0.15)', marginBottom: 16,
            }}>
              <h3 style={{ margin: '0 0 12px', fontSize: 15, color: '#8899BB' }}>
                🎨 Caption Style
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {CAPTION_STYLES.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setCaptionStyle(s.id)}
                    style={{
                      padding: '14px 12px', borderRadius: 12, cursor: 'pointer',
                      border: captionStyle === s.id ? '2px solid #00AAFF' : '1px solid rgba(0,170,255,0.15)',
                      background: captionStyle === s.id ? 'rgba(0,170,255,0.1)' : '#0A0F1E',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ fontSize: 20, marginBottom: 4 }}>{s.icon}</div>
                    <div style={{
                      fontSize: 13, fontWeight: 700,
                      color: captionStyle === s.id ? '#00AAFF' : '#ccc',
                    }}>
                      {s.label}
                    </div>
                    <div style={{ fontSize: 11, color: '#4a5a7a', marginTop: 2 }}>{s.desc}</div>
                    {/* Preview chip */}
                    <div style={{
                      marginTop: 8, padding: '4px 8px', borderRadius: 6,
                      background: s.preview.bg, display: 'inline-block',
                      color: s.preview.color,
                      fontWeight: s.preview.fontWeight,
                      textTransform: s.preview.textTransform,
                      fontSize: 11,
                      textShadow: s.id === 'temitayo' ? '0 0 8px rgba(0,170,255,0.5)' :
                        s.id === 'bold' ? '0 0 4px rgba(0,0,0,1)' : 'none',
                    }}>
                      sample text
                    </div>
                  </button>
                ))}
              </div>
            </div>
            {/* Word-by-word toggle */}
            <div style={{
              background: '#0D1526', borderRadius: 16, padding: 16,
              border: '1px solid rgba(0,170,255,0.15)', marginBottom: 20,
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#ccc' }}>
                  🎤 Word-by-Word Mode
                </div>
                <div style={{ fontSize: 12, color: '#4a5a7a', marginTop: 2 }}>
                  Karaoke-style — one word at a time (trending!)
                </div>
              </div>
              <button
                onClick={() => setWordByWord(!wordByWord)}
                style={{
                  width: 52, height: 28, borderRadius: 14, border: 'none',
                  background: wordByWord ? '#00AAFF' : '#1a2540',
                  cursor: 'pointer', position: 'relative', transition: 'background 0.2s',
                }}
              >
                <div style={{
                  width: 22, height: 22, borderRadius: 11,
                  background: '#fff', position: 'absolute', top: 3,
                  left: wordByWord ? 27 : 3, transition: 'left 0.2s',
                }} />
              </button>
            </div>
            {/* Submit button */}
            <button
              onClick={uploadFile ? handleCaptionFromUpload : handleCaptionFromJob}
              disabled={!uploadFile && !selectedJob}
              style={{
                width: '100%', padding: 16, borderRadius: 14, border: 'none',
                background: (uploadFile || selectedJob) ? 'linear-gradient(135deg, #00AAFF, #00D4FF)' : '#1a2540',
                color: (uploadFile || selectedJob) ? '#fff' : '#4a5a7a',
                fontSize: 16, fontWeight: 700, cursor: (uploadFile || selectedJob) ? 'pointer' : 'not-allowed',
                boxShadow: (uploadFile || selectedJob) ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
              }}
            >
              💬 Add Captions
            </button>
            {error && (
              <div style={{
                background: '#2a1515', border: '1px solid #ff4444',
                borderRadius: 12, padding: 12, marginTop: 12,
                color: '#ff6666', fontSize: 13,
              }}>
                ❌ {error}
              </div>
            )}
          </>
        )}
        {/* Processing / Polling state */}
        {(stage === 'uploading' || stage === 'processing' || stage === 'polling') && (
          <div style={{
            background: '#0D1526', borderRadius: 16, padding: 32,
            border: '1px solid rgba(0,170,255,0.15)', textAlign: 'center',
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>💬</div>
            <h3 style={{ color: '#00AAFF', margin: '0 0 8px' }}>
              {stage === 'uploading' ? 'Uploading…' : 'Adding Captions…'}
            </h3>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 20 }}>
              {statusMsg || 'Processing your video…'}
            </p>
            {/* Progress bar */}
            <div style={{
              height: 6, background: '#0A0F1E', borderRadius: 3,
              overflow: 'hidden', marginBottom: 8,
            }}>
              <div style={{
                height: '100%', background: 'linear-gradient(90deg, #00AAFF, #00D4FF)', borderRadius: 3,
                width: `${progress}%`, transition: 'width 0.5s ease',
              }} />
            </div>
            <p style={{ color: '#3a4a6a', fontSize: 12 }}>{progress}%</p>
          </div>
        )}
        {/* Done state */}
        {stage === 'done' && captionJobId && (
          <div style={{
            background: '#0D1526', borderRadius: 16, padding: 32,
            border: '1px solid #00AAFF', textAlign: 'center',
            boxShadow: '0 0 20px rgba(0,170,255,0.15)',
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
            <h3 style={{ color: '#00AAFF', margin: '0 0 8px' }}>Captions Added!</h3>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 20 }}>
              Your captioned video is ready to download.
            </p>
            <a
              href={`${API}/download/${captionJobId}`}
              style={{
                display: 'inline-block', padding: '14px 32px', borderRadius: 12,
                background: 'linear-gradient(135deg, #00AAFF, #00D4FF)', color: '#fff', fontWeight: 700,
                fontSize: 15, textDecoration: 'none',
                boxShadow: '0 0 20px rgba(0,170,255,0.3)',
              }}
            >
              ⬇️ Download Video
            </a>
            <button
              onClick={resetCaptions}
              style={{
                display: 'block', width: '100%', marginTop: 16, padding: 12,
                borderRadius: 12, border: '1px solid rgba(0,170,255,0.15)', background: 'transparent',
                color: '#8899BB', fontSize: 14, cursor: 'pointer',
              }}
            >
              ← Caption Another Video
            </button>
          </div>
        )}
        {/* Error state */}
        {stage === 'error' && (
          <div style={{
            background: '#1a1212', borderRadius: 16, padding: 32,
            border: '1px solid #ff4444', textAlign: 'center',
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
            <h3 style={{ color: '#ff6666', margin: '0 0 8px' }}>Caption Failed</h3>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 20 }}>{error}</p>
            <button
              onClick={resetCaptions}
              style={{
                padding: '12px 32px', borderRadius: 12, border: '1px solid rgba(0,170,255,0.15)',
                background: 'transparent', color: '#8899BB', fontSize: 14, cursor: 'pointer',
              }}
            >
              ← Try Again
            </button>
          </div>
        )}
        {/* ─── VOICEOVER SECTION ────────────────────────────── */}
        <div style={{ marginTop: 40 }}>
          <div style={{ textAlign: 'center', marginBottom: 20 }}>
            <h2 style={{ fontSize: 24, fontWeight: 700, margin: 0, color: '#00AAFF' }}>
              🎙️ Voiceover
            </h2>
            <p style={{ color: '#8899BB', fontSize: 13, marginTop: 4 }}>
              Generate AI voiceover with ElevenLabs
            </p>
          </div>
          {voStage === 'idle' && (
            <>
              {/* Script input */}
              <div style={{
                background: '#0D1526', borderRadius: 16, padding: 20,
                border: '1px solid rgba(0,170,255,0.15)', marginBottom: 16,
              }}>
                <h3 style={{ margin: '0 0 10px', fontSize: 14, color: '#8899BB' }}>
                  📝 Script
                </h3>
                <textarea
                  value={voText}
                  onChange={(e) => setVoText(e.target.value)}
                  placeholder="Type your script here..."
                  style={{
                    width: '100%', minHeight: 100, padding: 12, borderRadius: 10,
                    border: '1px solid rgba(0,170,255,0.15)', background: '#0A0F1E', color: '#fff',
                    fontSize: 14, resize: 'vertical', fontFamily: 'inherit',
                  }}
                />
              </div>
              {/* Voice selector */}
              <div style={{
                background: '#0D1526', borderRadius: 16, padding: 20,
                border: '1px solid rgba(0,170,255,0.15)', marginBottom: 16,
              }}>
                <h3 style={{ margin: '0 0 10px', fontSize: 14, color: '#8899BB' }}>
                  🗣️ Voice
                </h3>
                <select
                  value={voVoiceId}
                  onChange={(e) => setVoVoiceId(e.target.value)}
                  style={{
                    width: '100%', padding: 12, borderRadius: 10,
                    border: '1px solid rgba(0,170,255,0.15)', background: '#0A0F1E', color: '#fff',
                    fontSize: 14,
                  }}
                >
                  <option value="">Default (Rachel)</option>
                  {voices.map((v) => (
                    <option key={v.voice_id} value={v.voice_id}>
                      {v.name}
                    </option>
                  ))}
                </select>
              </div>
              {/* Attach to video */}
              <div style={{
                background: '#0D1526', borderRadius: 16, padding: 20,
                border: '1px solid rgba(0,170,255,0.15)', marginBottom: 16,
              }}>
                <h3 style={{ margin: '0 0 10px', fontSize: 14, color: '#8899BB' }}>
                  🎬 Attach to Video (optional)
                </h3>
                <select
                  value={voAttachJob || ''}
                  onChange={(e) => setVoAttachJob(e.target.value || null)}
                  style={{
                    width: '100%', padding: 12, borderRadius: 10,
                    border: '1px solid rgba(0,170,255,0.15)', background: '#0A0F1E', color: '#fff',
                    fontSize: 14,
                  }}
                >
                  <option value="">Audio only (no video)</option>
                  {jobs.map((j) => (
                    <option key={j.job_id} value={j.job_id}>
                      {j.prompt ? j.prompt.slice(0, 50) : j.job_id.slice(0, 8)}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleVoiceover}
                disabled={!voText.trim()}
                style={{
                  width: '100%', padding: 16, borderRadius: 14, border: 'none',
                  background: voText.trim() ? 'linear-gradient(135deg, #00AAFF, #00D4FF)' : '#1a2540',
                  color: voText.trim() ? '#fff' : '#4a5a7a',
                  fontSize: 16, fontWeight: 700,
                  cursor: voText.trim() ? 'pointer' : 'not-allowed',
                  boxShadow: voText.trim() ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
                }}
              >
                🎙️ Generate Voiceover
              </button>
              {voError && (
                <div style={{
                  background: '#2a1515', border: '1px solid #ff4444',
                  borderRadius: 12, padding: 12, marginTop: 12,
                  color: '#ff6666', fontSize: 13,
                }}>
                  ❌ {voError}
                </div>
              )}
            </>
          )}
          {(voStage === 'generating' || voStage === 'polling') && (
            <div style={{
              background: '#0D1526', borderRadius: 16, padding: 32,
              border: '1px solid rgba(0,170,255,0.15)', textAlign: 'center',
            }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🎙️</div>
              <h3 style={{ color: '#00AAFF', margin: '0 0 8px' }}>Generating Voiceover…</h3>
              <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 20 }}>
                {voStatusMsg || 'Processing…'}
              </p>
              <div style={{
                height: 6, background: '#0A0F1E', borderRadius: 3,
                overflow: 'hidden', marginBottom: 8,
              }}>
                <div style={{
                  height: '100%', background: 'linear-gradient(90deg, #00AAFF, #00D4FF)', borderRadius: 3,
                  width: `${voProgress}%`, transition: 'width 0.5s ease',
                }} />
              </div>
              <p style={{ color: '#3a4a6a', fontSize: 12 }}>{voProgress}%</p>
            </div>
          )}
          {voStage === 'done' && voJobId && (
            <div style={{
              background: '#0D1526', borderRadius: 16, padding: 32,
              border: '1px solid #00AAFF', textAlign: 'center',
              boxShadow: '0 0 20px rgba(0,170,255,0.15)',
            }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
              <h3 style={{ color: '#00AAFF', margin: '0 0 8px' }}>Voiceover Ready!</h3>
              <a
                href={`${API}/download/${voJobId}`}
                style={{
                  display: 'inline-block', padding: '14px 32px', borderRadius: 12,
                  background: 'linear-gradient(135deg, #00AAFF, #00D4FF)', color: '#fff', fontWeight: 700,
                  fontSize: 15, textDecoration: 'none',
                  boxShadow: '0 0 20px rgba(0,170,255,0.3)',
                }}
              >
                ⬇️ Download
              </a>
              <button
                onClick={resetVoiceover}
                style={{
                  display: 'block', width: '100%', marginTop: 16, padding: 12,
                  borderRadius: 12, border: '1px solid rgba(0,170,255,0.15)', background: 'transparent',
                  color: '#8899BB', fontSize: 14, cursor: 'pointer',
                }}
              >
                ← New Voiceover
              </button>
            </div>
          )}
          {voStage === 'error' && (
            <div style={{
              background: '#1a1212', borderRadius: 16, padding: 32,
              border: '1px solid #ff4444', textAlign: 'center',
            }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
              <h3 style={{ color: '#ff6666', margin: '0 0 8px' }}>Voiceover Failed</h3>
              <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 20 }}>{voError}</p>
              <button
                onClick={resetVoiceover}
                style={{
                  padding: '12px 32px', borderRadius: 12, border: '1px solid rgba(0,170,255,0.15)',
                  background: 'transparent', color: '#8899BB', fontSize: 14, cursor: 'pointer',
                }}
              >
                ← Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
