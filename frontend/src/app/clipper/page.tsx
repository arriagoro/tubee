'use client';
import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';
import { apiBase, isRailwayActive, SKIP_NGROK } from '@/lib/api';

const HEADERS = SKIP_NGROK;

const CLIP_COUNTS = [3, 5, 10, 20];
const CLIP_LENGTHS = [
  { label: '30s', value: 30 },
  { label: '60s', value: 60 },
  { label: '90s', value: 90 },
];
const CONTENT_TYPES = [
  { label: 'Gaming 🎮', value: 'gaming' },
  { label: 'Podcast 🎙️', value: 'podcast' },
  { label: 'Sports ⚽', value: 'sports' },
  { label: 'General 📹', value: 'general' },
];
const FORMATS = [
  { label: 'Reels 9:16', value: 'reels' },
  { label: 'Landscape 16:9', value: 'landscape' },
  { label: 'Square 1:1', value: 'square' },
];

const TYPE_BADGES: Record<string, string> = {
  reaction: '🔥 Reaction',
  funny: '😂 Funny',
  highlight: '🎯 Highlight',
  educational: '📚 Educational',
  emotional: '💜 Emotional',
};

type Stage = 'idle' | 'uploading' | 'processing' | 'done' | 'error';

interface Highlight {
  start: number;
  end: number;
  duration: number;
  score: number;
  reason: string;
  type: string;
  transcript_snippet: string;
}

interface Clip {
  index: number;
  filename: string;
  highlight: Highlight;
  download_url: string;
}

