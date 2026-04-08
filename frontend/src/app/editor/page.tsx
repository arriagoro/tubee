'use client';
import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';
import { apiBase, isRailwayActive, SKIP_NGROK } from '@/lib/api';
const HEADERS = SKIP_NGROK;
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
const TRANSITIONS = [
  { label: 'None', value: 'hard_cut' },
  { label: 'Whip Pan', value: 'whip_pan' },
  { label: 'Circle', value: 'circle_reveal' },
  { label: 'Swipe', value: 'swipe' },
  { label: 'Zoom Blur', value: 'zoom_blur' },
  { label: 'Glitch', value: 'glitch' },
  { label: 'Mixed', value: 'mixed' },
];
const EXPORT_QUALITIES = [
  { label: '1080p', value: '1080p', badge: null },
  { label: '2K', value: '2k', badge: null },
  { label: '4K', value: '4k', badge: 'Pro' },
];
const OUTPUT_FORMATS = [
  { label: 'Reels (9:16)', value: 'reels' },
  { label: 'Landscape (16:9)', value: 'landscape' },
  { label: 'Square (1:1)', value: 'square' },
];
type Stage = 'idle' | 'uploading' | 'editing' | 'polling' | 'done' | 'error';
export default function EditorPage() {

  // Payment gate — check real subscription status via backend
  const [subscriptionChecked, setSubscriptionChecked] = useState(false);
  useEffect(() => {
    const checkPayment = async () => {
      try {
        // Check for payment=success query param (just completed checkout)
        if (typeof window !== 'undefined') {
          const params = new URLSearchParams(window.location.search);
          if (params.get('payment') === 'success') {
            // Just paid — give webhook a moment to process, then allow access
            setSubscriptionChecked(true);
            return;
          }
        }

        const { data: { user: currentUser } } = await (await import('@/lib/supabase')).supabase.auth.getUser();
        if (!currentUser) {
          // Not logged in — let AuthProvider handle redirect
          setSubscriptionChecked(true);
          return;
        }

        const API = await apiBase();
        const res = await fetch(`${API}/subscription-status/${currentUser.id}`, {
          headers: HEADERS,
        });
        if (res.ok) {
          const data = await res.json();
          if (!data.is_paid) {
            // No active subscription — redirect to pricing
            window.location.href = '/pricing';
            return;
          }
        }
      } catch (err) {
        // On error, don't block — allow access
        console.error('Subscription check failed:', err);
      }
      setSubscriptionChecked(true);
    };
    checkPayment();
  }, []);

  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [musicFile, setMusicFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('Cinematic');
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [transition, setTransition] = useState('hard_cut');
  const [exportQuality, setExportQuality] = useState('1080p');
  const [outputFormat, setOutputFormat] = useState('reels');
  const [stage, setStage] = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState('');
  // Smart Take Removal state
  const [takeRemovalEnabled, setTakeRemovalEnabled] = useState(false);
  const [takeAggressiveness, setTakeAggressiveness] = useState(0.5);
  const [takeAnalyzing, setTakeAnalyzing] = useState(false);
  const [takeAnalysisStatus, setTakeAnalysisStatus] = useState('');
  const [takeAnalysisResult, setTakeAnalysisResult] = useState<any>(null);
  const [takeRemoving, setTakeRemoving] = useState(false);
  const [takeRemovalDone, setTakeRemovalDone] = useState(false);
  const [takeAnalysisJobId, setTakeAnalysisJobId] = useState<string | null>(null);

  const videoInputRef = useRef<HTMLInputElement>(null);
  const musicInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Cleanup polling on unmount
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);
  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    let files = Array.from(e.target.files || []);
    if (videoFiles.length + files.length > 8) { setError('Maximum 8 videos per edit'); files = files.slice(0, 8 - videoFiles.length); }
    if (files.length > 0) setVideoFiles(files);
  };
  const handleMusicSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    let files = Array.from(e.target.files || []);
    if (videoFiles.length + files.length > 8) { setError('Maximum 8 videos per edit'); files = files.slice(0, 8 - videoFiles.length); }
    if (files.length > 0) setMusicFile(files[0]);
  };
  // Smart Take Removal: analyze takes after upload
  const handleAnalyzeTakes = async (uploadJobId: string) => {
    if (!takeRemovalEnabled || !API) return;
    setTakeAnalyzing(true);
    setTakeAnalysisStatus('Starting analysis…');
    setTakeAnalysisResult(null);
    setTakeRemovalDone(false);

    try {
      const res = await fetch(`${API}/analyze-takes`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: uploadJobId }),
      });
      if (!res.ok) throw new Error(`Analysis request failed (${res.status})`);
      const data = await res.json();
      const analysisJobId = data.job_id;
      setTakeAnalysisJobId(analysisJobId);

      // Poll for analysis completion
      const analysisPoll = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API}/status/${analysisJobId}`, { headers: HEADERS });
          const statusData = await statusRes.json();
          setTakeAnalysisStatus(statusData.stage || 'Analyzing…');

          if (statusData.status === 'done' || statusData.status === 'completed') {
            clearInterval(analysisPoll);
            setTakeAnalyzing(false);
            // Fetch full job data to get take_analysis
            const jobRes = await fetch(`${API}/status/${analysisJobId}`, { headers: HEADERS });
            const jobData = await jobRes.json();
            // The analysis result is stored in the job's take_analysis field
            // We need to get it from the job file or a dedicated endpoint
            // For now, parse from edit_notes and use a dedicated fetch
            try {
              const fullRes = await fetch(`${API}/jobs`, { headers: HEADERS });
              const fullData = await fullRes.json();
              const analysisJob = fullData.jobs?.find((j: any) => j.job_id === analysisJobId);
              // The take_analysis is in the job JSON file - fetch via status
              // Since the API returns take_analysis in the job dict, try to access it
              if (statusData.take_analysis) {
                setTakeAnalysisResult(statusData.take_analysis);
              } else {
                // Fallback: create a basic result from edit_notes
                setTakeAnalysisResult({
                  summary: statusData.edit_notes || jobData.edit_notes || 'Analysis complete',
                  takes: [],
                });
              }
            } catch {
              setTakeAnalysisResult({
                summary: statusData.edit_notes || 'Analysis complete',
                takes: [],
              });
            }
          } else if (statusData.status === 'error' || statusData.status === 'failed') {
            clearInterval(analysisPoll);
            setTakeAnalyzing(false);
            setTakeAnalysisResult(null);
          }
        } catch {
          // keep polling
        }
      }, 3000);
    } catch (err) {
      setTakeAnalyzing(false);
      console.error('Take analysis failed:', err);
    }
  };

  const handleRemoveTakes = async () => {
    if (!takeAnalysisJobId || !API) return;
    setTakeRemoving(true);

    try {
      const res = await fetch(`${API}/remove-takes`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: takeAnalysisJobId,
          aggressiveness: takeAggressiveness,
        }),
      });
      if (!res.ok) throw new Error(`Remove takes request failed (${res.status})`);
      const data = await res.json();
      const removeJobId = data.job_id;

      // Poll for removal completion
      const removePoll = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API}/status/${removeJobId}`, { headers: HEADERS });
          const statusData = await statusRes.json();

          if (statusData.status === 'done' || statusData.status === 'completed') {
            clearInterval(removePoll);
            setTakeRemoving(false);
            setTakeRemovalDone(true);
          } else if (statusData.status === 'error' || statusData.status === 'failed') {
            clearInterval(removePoll);
            setTakeRemoving(false);
          }
        } catch {
          // keep polling
        }
      }, 3000);
    } catch (err) {
      setTakeRemoving(false);
      console.error('Take removal failed:', err);
    }
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
          // Mark trial as used after successful edit
          // trial check removed)
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
    if (videoFiles.length > 8) { setError('Maximum 8 videos per edit. Please remove some clips.'); return; }
    setError('');
    setStage('uploading');
    setProgress(0);
    setStatusMsg('Uploading files…');
    try {
      const form = new FormData();
      videoFiles.forEach(f => form.append('files', f));
      if (musicFile) form.append('files', musicFile);
      setStatusMsg('Uploading videos... (may take 30-60 seconds for large files)');
      // Use AbortController with 3 minute timeout for large files
      const controller = new AbortController();
      const uploadTimeout = setTimeout(() => controller.abort(), 600000); // 10 minutes for large files
      let upRes;
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
      if (!upRes.ok) throw new Error(`Upload failed (${upRes.status}) — try with smaller files or fewer clips`);
      const upData = await upRes.json();
      const id = upData.job_id;
      setJobId(id);

      // If take removal is enabled, trigger analysis
      if (takeRemovalEnabled) {
        handleAnalyzeTakes(id);
      }

      setStage('editing');
      setStatusMsg('Starting edit…');
      const editRes = await fetch(`${API}/edit`, {
        method: 'POST',
        headers: { ...HEADERS, 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: id, prompt, style, aspect_ratio: aspectRatio, transition_style: transition, export_quality: exportQuality, output_format: outputFormat }),
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
    setTransition('hard_cut'); setExportQuality('1080p'); setOutputFormat('reels');
    setStage('idle'); setProgress(0); setStatusMsg(''); setJobId(null); setError('');
    setTakeRemovalEnabled(false); setTakeAggressiveness(0.5); setTakeAnalyzing(false);
    setTakeAnalysisResult(null); setTakeRemoving(false); setTakeRemovalDone(false);
    setTakeAnalysisJobId(null); setTakeAnalysisStatus('');
    if (pollRef.current) clearInterval(pollRef.current);
  };
  const isWorking = stage === 'uploading' || stage === 'editing' || stage === 'polling';
  const { user } = useAuth();
  const [API, setAPI] = useState('');
  const [apiReady, setApiReady] = useState(false);
  useEffect(() => {
    apiBase().then(base => { setAPI(base); setApiReady(true); });
  }, []);
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
        position: 'relative',
      }}>
        {/* API Status Indicator */}
        {apiReady && (
          <div style={{
            position: 'absolute', top: 4, right: 8,
            display: 'flex', alignItems: 'center', gap: 4,
            fontSize: 10, color: '#556677', zIndex: 10,
          }}>
            <div style={{
              width: 6, height: 6, borderRadius: '50%',
              background: isRailwayActive() ? '#00FF88' : '#FFD700',
            }} />
            {isRailwayActive() ? 'Railway' : 'ngrok'}
          </div>
        )}
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
      {/* Trial Banner & Upgrade Modal */}
      
      
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
          <>📹 Select Videos <span style={{ fontSize: 12, opacity: 0.7 }}>(max 8)</span></>
        ) : (
          <span style={{ color: '#00AAFF' }}>
            ✅ {videoFiles.length}/8 videos ready
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

      {/* ── Smart Take Removal ─────────────────────────── */}
      <div style={{
        marginBottom: 20,
        background: '#0D1526',
        border: takeRemovalEnabled ? '1px solid rgba(0,170,255,0.4)' : '1px solid rgba(0,170,255,0.1)',
        borderRadius: 16,
        overflow: 'hidden',
        transition: 'all 0.2s',
      }}>
        {/* Toggle Header */}
        <button
          onClick={() => setTakeRemovalEnabled(!takeRemovalEnabled)}
          disabled={isWorking}
          style={{
            width: '100%', padding: '16px 18px',
            background: 'transparent', border: 'none',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            cursor: isWorking ? 'not-allowed' : 'pointer',
          }}
        >
          <span style={{ color: '#fff', fontSize: 16, fontWeight: 600 }}>
            ✂️ Smart Take Removal
          </span>
          <div style={{
            width: 44, height: 24, borderRadius: 12,
            background: takeRemovalEnabled ? '#00AAFF' : '#1a2540',
            position: 'relative', transition: 'background 0.2s',
          }}>
            <div style={{
              width: 18, height: 18, borderRadius: '50%',
              background: '#fff', position: 'absolute', top: 3,
              left: takeRemovalEnabled ? 23 : 3,
              transition: 'left 0.2s',
            }} />
          </div>
        </button>

        {/* Expanded Content */}
        {takeRemovalEnabled && (
          <div style={{ padding: '0 18px 18px' }}>
            <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 16, lineHeight: 1.5 }}>
              AI analyzes your clips, removes stumbles and weak takes automatically
            </p>

            {/* Aggressiveness Slider */}
            <div style={{ marginBottom: 16 }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                fontSize: 12, color: '#8899BB', marginBottom: 6,
              }}>
                <span>Conservative</span>
                <span style={{ color: '#00AAFF', fontWeight: 600 }}>
                  {takeAggressiveness <= 0.3 ? 'Lenient' : takeAggressiveness <= 0.7 ? 'Balanced' : 'Strict'}
                </span>
                <span>Aggressive</span>
              </div>
              <input
                type="range"
                min="0" max="100" step="5"
                value={takeAggressiveness * 100}
                onChange={e => setTakeAggressiveness(parseInt(e.target.value) / 100)}
                disabled={isWorking}
                style={{
                  width: '100%', height: 6,
                  WebkitAppearance: 'none', appearance: 'none',
                  background: `linear-gradient(to right, #00AAFF ${takeAggressiveness * 100}%, #1a2540 ${takeAggressiveness * 100}%)`,
                  borderRadius: 3, outline: 'none',
                  cursor: isWorking ? 'not-allowed' : 'pointer',
                }}
              />
            </div>

            {/* Analysis Results */}
            {takeAnalysisResult && (
              <div style={{
                background: 'rgba(0,170,255,0.05)',
                borderRadius: 12, padding: 14,
                border: '1px solid rgba(0,170,255,0.15)',
              }}>
                <p style={{ color: '#00AAFF', fontSize: 14, fontWeight: 600, marginBottom: 10 }}>
                  📊 {takeAnalysisResult.summary}
                </p>
                <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                  {takeAnalysisResult.takes?.map((take: { file: string; quality_score: number; recommendation: string; reason: string; issues?: string[] }, i: number) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'flex-start', gap: 10,
                      padding: '8px 0',
                      borderBottom: i < takeAnalysisResult.takes.length - 1 ? '1px solid rgba(0,170,255,0.08)' : 'none',
                    }}>
                      <span style={{
                        fontSize: 16, flexShrink: 0, marginTop: 2,
                      }}>
                        {take.recommendation === 'keep' ? '✅' : '❌'}
                      </span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          marginBottom: 2,
                        }}>
                          <span style={{
                            color: '#fff', fontSize: 13, fontWeight: 500,
                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                          }}>
                            {take.file}
                          </span>
                          <span style={{
                            fontSize: 12, fontWeight: 600, flexShrink: 0, marginLeft: 8,
                            color: take.quality_score >= 0.7 ? '#00FF88' : take.quality_score >= 0.4 ? '#FFD700' : '#FF6B6B',
                          }}>
                            {(take.quality_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p style={{ color: '#8899BB', fontSize: 11, margin: 0 }}>
                          {take.reason}
                        </p>
                        {take.issues && take.issues.length > 0 && (
                          <p style={{ color: '#FF8888', fontSize: 11, margin: '2px 0 0' }}>
                            ⚠️ {take.issues.join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Proceed button */}
                {!takeRemovalDone && (
                  <button
                    onClick={handleRemoveTakes}
                    disabled={isWorking || takeRemoving}
                    style={{
                      width: '100%', marginTop: 12, padding: 12,
                      background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                      color: '#fff', border: 'none', borderRadius: 10,
                      fontSize: 14, fontWeight: 700,
                      cursor: isWorking || takeRemoving ? 'not-allowed' : 'pointer',
                      opacity: isWorking || takeRemoving ? 0.6 : 1,
                    }}
                  >
                    {takeRemoving ? '⏳ Removing bad takes…' : '✂️ Proceed with clean footage'}
                  </button>
                )}
                {takeRemovalDone && (
                  <div style={{
                    marginTop: 12, padding: 10, textAlign: 'center',
                    background: 'rgba(0,255,136,0.05)', borderRadius: 10,
                    border: '1px solid rgba(0,255,136,0.2)',
                  }}>
                    <span style={{ color: '#00FF88', fontSize: 14, fontWeight: 600 }}>
                      ✅ Clean footage ready — proceed with your edit below
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Analyzing indicator */}
            {takeAnalyzing && !takeAnalysisResult && (
              <div style={{
                textAlign: 'center', padding: 20,
                background: 'rgba(0,170,255,0.05)', borderRadius: 12,
              }}>
                <div style={{ fontSize: 24, marginBottom: 8 }}>🔍</div>
                <p style={{ color: '#00AAFF', fontSize: 14, fontWeight: 500 }}>
                  Analyzing takes…
                </p>
                <p style={{ color: '#8899BB', fontSize: 12 }}>
                  {takeAnalysisStatus || 'Transcribing and evaluating your clips'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

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
      {/* ── Transitions ────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>TRANSITIONS</p>
        <div style={{
          display: 'flex', gap: 8, overflowX: 'auto',
          paddingBottom: 8, WebkitOverflowScrolling: 'touch',
        }}>
          {TRANSITIONS.map(t => (
            <button
              key={t.value}
              onClick={() => setTransition(t.value)}
              disabled={isWorking}
              style={{
                flexShrink: 0, padding: '10px 18px',
                borderRadius: 99, border: 'none',
                background: transition === t.value ? '#00AAFF' : '#0D1526',
                color: transition === t.value ? '#fff' : '#8899BB',
                fontSize: 14, fontWeight: transition === t.value ? 700 : 500,
                cursor: isWorking ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>
      {/* ── Export Quality ─────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>EXPORT QUALITY</p>
        <div style={{
          display: 'flex', gap: 8, overflowX: 'auto',
          paddingBottom: 8, WebkitOverflowScrolling: 'touch',
        }}>
          {EXPORT_QUALITIES.map(q => (
            <button
              key={q.value}
              onClick={() => setExportQuality(q.value)}
              disabled={isWorking}
              style={{
                flexShrink: 0, padding: '10px 18px',
                borderRadius: 99, border: 'none',
                background: exportQuality === q.value ? '#00AAFF' : '#0D1526',
                color: exportQuality === q.value ? '#fff' : '#8899BB',
                fontSize: 14, fontWeight: exportQuality === q.value ? 700 : 500,
                cursor: isWorking ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              {q.label}
              {q.badge && (
                <span style={{
                  fontSize: 10, fontWeight: 700, padding: '2px 6px',
                  borderRadius: 6,
                  background: exportQuality === q.value ? 'rgba(255,255,255,0.2)' : 'rgba(0,170,255,0.15)',
                  color: exportQuality === q.value ? '#fff' : '#00AAFF',
                }}>
                  {q.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
      {/* ── Output Format ──────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ color: '#8899BB', fontSize: 13, marginBottom: 8, fontWeight: 500 }}>FORMAT</p>
        <div style={{
          display: 'flex', gap: 8, overflowX: 'auto',
          paddingBottom: 8, WebkitOverflowScrolling: 'touch',
        }}>
          {OUTPUT_FORMATS.map(f => (
            <button
              key={f.value}
              onClick={() => setOutputFormat(f.value)}
              disabled={isWorking}
              style={{
                flexShrink: 0, padding: '10px 18px',
                borderRadius: 99, border: 'none',
                background: outputFormat === f.value ? '#00AAFF' : '#0D1526',
                color: outputFormat === f.value ? '#fff' : '#8899BB',
                fontSize: 14, fontWeight: outputFormat === f.value ? 700 : 500,
                cursor: isWorking ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {f.label}
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
          {/* Post-edit AI tools */}
          <div style={{
            display: 'flex', gap: 8, marginBottom: 12,
          }}>
            <button
              onClick={async () => {
                if (!jobId) return;
                try {
                  const res = await fetch(`${API}/generate-thumbnail`, {
                    method: 'POST',
                    headers: { ...HEADERS, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ job_id: jobId }),
                  });
                  const data = await res.json();
                  if (data.job_id) {
                    alert(`Thumbnail generating! Job ID: ${data.job_id}\nPoll /status/${data.job_id} to check progress.`);
                  }
                } catch { alert('Thumbnail generation failed'); }
              }}
              style={{
                flex: 1, padding: 14, background: '#0D1526',
                color: '#00AAFF', border: '1px solid rgba(0,170,255,0.3)', borderRadius: 12,
                fontSize: 14, fontWeight: 600, cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              🖼️ Generate Thumbnail
            </button>
            <button
              onClick={async () => {
                if (!jobId) return;
                const musicPrompt = prompt || 'Upbeat background music for social media video';
                try {
                  const res = await fetch(`${API}/generate-music`, {
                    method: 'POST',
                    headers: { ...HEADERS, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: musicPrompt, duration: 30 }),
                  });
                  const data = await res.json();
                  if (data.job_id) {
                    alert(`Music generating! Job ID: ${data.job_id}\nPoll /status/${data.job_id} to check progress.`);
                  }
                } catch { alert('Music generation failed'); }
              }}
              style={{
                flex: 1, padding: 14, background: '#0D1526',
                color: '#00AAFF', border: '1px solid rgba(0,170,255,0.3)', borderRadius: 12,
                fontSize: 14, fontWeight: 600, cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              🎵 Generate Music
            </button>
          </div>
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
