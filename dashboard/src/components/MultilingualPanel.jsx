import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { Skeleton, toast } from './CFUI';

export default function MultilingualPanel() {
  const [languages, setLanguages] = useState({});
  const [loadingLangs, setLoadingLangs] = useState(true);
  const [videoPath, setVideoPath] = useState('');
  const [sourceLang, setSourceLang] = useState('');
  const [targetLang, setTargetLang] = useState('es');
  const [translating, setTranslating] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    setLoadingLangs(true);
    fetch(getApiUrl('/api/multilingual/languages')).then((r) => r.json()).then((d) => setLanguages(d.languages || {})).catch(() => {}).finally(() => setLoadingLangs(false));
  }, []);

  const onTranslate = async () => {
    if (!videoPath.trim()) return toast('Enter a video path or use one from your /videos/ directory.', 'warn');
    setTranslating(true); setResult(null);
    try {
      const fd = new FormData();
      fd.append('video_path', videoPath);
      fd.append('target_language', targetLang);
      if (sourceLang) fd.append('source_language', sourceLang);
      const r = await fetch(getApiUrl('/api/multilingual/translate'), { method: 'POST', body: fd });
      const d = await r.json();
      if (r.ok) setResult(d);
      else toast(`Translate failed: ${d.detail || r.statusText}`, 'error');
    } catch (err) { toast(`Translate failed: ${err.message}`, 'error'); }
    finally { setTranslating(false); }
  };

  return (
    <div className="h-full overflow-y-auto p-8 max-w-4xl mx-auto animate-[fadeIn_0.3s_ease-out]">
      <h1 className="text-2xl font-bold mb-2">Multilingual</h1>
      <p className="text-zinc-400 text-sm mb-8">Translate a video's audio to another language. Uses STT + LLM + TTS (MiniMax pipeline).</p>

      <div className="glass-panel p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Translate a video</h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-zinc-500 mb-1 block">Video path (in /videos/ or local path)</label>
            <input value={videoPath} onChange={(e) => setVideoPath(e.target.value)}
              placeholder="/videos/abc123/clip.mp4"
              className="w-full bg-black/50 border border-white/20 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Source language (auto if blank)</label>
              <select value={sourceLang} onChange={(e) => setSourceLang(e.target.value)}
                className="w-full bg-black/50 border border-white/20 rounded-lg px-3 py-2 text-sm text-white">
                <option value="">Auto-detect</option>
                {Object.entries(languages).map(([code, name]) => <option key={code} value={code}>{name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Target language</label>
              <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)}
                className="w-full bg-black/50 border border-white/20 rounded-lg px-3 py-2 text-sm text-white">
                {Object.entries(languages).map(([code, name]) => <option key={code} value={code}>{name}</option>)}
              </select>
            </div>
          </div>
          <button onClick={onTranslate} disabled={translating}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white py-2.5 rounded-lg font-medium flex items-center justify-center gap-2">
            {translating ? 'Translating (STT + LLM + TTS)...' : 'Translate video'}
          </button>
        </div>
      </div>

      {result && (
        <div className="glass-panel p-6 border-emerald-500/30">
          <h2 className="text-lg font-semibold mb-2 text-emerald-300">Translation complete</h2>
          <p className="text-sm text-zinc-300 mb-3">Target: <strong>{result.target_language}</strong></p>
          <video src={result.url} controls className="w-full rounded-lg" />
          <a href={result.url} download className="inline-block mt-3 text-sm text-emerald-400 underline">Download</a>
        </div>
      )}

      <div className="glass-panel p-6 mt-6">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          Supported languages
          <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-zinc-400 font-normal">{Object.keys(languages).length}</span>
        </h2>
        <p className="text-xs text-zinc-500 mb-3">Powered by MiniMax TTS with language_boost + faster-whisper STT.</p>
        {loadingLangs ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} w="w-full" h="h-7" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs text-zinc-300">
            {Object.entries(languages).map(([code, name]) => (
              <div key={code} className="p-2 border border-white/5 rounded-lg hover:border-emerald-500/30 transition-colors stagger-item">
                <span className="text-emerald-400 font-mono">{code}</span> {name}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
