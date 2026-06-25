import React, { useState } from 'react';
import { getApiUrl } from '../config';
import { toast } from './CFUI';

export default function AvatarStudioPanel() {
  const [description, setDescription] = useState('A friendly 30-year-old man with short dark hair, warm smile, casual t-shirt');
  const [productDesc, setProductDesc] = useState('');
  const [numOptions, setNumOptions] = useState(3);
  const [images, setImages] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [animateTaskId, setAnimateTaskId] = useState(null);
  const [animateStatus, setAnimateStatus] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [audioPath, setAudioPath] = useState('');

  const onGenerate = async () => {
    if (!description.trim()) return;
    setGenerating(true); setImages([]); setSelectedImage(null);
    try {
      const fd = new FormData();
      fd.append('description', description);
      if (productDesc) fd.append('product_description', productDesc);
      fd.append('num_options', String(numOptions));
      const r = await fetch(getApiUrl('/api/avatar-studio/portrait'), { method: 'POST', body: fd });
      const d = await r.json();
      if (r.ok) setImages(d.urls || []);
      else toast(`Generate failed: ${d.detail || r.statusText}`, 'error');
    } catch (err) { toast(`Generate failed: ${err.message}`, 'error'); }
    finally { setGenerating(false); }
  };

  const onAnimate = async () => {
    if (!selectedImage) return;
    setAnimateTaskId(null); setAnimateStatus({ status: 'Submitting...' });
    try {
      const fd = new FormData();
      fd.append('image_path', selectedImage);
      if (audioPath) fd.append('audio_path', audioPath);
      fd.append('prompt', 'Person talking to camera with natural expressions');
      const r = await fetch(getApiUrl('/api/avatar-studio/animate'), { method: 'POST', body: fd });
      const d = await r.json();
      if (r.ok) {
        setAnimateTaskId(d.task_id);
        const poll = async () => {
          const sr = await fetch(getApiUrl(`/api/avatar-studio/status/${d.task_id}`));
          if (sr.ok) {
            const sd = await sr.json();
            setAnimateStatus(sd);
            if (sd.status === 'Success' || sd.status === 'Fail') return;
          }
          setTimeout(poll, 4000);
        };
        poll();
      } else {
        setAnimateStatus({ error: d.detail || r.statusText });
      }
    } catch (err) { setAnimateStatus({ error: err.message }); }
  };

  return (
    <div className="h-full overflow-y-auto p-8 max-w-5xl mx-auto animate-[fadeIn_0.3s_ease-out]">
      <h1 className="text-2xl font-bold mb-2">Avatar Studio</h1>
      <p className="text-zinc-400 text-sm mb-8">Generate AI actor portraits, then animate with audio for talking-head videos.</p>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="glass-panel p-6">
          <h2 className="text-lg font-semibold mb-4">Generate portraits</h2>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Actor description</label>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3}
                className="w-full bg-black/50 border border-white/20 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500" />
            </div>
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Product description (optional)</label>
              <input value={productDesc} onChange={(e) => setProductDesc(e.target.value)}
                placeholder="e.g. artisan coffee beans in a kraft bag"
                className="w-full bg-black/50 border border-white/20 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-violet-500" />
            </div>
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Number of options</label>
              <input type="number" min={1} max={6} value={numOptions} onChange={(e) => setNumOptions(Number(e.target.value))}
                className="w-24 bg-black/50 border border-white/20 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500" />
            </div>
            <button onClick={onGenerate} disabled={generating}
              className="w-full bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white py-2.5 rounded-lg font-medium flex items-center justify-center gap-2">
              {generating ? 'Generating...' : 'Generate portraits'}
            </button>
          </div>
        </div>

        <div className="glass-panel p-6">
          <h2 className="text-lg font-semibold mb-4">Animate with audio</h2>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Selected portrait</label>
              {selectedImage ? (
                <img src={selectedImage} alt="Selected" className="w-32 h-32 object-cover rounded-lg border border-violet-500/30" />
              ) : (
                <p className="text-xs text-zinc-500 italic">Generate and select a portrait to animate</p>
              )}
            </div>
            <div>
              <label className="text-xs text-zinc-500 mb-1 block">Audio path (optional, /videos/...)</label>
              <input value={audioPath} onChange={(e) => setAudioPath(e.target.value)}
                placeholder="/videos/my_job/voiceover.mp3"
                className="w-full bg-black/50 border border-white/20 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-violet-500" />
            </div>
            <button onClick={onAnimate} disabled={!selectedImage || !!animateTaskId}
              className="w-full bg-pink-600 hover:bg-pink-500 disabled:opacity-50 text-white py-2.5 rounded-lg font-medium">
              {animateTaskId ? 'Animating...' : 'Animate (MiniMax S2V)'}
            </button>
            {animateStatus && (
              <div className="text-xs text-zinc-300 p-3 bg-black/30 rounded-lg">
                {animateStatus.status || JSON.stringify(animateStatus)}
                {animateStatus.file_id && (
                  <div className="mt-2">
                    <a href={`/api/avatar-studio/download/${animateStatus.file_id}`} className="text-violet-400 underline">Download video</a>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {images.length > 0 && (
        <div className="glass-panel p-6 mt-6">
          <h2 className="text-lg font-semibold mb-4">Generated options</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {images.map((url, i) => (
              <button key={i} onClick={() => setSelectedImage(url)}
                className={`relative rounded-lg overflow-hidden border-2 transition-all ${
                  selectedImage === url ? 'border-violet-500' : 'border-white/10 hover:border-white/30'
                }`}>
                <img src={url} alt={`Option ${i+1}`} className="w-full aspect-[9/16] object-cover" />
                {selectedImage === url && (
                  <div className="absolute top-2 right-2 bg-violet-500 text-white text-xs px-2 py-1 rounded">Selected</div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
