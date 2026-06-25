import React, { useState, useEffect } from 'react';
import { Play, Trash2, Volume2, Mic } from 'lucide-react';
import { getApiUrl } from '../config';
import { Skeleton, EmptyState, toast } from './CFUI';

export default function VoiceLabPanel() {
  const [library, setLibrary] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [testText, setTestText] = useState('Hello, this is a test of my cloned voice.');
  const [testAudio, setTestAudio] = useState(null);
  const [testing, setTesting] = useState(false);
  const [name, setName] = useState('');

  const fetchLibrary = async () => {
    setLoading(true);
    try {
      const r = await fetch(getApiUrl('/api/voice-lab/library'));
      const d = await r.json();
      setLibrary(d.voices || []);
    } catch (_) { setLibrary([]); }
    finally { setLoading(false); }
  };
  useEffect(() => { fetchLibrary(); }, []);

  const [loading, setLoading] = useState(true);

  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !name.trim()) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('name', name.trim());
      fd.append('sample_text', 'Hello, this is a sample of my voice.');
      fd.append('file', file);
      const r = await fetch(getApiUrl('/api/voice-lab/clone'), { method: 'POST', body: fd });
      if (r.ok) {
        setName('');
        await fetchLibrary();
        toast('Voice cloned! Now in your library.', 'success');
      } else {
        const e = await r.json().catch(() => ({}));
        toast(`Clone failed: ${e.detail || r.statusText}`, 'error');
      }
    } catch (err) { toast(`Clone failed: ${err.message}`, 'error'); }
    finally { setUploading(false); }
  };

  const onTest = async (voiceId) => {
    setTesting(true);
    try {
      const fd = new FormData();
      fd.append('voice_id', voiceId);
      fd.append('text', testText);
      const r = await fetch(getApiUrl('/api/voice-lab/test'), { method: 'POST', body: fd });
      if (r.ok) {
        const blob = await r.blob();
        setTestAudio(URL.createObjectURL(blob));
        toast('Voice test generated', 'success');
      } else {
        const e = await r.json().catch(() => ({}));
        toast(`Test failed: ${e.detail || r.statusText}`, 'error');
      }
    } catch (err) { toast(`Test failed: ${err.message}`, 'error'); }
    finally { setTesting(false); }
  };

  const onDelete = async (voiceId) => {
    if (!confirm(`Delete voice ${voiceId}?`)) return;
    const r = await fetch(getApiUrl(`/api/voice-lab/${voiceId}`), { method: 'DELETE' });
    if (r.ok) { await fetchLibrary(); toast('Voice deleted', 'success'); }
  };

  return (
    <div className="h-full overflow-y-auto p-8 max-w-5xl mx-auto animate-[fadeIn_0.3s_ease-out]">
      <h1 className="text-2xl font-bold mb-2">Voice Lab</h1>
      <p className="text-zinc-400 text-sm mb-8">Clone a voice from a 10s+ sample, then use it in AI Shorts and translations.</p>

      <div className="glass-panel p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Clone a new voice</h2>
        <div className="space-y-3">
          <input
            value={name} onChange={(e) => setName(e.target.value)}
            placeholder="Voice name (e.g. 'My Brand Voice')"
            className="w-full bg-black/50 border border-white/20 rounded-lg px-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-violet-500"
          />
          <label className="block">
            <span className="text-xs text-zinc-500 mb-1 block">Sample audio (.wav / .mp3, 10-60s recommended)</span>
            <input type="file" accept="audio/*" onChange={onUpload} disabled={uploading || !name.trim()}
              className="block w-full text-sm text-zinc-300 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-violet-600 file:text-white file:cursor-pointer disabled:opacity-50" />
          </label>
          {uploading && <p className="text-xs text-violet-400">Cloning... (may take 10-30s)</p>}
        </div>
      </div>

      <div className="glass-panel p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Test synthesis</h2>
        <textarea
          value={testText} onChange={(e) => setTestText(e.target.value)}
          rows={3} className="w-full bg-black/50 border border-white/20 rounded-lg px-4 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-violet-500 mb-3"
        />
        {testAudio && (
          <div className="mb-3"><audio src={testAudio} controls className="w-full" /></div>
        )}
        {library.length === 0 ? (
          <p className="text-xs text-zinc-500">Clone a voice first to test synthesis.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {library.map((v) => (
              <button key={v.voice_id} onClick={() => onTest(v.voice_id)} disabled={testing}
                className="text-xs bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg flex items-center gap-1">
                <Play size={12} /> {v.name} {testing ? '...' : ''}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="glass-panel p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          Voice library
          <span className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-zinc-400 font-normal">{library.length}</span>
        </h2>
        {loading ? (
          <div className="space-y-2">
            <Skeleton w="w-full" h="h-12" />
            <Skeleton w="w-5/6" h="h-12" />
            <Skeleton w="w-4/6" h="h-12" />
          </div>
        ) : library.length === 0 ? (
          <EmptyState
            icon={Mic}
            title="No voices cloned yet"
            hint="Upload a 10-60 second audio sample above. Your voice will appear here and can be used in AI Shorts and translations."
          />
        ) : (
          <div className="space-y-2">
            {library.map((v) => (
              <div key={v.voice_id} className="flex items-center justify-between p-3 border border-white/5 rounded-lg hover:border-violet-500/30 transition-colors stagger-item">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-violet-500/10 flex items-center justify-center">
                    <Volume2 size={16} className="text-violet-400" />
                  </div>
                  <div>
                    <p className="text-white font-medium">{v.name}</p>
                    <p className="text-xs text-zinc-500">{v.engine} · {new Date(v.created_at * 1000).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onTest(v.voice_id)}
                    className="text-zinc-400 hover:text-violet-400 p-1.5 hover:bg-violet-500/10 rounded transition-colors"
                    title="Test synthesis"
                  >
                    <Play size={16} />
                  </button>
                  <button onClick={() => onDelete(v.voice_id)} className="text-zinc-400 hover:text-red-400 p-1.5 hover:bg-red-500/10 rounded transition-colors" title="Delete">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
