'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import Link from 'next/link';
import { uploadFiles, uploadMusic, submitEdit, getStatus, getDownloadUrl } from '@/lib/api';
import type { StatusResponse } from '@/lib/api';

const STYLES = ['Auto', 'Cole Bennett', 'Cinematic', 'Vintage', 'Clean', 'Neon', 'Temitayo'];

const PLACEHOLDER_PROMPTS = [
  'Fast-paced highlight reel, energetic cuts',
  'Cinematic slow-mo recap, warm vibes',
  '30-second Instagram Reel, hook at the start',
];

type AppState = 'idle' | 'uploading' | 'processing' | 'completed' | 'error';

export default function EditorPage() {
  const [videoFiles, setVideoFiles] = useState<File[]>([]);
  const [musicFile, setMusicFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('Auto');
  const [appState, setAppState] = useState<AppState>('idle');
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState('');
  const [jobId, setJobId] = useState('');

  const videoInputRef = useRef<HTMLInputElement>(null);
  const musicInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleVideoDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    const files = Array.from(e.dataTransfer.files).filter((f) =>
      ['video/mp4', 'video/quicktime'].includes(f.type)
    );
    if (files.length) setVideoFiles((prev) => [...prev, ...files]);
  }, []);

  const handleMusicDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    const file = Array.from(e.dataTransfer.files).find((f) =>
      ['audio/mpeg', 'audio/wav', 'audio/mp3'].includes(f.type)
    );
    if (file) setMusicFile(file);
  }, []);

  const dragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
  };

  const dragLeave = (e: React.DragEvent) => {
    e.currentTarget.classList.remove('drag-over');
  };

  const removeVideo = (index: number) => {
    setVideoFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!videoFiles.length) {
      setError('Please add at least one video file.');
      return;
    }
    if (!prompt.trim()) {
      setError('Please describe your edit.');
      return;
    }

    setError('');
    setAppState('uploading');

    try {
      // Upload videos
      const uploadRes = await uploadFiles(videoFiles);
      const fileIds = uploadRes.file_ids;

      // Upload music if present
      let musicId: string | undefined;
      if (musicFile) {
        const musicRes = await uploadMusic(musicFile);
        musicId = musicRes.music_id;
      }

      // Submit edit
      setAppState('processing');
      const editRes = await submitEdit({
        file_ids: fileIds,
        music_id: musicId,
        prompt: prompt.trim(),
        style: style.toLowerCase(),
      });

      setJobId(editRes.job_id);

      // Poll for status
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await getStatus(editRes.job_id);
          setStatus(statusRes);

          if (statusRes.status === 'completed') {
            if (pollRef.current) clearInterval(pollRef.current);
            setAppState('completed');
          } else if (statusRes.status === 'failed') {
            if (pollRef.current) clearInterval(pollRef.current);
            setAppState('error');
            setError(statusRes.error || 'Edit failed. Please try again.');
          }
        } catch {
          // Silently retry on poll failure
        }
      }, 2000);
    } catch (err) {
      setAppState('error');
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    }
  };

  const resetEditor = () => {
    setVideoFiles([]);
    setMusicFile(null);
    setPrompt('');
    setStyle('Auto');
    setAppState('idle');
    setStatus(null);
    setError('');
    setJobId('');
    if (pollRef.current) clearInterval(pollRef.current);
  };

  const placeholderIndex = useRef(Math.floor(Math.random() * PLACEHOLDER_PROMPTS.length));

  return (
    <main className="min-h-screen">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-dark/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold tracking-tight">
            tubee<span className="text-accent">.</span>
          </Link>
          <span className="text-sm text-secondary">Editor</span>
        </div>
      </nav>

      <div className="pt-28 pb-20 px-6">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">Create your edit</h1>
          <p className="text-secondary mb-10">
            Upload footage, describe what you want, and let AI do the rest.
          </p>

          {/* Upload Section */}
          {(appState === 'idle' || appState === 'error') && (
            <div className="space-y-6">
              {/* Video Upload */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Video Files <span className="text-accent">*</span>
                </label>
                <div
                  className="drop-zone border-2 border-dashed border-white/10 rounded-2xl p-10 text-center cursor-pointer hover:border-white/20 transition-colors"
                  onDrop={handleVideoDrop}
                  onDragOver={dragOver}
                  onDragLeave={dragLeave}
                  onClick={() => videoInputRef.current?.click()}
                >
                  <input
                    ref={videoInputRef}
                    type="file"
                    accept="video/mp4,video/quicktime,.mp4,.mov"
                    multiple
                    className="hidden"
                    onChange={(e) => {
                      const files = Array.from(e.target.files || []);
                      if (files.length) setVideoFiles((prev) => [...prev, ...files]);
                      e.target.value = '';
                    }}
                  />
                  <div className="text-3xl mb-3">🎬</div>
                  <p className="text-white font-medium mb-1">
                    Drop video files here or click to browse
                  </p>
                  <p className="text-secondary text-sm">MP4, MOV — multiple files supported</p>
                </div>

                {/* File list */}
                {videoFiles.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {videoFiles.map((f, i) => (
                      <div
                        key={`${f.name}-${i}`}
                        className="flex items-center justify-between bg-card border border-white/5 rounded-xl px-4 py-3"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="text-accent text-sm">▶</span>
                          <span className="text-sm truncate">{f.name}</span>
                          <span className="text-secondary text-xs flex-shrink-0">
                            {(f.size / 1024 / 1024).toFixed(1)} MB
                          </span>
                        </div>
                        <button
                          onClick={() => removeVideo(i)}
                          className="text-secondary hover:text-white ml-3 text-lg"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Music Upload */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Music <span className="text-secondary text-xs">(optional)</span>
                </label>
                {musicFile ? (
                  <div className="flex items-center justify-between bg-card border border-white/5 rounded-xl px-4 py-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-accent text-sm">♫</span>
                      <span className="text-sm truncate">{musicFile.name}</span>
                      <span className="text-secondary text-xs flex-shrink-0">
                        {(musicFile.size / 1024 / 1024).toFixed(1)} MB
                      </span>
                    </div>
                    <button
                      onClick={() => setMusicFile(null)}
                      className="text-secondary hover:text-white ml-3 text-lg"
                    >
                      ×
                    </button>
                  </div>
                ) : (
                  <div
                    className="drop-zone border-2 border-dashed border-white/10 rounded-2xl p-6 text-center cursor-pointer hover:border-white/20 transition-colors"
                    onDrop={handleMusicDrop}
                    onDragOver={dragOver}
                    onDragLeave={dragLeave}
                    onClick={() => musicInputRef.current?.click()}
                  >
                    <input
                      ref={musicInputRef}
                      type="file"
                      accept="audio/mpeg,audio/wav,.mp3,.wav"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) setMusicFile(file);
                        e.target.value = '';
                      }}
                    />
                    <p className="text-secondary text-sm">
                      🎵 Drop a music file here — MP3, WAV
                    </p>
                  </div>
                )}
              </div>

              {/* Prompt */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Describe your edit <span className="text-accent">*</span>
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder={PLACEHOLDER_PROMPTS[placeholderIndex.current]}
                  rows={3}
                  className="w-full bg-card border border-white/10 rounded-2xl px-5 py-4 text-white placeholder:text-secondary/50 focus:outline-none focus:border-accent/40 transition-colors resize-none text-sm"
                />
              </div>

              {/* Style Selector */}
              <div>
                <label className="block text-sm font-medium mb-3">Style Preset</label>
                <div className="flex flex-wrap gap-2">
                  {STYLES.map((s) => (
                    <button
                      key={s}
                      onClick={() => setStyle(s)}
                      className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                        style === s
                          ? 'bg-accent text-dark'
                          : 'bg-card border border-white/10 text-secondary hover:text-white hover:border-white/20'
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-2xl px-5 py-4 text-red-400 text-sm">
                  {error}
                </div>
              )}

              {/* Submit */}
              <button
                onClick={handleSubmit}
                className="w-full bg-accent text-dark font-bold text-lg py-4 rounded-2xl hover:brightness-110 hover:scale-[1.01] transition-all shadow-[0_0_40px_rgba(200,241,53,0.15)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create Edit ⚡
              </button>
            </div>
          )}

          {/* Processing State */}
          {appState === 'processing' && status && (
            <div className="bg-card border border-white/5 rounded-2xl p-8">
              <div className="text-center mb-8">
                <div className="text-4xl mb-4 animate-pulse">⚡</div>
                <h2 className="text-xl font-bold mb-1">Creating your edit</h2>
                <p className="text-secondary text-sm">This usually takes 1-3 minutes</p>
              </div>

              {/* Progress bar */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-secondary">{status.stage || 'Processing...'}</span>
                  <span className="text-accent font-mono">{Math.round(status.progress)}%</span>
                </div>
                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${status.progress}%` }}
                  />
                </div>
              </div>

              {/* Stage details */}
              <div className="space-y-2 mt-6">
                {[
                  { stage: 'Uploading files', threshold: 10 },
                  { stage: 'Detecting scenes', threshold: 25 },
                  { stage: 'AI making edit decisions', threshold: 50 },
                  { stage: 'Assembling timeline', threshold: 75 },
                  { stage: 'Rendering final video', threshold: 90 },
                ].map((s) => (
                  <div
                    key={s.stage}
                    className={`flex items-center gap-2 text-sm ${
                      status.progress >= s.threshold ? 'text-white' : 'text-secondary/40'
                    }`}
                  >
                    <span>
                      {status.progress >= s.threshold + 15 ? '✓' : status.progress >= s.threshold ? '◉' : '○'}
                    </span>
                    {s.stage}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Uploading State */}
          {appState === 'uploading' && (
            <div className="bg-card border border-white/5 rounded-2xl p-8 text-center">
              <div className="text-4xl mb-4 animate-spin">⬆️</div>
              <h2 className="text-xl font-bold mb-1">Uploading files</h2>
              <p className="text-secondary text-sm">Sending your footage to the AI pipeline...</p>
            </div>
          )}

          {/* Processing without status yet */}
          {appState === 'processing' && !status && (
            <div className="bg-card border border-white/5 rounded-2xl p-8 text-center">
              <div className="text-4xl mb-4 animate-pulse">⚡</div>
              <h2 className="text-xl font-bold mb-1">Starting your edit</h2>
              <p className="text-secondary text-sm">Initializing AI pipeline...</p>
            </div>
          )}

          {/* Completed State */}
          {appState === 'completed' && (
            <div className="bg-card border border-accent/20 rounded-2xl p-8">
              <div className="text-center mb-8">
                <div className="text-5xl mb-4">🎉</div>
                <h2 className="text-2xl font-bold mb-1">Your edit is ready!</h2>
                <p className="text-secondary text-sm">Preview it below or download directly</p>
              </div>

              {/* Video preview */}
              <div className="bg-black rounded-2xl overflow-hidden mb-6 aspect-[9/16] max-w-sm mx-auto">
                <video
                  src={getDownloadUrl(jobId)}
                  controls
                  className="w-full h-full object-contain"
                />
              </div>

              <div className="flex gap-3">
                <a
                  href={getDownloadUrl(jobId)}
                  download
                  className="flex-1 bg-accent text-dark font-bold text-center py-4 rounded-2xl hover:brightness-110 transition-all"
                >
                  Download ↓
                </a>
                <button
                  onClick={resetEditor}
                  className="flex-1 border border-white/10 text-white font-semibold py-4 rounded-2xl hover:bg-white/5 transition-all"
                >
                  Edit Again
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