function formatTimestamp(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export default function ClipperPage() {
  const { user } = useAuth();
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [numClips, setNumClips] = useState(5);
  const [clipDuration, setClipDuration] = useState(60);
  const [contentType, setContentType] = useState('general');
  const [format, setFormat] = useState('reels');
  const [stage, setStage] = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [clips, setClips] = useState<Clip[]>([]);
  const [highlights, setHighlights] = useState<Highlight[]>([]);
  const [error, setError] = useState('');
  const [apiReady, setApiReady] = useState(false);
  const [previewClip, setPreviewClip] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiBase().then(() => setApiReady(true));
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && (file.type.startsWith('video/') || file.name.match(/\.(mp4|mov|mkv|avi|webm)$/i))) {
      setVideoFile(file);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setVideoFile(file);
  };

  const startClipping = async () => {
    if (!videoFile) return;
    setStage('uploading');
    setError('');
    setProgress(0);
    setStatusMsg('Uploading video...');
    setClips([]);
    setHighlights([]);

    try {
      const API = await apiBase();
      const formData = new FormData();
      formData.append('files', videoFile);
      formData.append('num_clips', String(numClips));
      formData.append('clip_duration', String(clipDuration));
      formData.append('style', contentType);
      formData.append('format', format);

      const uploadRes = await fetch(`${API}/auto-clip/upload`, {
        method: 'POST',
        headers: HEADERS,
        body: formData,
      });

      if (!uploadRes.ok) {
        const err = await uploadRes.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(err.detail || 'Upload failed');
      }

      const { job_id } = await uploadRes.json();
      setJobId(job_id);
      setStage('processing');
      setStatusMsg('Analyzing video...');

      // Start polling
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API}/clips/${job_id}`, { headers: HEADERS });
          if (!statusRes.ok) return;
          const data = await statusRes.json();

          setProgress(data.progress || 0);
          setStatusMsg(data.stage || 'Processing...');

          if (data.status === 'completed') {
            clearInterval(pollRef.current!);
            pollRef.current = null;
            setClips(data.clips || []);
            setHighlights(data.highlights || []);
            setStage('done');
          } else if (data.status === 'error') {
            clearInterval(pollRef.current!);
            pollRef.current = null;
            setError(data.stage || 'Processing failed');
            setStage('error');
          }
        } catch {
          // Ignore poll errors
        }
      }, 3000);

    } catch (e: any) {
      setError(e.message || 'Something went wrong');
      setStage('error');
    }
  };

  const downloadClip = async (clip: Clip) => {
    const API = await apiBase();
    const url = `${API}${clip.download_url}`;
    window.open(url, '_blank');
  };

  const downloadAll = async () => {
    if (!jobId) return;
    const API = await apiBase();
    window.open(`${API}/clips/${jobId}/download-all`, '_blank');
  };

  const resetClipper = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setVideoFile(null);
    setStage('idle');
    setProgress(0);
    setStatusMsg('');
    setJobId(null);
    setClips([]);
    setHighlights([]);
    setError('');
    setPreviewClip(null);
  };

  const isWorking = stage === 'uploading' || stage === 'processing';

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #080C1A 0%, #0A1628 50%, #0D1F35 100%)',
      color: '#fff', padding: '96px 16px 60px',
    }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>

        {/* Tab Nav */}
        <nav style={{
          display: 'flex', gap: 0, marginBottom: 32, borderRadius: 14,
          overflow: 'hidden', border: '1px solid rgba(0,170,255,0.15)',
          position: 'relative',
        }}>
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
          <div style={{
            flex: 1, padding: '14px 0', textAlign: 'center',
            background: '#00AAFF', color: '#fff', fontWeight: 700, fontSize: 15,
            borderRight: '1px solid rgba(0,170,255,0.15)',
          }}>
            🎬 Clipper
          </div>
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
            🎮 Auto Clipper — Find Your Best Moments
          </h1>
          <p style={{ color: '#8899BB', fontSize: 14, marginTop: 4 }}>
            Upload stream footage, podcast, or any long video. AI finds the highlights and clips them for social media.
          </p>
        </div>

        {/* IDLE STATE: Upload + Settings */}
        {(stage === 'idle' || stage === 'error') && (
          <>
            {/* Upload Zone */}
            <div
              ref={dropRef}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: videoFile ? '2px solid #00AAFF' : '2px dashed rgba(0,170,255,0.3)',
                borderRadius: 16,
                padding: videoFile ? '24px 32px' : '48px 32px',
                textAlign: 'center',
                cursor: 'pointer',
                background: videoFile ? 'rgba(0,170,255,0.05)' : 'rgba(0,170,255,0.02)',
                transition: 'all 0.2s',
                marginBottom: 24,
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/quicktime,video/x-matroska,.mp4,.mov,.mkv,.avi,.webm"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
              {videoFile ? (
                <div>
                  <div style={{ fontSize: 32, marginBottom: 8 }}>🎥</div>
                  <p style={{ color: '#fff', fontWeight: 600, fontSize: 16, margin: '0 0 4px' }}>
                    {videoFile.name}
                  </p>
                  <p style={{ color: '#8899BB', fontSize: 13, margin: 0 }}>
                    {formatFileSize(videoFile.size)} • Click to change
                  </p>
                </div>
              ) : (
                <div>
                  <div style={{ fontSize: 48, marginBottom: 12 }}>📁</div>
                  <p style={{ color: '#fff', fontWeight: 600, fontSize: 16, margin: '0 0 4px' }}>
                    Drop your stream/video here
                  </p>
                  <p style={{ color: '#8899BB', fontSize: 13, margin: 0 }}>
                    Accepts MP4, MOV, MKV • Up to 2GB
                  </p>
                </div>
              )}
            </div>

            {/* Settings */}
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16,
              marginBottom: 24,
            }}>
              {/* Number of clips */}
              <div style={{
                background: 'rgba(13,21,38,0.8)', border: '1px solid rgba(0,170,255,0.1)',
                borderRadius: 12, padding: 16,
              }}>
                <label style={{ color: '#8899BB', fontSize: 12, fontWeight: 600, marginBottom: 8, display: 'block' }}>
                  Number of clips to find
                </label>
                <div style={{ display: 'flex', gap: 8 }}>
                  {CLIP_COUNTS.map(n => (
                    <button
                      key={n}
                      onClick={() => setNumClips(n)}
                      style={{
                        flex: 1, padding: '10px 0', borderRadius: 8, border: 'none',
                        background: numClips === n ? '#00AAFF' : 'rgba(0,170,255,0.1)',
                        color: numClips === n ? '#fff' : '#8899BB',
                        fontWeight: 600, fontSize: 14, cursor: 'pointer',
                      }}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>

              {/* Clip length */}
              <div style={{
                background: 'rgba(13,21,38,0.8)', border: '1px solid rgba(0,170,255,0.1)',
                borderRadius: 12, padding: 16,
              }}>
                <label style={{ color: '#8899BB', fontSize: 12, fontWeight: 600, marginBottom: 8, display: 'block' }}>
                  Clip length
                </label>
                <div style={{ display: 'flex', gap: 8 }}>
                  {CLIP_LENGTHS.map(cl => (
                    <button
                      key={cl.value}
                      onClick={() => setClipDuration(cl.value)}
                      style={{
                        flex: 1, padding: '10px 0', borderRadius: 8, border: 'none',
                        background: clipDuration === cl.value ? '#00AAFF' : 'rgba(0,170,255,0.1)',
                        color: clipDuration === cl.value ? '#fff' : '#8899BB',
                        fontWeight: 600, fontSize: 14, cursor: 'pointer',
                      }}
                    >
                      {cl.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Content type */}
              <div style={{
                background: 'rgba(13,21,38,0.8)', border: '1px solid rgba(0,170,255,0.1)',
                borderRadius: 12, padding: 16,
              }}>
                <label style={{ color: '#8899BB', fontSize: 12, fontWeight: 600, marginBottom: 8, display: 'block' }}>
                  Content type
                </label>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {CONTENT_TYPES.map(ct => (
                    <button
                      key={ct.value}
                      onClick={() => setContentType(ct.value)}
                      style={{
                        flex: 1, padding: '10px 4px', borderRadius: 8, border: 'none',
                        background: contentType === ct.value ? '#00AAFF' : 'rgba(0,170,255,0.1)',
                        color: contentType === ct.value ? '#fff' : '#8899BB',
                        fontWeight: 600, fontSize: 12, cursor: 'pointer',
                        minWidth: 80, whiteSpace: 'nowrap',
                      }}
                    >
                      {ct.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Format */}
              <div style={{
                background: 'rgba(13,21,38,0.8)', border: '1px solid rgba(0,170,255,0.1)',
                borderRadius: 12, padding: 16,
              }}>
                <label style={{ color: '#8899BB', fontSize: 12, fontWeight: 600, marginBottom: 8, display: 'block' }}>
                  Format
                </label>
                <div style={{ display: 'flex', gap: 8 }}>
                  {FORMATS.map(f => (
                    <button
                      key={f.value}
                      onClick={() => setFormat(f.value)}
                      style={{
                        flex: 1, padding: '10px 4px', borderRadius: 8, border: 'none',
                        background: format === f.value ? '#00AAFF' : 'rgba(0,170,255,0.1)',
                        color: format === f.value ? '#fff' : '#8899BB',
                        fontWeight: 600, fontSize: 12, cursor: 'pointer',
                      }}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div style={{
                background: 'rgba(255,60,60,0.1)', border: '1px solid rgba(255,60,60,0.3)',
                borderRadius: 12, padding: 16, marginBottom: 16, color: '#ff6b6b',
                fontSize: 14, textAlign: 'center',
              }}>
                ⚠️ {error}
              </div>
            )}

            {/* Find Highlights Button */}
            <button
              onClick={startClipping}
              disabled={!videoFile}
              style={{
                width: '100%', padding: '16px 0', borderRadius: 12, border: 'none',
                background: videoFile
                  ? 'linear-gradient(135deg, #00AAFF, #0088DD)'
                  : 'rgba(0,170,255,0.15)',
                color: videoFile ? '#fff' : '#556677',
                fontWeight: 700, fontSize: 16, cursor: videoFile ? 'pointer' : 'not-allowed',
                boxShadow: videoFile ? '0 4px 20px rgba(0,170,255,0.3)' : 'none',
                transition: 'all 0.2s',
              }}
            >
              ✨ Find Highlights
            </button>
          </>
        )}

        {/* PROCESSING STATE */}
        {isWorking && (
          <div style={{
            background: 'rgba(13,21,38,0.8)', border: '1px solid rgba(0,170,255,0.15)',
            borderRadius: 16, padding: 40, textAlign: 'center',
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>
              {stage === 'uploading' ? '📤' : '🔍'}
            </div>
            <h3 style={{ color: '#00AAFF', margin: '0 0 8px', fontSize: 18 }}>
              {statusMsg || 'Processing...'}
            </h3>
            <div style={{
              width: '100%', height: 8, background: 'rgba(0,170,255,0.1)',
              borderRadius: 4, overflow: 'hidden', margin: '16px 0',
            }}>
              <div style={{
                width: `${progress}%`, height: '100%',
                background: 'linear-gradient(90deg, #00AAFF, #00D4FF)',
                borderRadius: 4, transition: 'width 0.5s ease',
              }} />
            </div>
            <p style={{ color: '#8899BB', fontSize: 13, margin: 0 }}>
              {progress}% complete
            </p>
            <p style={{ color: '#556677', fontSize: 12, marginTop: 8 }}>
              This may take a few minutes for long videos...
            </p>
          </div>
        )}

        {/* DONE STATE: Results */}
        {stage === 'done' && (
          <>
            <div style={{
              background: 'rgba(0,200,100,0.05)', border: '1px solid rgba(0,200,100,0.2)',
              borderRadius: 16, padding: 24, textAlign: 'center', marginBottom: 24,
            }}>
              <h3 style={{ color: '#00CC66', margin: '0 0 4px', fontSize: 18 }}>
                🎉 Found {clips.length} highlight{clips.length !== 1 ? 's' : ''}!
              </h3>
              <p style={{ color: '#8899BB', fontSize: 13, margin: 0 }}>
                Ready to download or edit
              </p>
            </div>

            {/* Clip Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 24 }}>
              {clips.map((clip, i) => {
                const h = clip.highlight;
                return (
                  <div key={i} style={{
                    background: 'rgba(13,21,38,0.8)',
                    border: '1px solid rgba(0,170,255,0.12)',
                    borderRadius: 14, padding: 20, position: 'relative',
                    transition: 'border-color 0.2s',
                  }}>
                    {/* Top row: badges */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
                      <span style={{
                        background: 'rgba(0,170,255,0.15)', color: '#00AAFF',
                        padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                      }}>
                        {formatTimestamp(h.start)} - {formatTimestamp(h.end)}
                      </span>
                      <span style={{
                        background: h.score >= 0.8 ? 'rgba(255,200,0,0.15)' : 'rgba(0,170,255,0.1)',
                        color: h.score >= 0.8 ? '#FFD700' : '#8899BB',
                        padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                      }}>
                        ⭐ {Math.round(h.score * 100)}%
                      </span>
                      <span style={{
                        background: 'rgba(255,100,50,0.12)',
                        color: '#FF8844',
                        padding: '4px 10px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                      }}>
                        {TYPE_BADGES[h.type] || h.type}
                      </span>
                    </div>

                    {/* Reason */}
                    <p style={{ color: '#ccc', fontSize: 14, margin: '0 0 8px', fontWeight: 500 }}>
                      {h.reason}
                    </p>

                    {/* Transcript snippet */}
                    {h.transcript_snippet && (
                      <p style={{
                        color: '#8899BB', fontSize: 13, margin: '0 0 14px',
                        fontStyle: 'italic', lineHeight: 1.4,
                        borderLeft: '3px solid rgba(0,170,255,0.2)',
                        paddingLeft: 12,
                      }}>
                        &ldquo;{h.transcript_snippet}&rdquo;
                      </p>
                    )}

                    {/* Actions */}
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <button
                        onClick={() => {
                          const url = clip.download_url;
                          setPreviewClip(previewClip === url ? null : url);
                        }}
                        style={{
                          padding: '8px 16px', borderRadius: 8, border: 'none',
                          background: 'rgba(0,170,255,0.12)', color: '#00AAFF',
                          fontWeight: 600, fontSize: 13, cursor: 'pointer',
                        }}
                      >
                        ▶ Preview
                      </button>
                      <button
                        onClick={() => downloadClip(clip)}
                        style={{
                          padding: '8px 16px', borderRadius: 8, border: 'none',
                          background: 'rgba(0,200,100,0.12)', color: '#00CC66',
                          fontWeight: 600, fontSize: 13, cursor: 'pointer',
                        }}
                      >
                        ⬇ Download
                      </button>
                      <Link href="/editor" style={{
                        padding: '8px 16px', borderRadius: 8,
                        background: 'rgba(255,170,0,0.12)', color: '#FFAA00',
                        fontWeight: 600, fontSize: 13, cursor: 'pointer',
                        textDecoration: 'none',
                      }}>
                        🎬 Edit This Clip
                      </Link>
                    </div>

                    {/* Preview player */}
                    {previewClip === clip.download_url && (
                      <div style={{ marginTop: 12 }}>
                        <PreviewPlayer jobId={jobId!} clipIndex={clip.index} />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Download All + Reset */}
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                onClick={downloadAll}
                style={{
                  flex: 1, padding: '14px 0', borderRadius: 12, border: 'none',
                  background: 'linear-gradient(135deg, #00AAFF, #0088DD)',
                  color: '#fff', fontWeight: 700, fontSize: 15, cursor: 'pointer',
                  boxShadow: '0 4px 20px rgba(0,170,255,0.3)',
                }}
              >
                ⬇ Download All Clips
              </button>
              <button
                onClick={resetClipper}
                style={{
                  padding: '14px 24px', borderRadius: 12, border: '1px solid rgba(0,170,255,0.2)',
                  background: 'transparent', color: '#8899BB',
                  fontWeight: 600, fontSize: 15, cursor: 'pointer',
                }}
              >
                🔄 New Video
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function PreviewPlayer({ jobId, clipIndex }: { jobId: string; clipIndex: number }) {
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  useEffect(() => {
    apiBase().then(api => {
      setVideoUrl(`${api}/clips/${jobId}/download/${clipIndex}`);
    });
  }, [jobId, clipIndex]);

  if (!videoUrl) return null;

  return (
    <video
      src={videoUrl}
      controls
      autoPlay
      style={{
        width: '100%', maxHeight: 400, borderRadius: 10,
        background: '#000',
      }}
    />
  );
}
