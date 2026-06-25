import React, { useState, useEffect } from 'react';
import { Loader2, Wand2 } from 'lucide-react';
import { getApiUrl } from '../config';
import { toast } from './CFUI';

export default function VideoEditorPanel() {
  const [tools, setTools] = useState([]);
  const [selectedTool, setSelectedTool] = useState('');
  const [inputPath, setInputPath] = useState('');
  const [params, setParams] = useState('');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);

  useEffect(() => {
    fetch(getApiUrl('/api/video-editor/tools'))
      .then(r => r.json()).then(d => setTools(d.tools || []))
      .catch(() => {});
  }, []);

  const getVideoInfo = async () => {
    if (!inputPath) return;
    try {
      const r = await fetch(getApiUrl('/api/video-editor/info'), {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: inputPath }),
      });
      const d = await r.json();
      setVideoInfo(d);
    } catch { toast('Failed to get video info', 'error'); }
  };

  const executeTool = async () => {
    if (!selectedTool || !inputPath) return;
    setProcessing(true); setResult(null);
    try {
      let parsedParams = {};
      try { parsedParams = params ? JSON.parse(params) : {}; } catch { toast('Invalid JSON params', 'error'); setProcessing(false); return; }
      const r = await fetch(getApiUrl(`/api/video-editor/${selectedTool}`), {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: inputPath, ...parsedParams }),
      });
      const d = await r.json();
      setResult(d);
      if (d.output_path) toast('Done!', 'success');
      else if (d.error) toast(d.error, 'error');
    } catch { toast('Processing failed', 'error'); }
    finally { setProcessing(false); }
  };

  const toolDescriptions = {
    trim: 'Cut video between timestamps', merge: 'Merge multiple videos', add_text: 'Add text overlay',
    add_audio: 'Add background audio', resize: 'Resize dimensions', crop: 'Crop region',
    rotate: 'Rotate video', speed: 'Change speed', fade: 'Add fade in/out',
    filter: 'Apply visual filter', chroma_key: 'Green screen removal', overlay_video: 'Overlay another video',
    subtitles: 'Burn subtitles', watermark: 'Add watermark', normalize_audio: 'Normalize audio levels',
    extract_audio: 'Extract audio track', thumbnail: 'Generate thumbnail', detect_scenes: 'Detect scene changes',
    convert: 'Convert format', stabilize: 'Stabilize shaky footage', info: 'Get video metadata',
    quality_check: 'Check quality metrics', pipeline: 'Chain multiple operations',
  };

  return (
    <div className="h-full flex flex-col overflow-hidden p-4 md:p-6 animate-[fadeIn_0.3s_ease-out]">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-white">Video Editor</h2>
        <p className="text-zinc-400 text-sm">Professional video editing powered by FFmpeg</p>
      </div>

      {/* Input */}
      <div className="bg-white/5 rounded-xl p-4 mb-4 border border-white/5">
        <label className="text-xs text-zinc-400 mb-1 block">Input Video Path</label>
        <div className="flex gap-2">
          <input value={inputPath} onChange={e => setInputPath(e.target.value)}
            placeholder="/app/output/.../video.mp4"
            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm" />
          <button onClick={getVideoInfo} className="px-3 py-2 bg-white/10 hover:bg-white/15 text-zinc-300 rounded-lg text-sm">
            Info
          </button>
        </div>
        {videoInfo && (
          <div className="mt-2 text-xs text-zinc-400 bg-white/5 rounded-lg p-2 font-mono">
            {videoInfo.width}x{videoInfo.height} | {videoInfo.codec} | {videoInfo.duration?.toFixed(1)}s | {videoInfo.size_mb}MB
          </div>
        )}
      </div>

      {/* Tool selector */}
      <div className="bg-white/5 rounded-xl p-4 mb-4 border border-white/5">
        <label className="text-xs text-zinc-400 mb-1 block">Edit Operation</label>
        <select value={selectedTool} onChange={e => { setSelectedTool(e.target.value); setParams(''); setResult(null); }}
          className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm">
          <option value="">Select an operation...</option>
          {tools.map(t => <option key={t.name} value={t.name}>{t.name} — {toolDescriptions[t.name] || t.description}</option>)}
        </select>
        {selectedTool && toolDescriptions[selectedTool] && (
          <p className="text-xs text-zinc-500 mt-2">{toolDescriptions[selectedTool]}</p>
        )}
      </div>

      {/* Params */}
      {selectedTool && selectedTool !== 'info' && (
        <div className="bg-white/5 rounded-xl p-4 mb-4 border border-white/5">
          <label className="text-xs text-zinc-400 mb-1 block">Parameters (JSON)</label>
          <textarea value={params} onChange={e => setParams(e.target.value)}
            placeholder='{"start": 10, "end": 20}'
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white text-sm font-mono h-20 resize-none" />
        </div>
      )}

      {/* Execute */}
      <button onClick={executeTool} disabled={!selectedTool || !inputPath || processing}
        className="w-full py-3 rounded-xl font-semibold text-sm transition disabled:opacity-40 bg-primary hover:bg-primary/80 text-white">
        {processing ? <Loader2 className="animate-spin inline mr-2" size={16} /> : <Wand2 className="inline mr-2" size={16} />}
        {processing ? 'Processing...' : 'Run Operation'}
      </button>

      {/* Result */}
      {result && (
        <div className="mt-4 bg-white/5 rounded-xl p-4 border border-white/5">
          <h4 className="text-sm font-semibold text-white mb-2">Result</h4>
          {result.output_path ? (
            <div className="text-xs text-emerald-400 font-mono break-all">Output: {result.output_path}</div>
          ) : result.error ? (
            <div className="text-xs text-red-400">{result.error}</div>
          ) : (
            <pre className="text-xs text-zinc-400 font-mono overflow-x-auto max-h-48 overflow-y-auto">{JSON.stringify(result, null, 2)}</pre>
          )}
        </div>
      )}
    </div>
  );
}
