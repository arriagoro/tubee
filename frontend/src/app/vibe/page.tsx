'use client';
import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';
const API = 'https://tubee-production.up.railway.app';
const HEADERS = {};
const STYLES = [
  { label: 'Social Reel', value: 'social_reel', icon: '📱', desc: 'Animated text, color grade, vertical reel' },
  { label: 'Highlight', value: 'highlight', icon: '⚡', desc: 'Fast cuts with beat markers' },
  { label: 'Brand Promo', value: 'brand_promo', icon: '🏷️', desc: 'Title card + clips + CTA end card' },
  { label: 'Testimonial', value: 'testimonial', icon: '🗣️', desc: 'Talking head with animated captions' },
  { label: 'Before/After', value: 'before_after', icon: '↔️', desc: 'Split screen comparison' },
];
type Stage = 'idle' | 'uploading' | 'generating' | 'polling' | 'done' | 'error';
export default function VibePage() {
  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [musicFile, setMusicFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('social_reel');
  const [duration, setDuration] = useState(15);
  const [stage, setStage] = useState<Stage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState('');
  const [error, setError] = useState('');
  const [jobId, setJobId] = useState('');
  const [vibeJobId, setVibeJobId] = useState('');
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [codeExpanded, setCodeExpanded] = useState(false);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const musicInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);
  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);
  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setVideoFiles(Array.from(e.target.files));
    }
  };
  const handleMusicSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setMusicFile(e.target.files[0]);
    }
  };
  const removeFile = (idx: number) => {
    setVideoFiles((prev) => prev.filter((_, i) => i !== idx));
  };
  const handleVibeEdit = async () => {
    if (videoFiles.length === 0) {
      setError('Upload at least one video clip');
      return;
    }
    if (!prompt.trim()) {
      setError('Describe your video first');
      return;
    }
    // trial check removed
    setError('');
    setStage('uploading');
    setProgress(5);
    setStatusText('Uploading clips...');
    setGeneratedCode(null);
    try {
      // Step 1: Upload files
      const formData = new FormData();
      videoFiles.forEach((f) => formData.append('files', f));
      if (musicFile) formData.append('files', musicFile);
      const uploadRes = await fetch(`${API}/upload`, {
        method: 'POST',
        headers: HEADERS,
        body: formData,
      });
      if (!uploadRes.ok) {
        const err = await uploadRes.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(err.detail || 'Upload failed');
      }
      const uploadData = await uploadRes.json();
      const uploadJobId = uploadData.job_id;
      setJobId(uploadJobId);
      setProgress(20);
      setStatusText('Clips uploaded');
      // Step 2: Submit vibe edit
      setStage('generating');
      setStatusText('AI is generating your video...');
      setProgress(25);
      const vibeRes = await fetch(`${API}/vibe-edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...HEADERS },
        body: JSON.stringify({
          job_id: uploadJobId,
          prompt: prompt.trim(),
          style,
          duration,
        }),
      });
      if (!vibeRes.ok) {
        const err = await vibeRes.json().catch(() => ({ detail: 'Vibe edit failed' }));
        throw new Error(err.detail || 'Vibe edit failed');
      }
      const vibeData = await vibeRes.json();
      const vJobId = vibeData.job_id;
      setVibeJobId(vJobId);
      setStage('polling');
      // Step 3: Poll for progress
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API}/status/${vJobId}`, { headers: HEADERS });
          if (!statusRes.ok) return;
          const status = await statusRes.json();
          setProgress(status.progress || 30);
          setStatusText(status.stage || 'Processing...');
          if (status.status === 'done') {
            if (pollRef.current) clearInterval(pollRef.current);
            setStage('done');
            setProgress(100);
            setStatusText('Your vibe edit is ready!');
            // trial check removed)
            // Fetch generated code
            try {
              const codeRes = await fetch(`${API}/vibe-code/${vJobId}`, { headers: HEADERS });
              if (codeRes.ok) {
                const codeData = await codeRes.json();
                setGeneratedCode(codeData.code);
              }
            } catch {
              // Code fetch is optional
            }
          } else if (status.status === 'error') {
            if (pollRef.current) clearInterval(pollRef.current);
            setStage('error');
            setError(status.error || 'Processing failed');
          }
        } catch {
          // Ignore transient poll errors
        }
      }, 2000);
    } catch (err: any) {
      setStage('error');
      setError(err.message || 'Something went wrong');
    }
  };
  const reset = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    setVideoFiles([]);
    setMusicFile(null);
    setPrompt('');
    setStyle('social_reel');
    setDuration(15);
    setStage('idle');
    setProgress(0);
    setStatusText('');
    setError('');
    setJobId('');
    setVibeJobId('');
    setGeneratedCode(null);
    setCodeExpanded(false);
  };
  const isProcessing = stage === 'uploading' || stage === 'generating' || stage === 'polling';
  const { user } = useAuth();
  return (
    <main className="min-h-screen bg-dark text-white">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-dark/80 backdrop-blur-xl border-b border-[rgba(0,170,255,0.15)]">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold tracking-tight">
            tubee<span className="text-accent">.</span>
          </Link>
          <div className="flex items-center gap-1 text-sm">
            {[
              { label: 'Edit', href: '/editor' },
              { label: 'Generate', href: '/generate' },
              { label: 'Vibe', href: '/vibe' },
              { label: 'Captions', href: '/captions' },
              { label: 'Upscale', href: '/upscale' },
            ].map((tab) => (
              <Link
                key={tab.label}
                href={tab.href}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  tab.label === 'Vibe'
                    ? 'bg-accent text-white'
                    : 'text-secondary hover:text-white hover:bg-white/5'
                }`}
              >
                {tab.label}
              </Link>
            ))}
          </div>
        </div>
      </nav>
      <div className="pt-24 pb-16 px-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl sm:text-5xl font-black mb-3">
            ✨ Vibe Edit
          </h1>
          <p className="text-secondary text-lg max-w-xl mx-auto">
            Describe your video in natural language. AI writes the code. Remotion renders it. Magic.
          </p>
        </div>
        {/* Trial Banner & Upgrade Modal */}
        
        
        {stage === 'done' ? (
          /* ── Result ─────────────────────────────────────────── */
          <div className="space-y-6">
            <div className="bg-card border border-accent/30 rounded-2xl p-8 text-center">
              <div className="text-5xl mb-4">🎉</div>
              <h2 className="text-2xl font-bold mb-2">Your Vibe Edit is Ready</h2>
              <p className="text-secondary mb-6">{statusText}</p>
              <div className="flex gap-4 justify-center flex-wrap">
                <a
                  href={`${API}/download/${vibeJobId}`}
                  className="bg-accent text-white font-bold px-8 py-3 rounded-xl hover:shadow-[0_0_20px_rgba(0,170,255,0.3)] transition-all"
                >
                  ⬇️ Download Video
                </a>
                <button
                  onClick={reset}
                  className="border border-[rgba(0,170,255,0.15)] text-white font-semibold px-8 py-3 rounded-xl hover:bg-white/5 transition-all"
                >
                  New Vibe Edit
                </button>
              </div>
            </div>
            {/* Generated Code */}
            {generatedCode && (
              <div className="bg-card border border-[rgba(0,170,255,0.15)] rounded-2xl overflow-hidden">
                <button
                  onClick={() => setCodeExpanded(!codeExpanded)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/5 transition-all"
                >
                  <span className="font-semibold">
                    🧠 AI-Generated Remotion Code
                  </span>
                  <span className="text-secondary text-sm">
                    {codeExpanded ? '▲ Collapse' : '▼ Expand'}
                  </span>
                </button>
                {codeExpanded && (
                  <div className="px-6 pb-6">
                    <pre className="bg-[#0a0a0a] border border-white/10 rounded-xl p-4 overflow-x-auto text-xs text-green-400 max-h-96 overflow-y-auto">
                      <code>{generatedCode}</code>
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          /* ── Form ──────────────────────────────────────────── */
          <div className="space-y-6">
            {/* Upload Clips */}
            <div className="bg-card border border-[rgba(0,170,255,0.15)] rounded-2xl p-6">
              <h3 className="font-semibold mb-4 text-lg">📁 Upload Clips</h3>
              <div
                onClick={() => videoInputRef.current?.click()}
                className="border-2 border-dashed border-[rgba(0,170,255,0.2)] rounded-xl p-8 text-center cursor-pointer hover:border-accent/40 hover:bg-white/5 transition-all"
              >
                <div className="text-4xl mb-2">🎥</div>
                <p className="text-secondary">
                  {videoFiles.length > 0
                    ? `${videoFiles.length} clip${videoFiles.length > 1 ? 's' : ''} selected`
                    : 'Click to upload video clips'}
                </p>
              </div>
              <input
                ref={videoInputRef}
                type="file"
                accept="video/*"
                multiple
                className="hidden"
                onChange={handleVideoSelect}
              />
              {videoFiles.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {videoFiles.map((f, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 bg-white/5 px-3 py-1 rounded-lg text-sm"
                    >
                      🎬 {f.name}
                      <button
                        onClick={() => removeFile(i)}
                        className="text-red-400 hover:text-red-300 ml-1"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
              {/* Optional music */}
              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={() => musicInputRef.current?.click()}
                  className="text-sm text-secondary hover:text-white border border-white/10 px-3 py-1.5 rounded-lg hover:bg-white/5 transition-all"
                >
                  🎵 {musicFile ? musicFile.name : 'Add Music (optional)'}
                </button>
                {musicFile && (
                  <button
                    onClick={() => setMusicFile(null)}
                    className="text-red-400 text-sm hover:text-red-300"
                  >
                    Remove
                  </button>
                )}
              </div>
              <input
                ref={musicInputRef}
                type="file"
                accept="audio/*"
                className="hidden"
                onChange={handleMusicSelect}
              />
            </div>
            {/* Prompt */}
            <div className="bg-card border border-[rgba(0,170,255,0.15)] rounded-2xl p-6">
              <h3 className="font-semibold mb-4 text-lg">✍️ Describe Your Video</h3>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Make a 20-second hype reel with my clips, fast cuts, neon blue text showing my brand name, end with a CTA..."
                rows={4}
                className="w-full bg-[#0a0a0a] border border-white/10 rounded-xl p-4 text-white placeholder-white/30 resize-none focus:outline-none focus:border-accent/50 transition-all"
              />
            </div>
            {/* Style Selector */}
            <div className="bg-card border border-[rgba(0,170,255,0.15)] rounded-2xl p-6">
              <h3 className="font-semibold mb-4 text-lg">🎨 Style</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {STYLES.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => setStyle(s.value)}
                    className={`p-4 rounded-xl border text-center transition-all ${
                      style === s.value
                        ? 'border-accent bg-accent/10 shadow-[0_0_15px_rgba(0,170,255,0.15)]'
                        : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                    }`}
                  >
                    <div className="text-2xl mb-1">{s.icon}</div>
                    <div className="text-sm font-semibold">{s.label}</div>
                    <div className="text-xs text-secondary mt-1 hidden sm:block">{s.desc}</div>
                  </button>
                ))}
              </div>
            </div>
            {/* Duration */}
            <div className="bg-card border border-[rgba(0,170,255,0.15)] rounded-2xl p-6">
              <h3 className="font-semibold mb-4 text-lg">⏱️ Duration</h3>
              <div className="flex gap-3">
                {[10, 15, 20, 30, 60].map((d) => (
                  <button
                    key={d}
                    onClick={() => setDuration(d)}
                    className={`px-5 py-2 rounded-xl font-semibold transition-all ${
                      duration === d
                        ? 'bg-accent text-white'
                        : 'border border-white/10 text-secondary hover:text-white hover:bg-white/5'
                    }`}
                  >
                    {d}s
                  </button>
                ))}
              </div>
            </div>
            {/* Error */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
                ⚠️ {error}
              </div>
            )}
            {/* Progress */}
            {isProcessing && (
              <div className="bg-card border border-accent/30 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold">{statusText || 'Processing...'}</span>
                  <span className="text-sm text-secondary">{progress}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div
                    className="bg-accent h-2 rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
            {/* Submit Button */}
            <button
              onClick={handleVibeEdit}
              disabled={isProcessing || videoFiles.length === 0 || !prompt.trim()}
              className={`w-full py-4 rounded-2xl font-bold text-lg transition-all ${
                isProcessing || videoFiles.length === 0 || !prompt.trim()
                  ? 'bg-white/10 text-white/30 cursor-not-allowed'
                  : 'bg-gradient-to-r from-[#00AAFF] to-[#00D4FF] text-white hover:shadow-[0_0_40px_rgba(0,170,255,0.3)] hover:scale-[1.01]'
              }`}
            >
              {isProcessing ? '⏳ Processing...' : '✨ Vibe Edit'}
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
