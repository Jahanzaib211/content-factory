import React, { useState, useEffect } from 'react';
import { Upload, FileVideo, Sparkles, Youtube, Instagram, Share2, LogOut, ChevronDown, Check, Activity, LayoutDashboard, Settings, PlusCircle, History, Menu, X, Terminal, Shield, LayoutGrid, Image, Globe, RotateCcw, Calendar, AlertTriangle, KeyRound, Bot, Users, Smartphone, ExternalLink, Copy, CheckCircle2, Mic, UserCircle, Languages, Layers, Trash2, Play, Pause, Volume2, Send, Type, FileText, Sparkle, Headphones, Mic2, Wand2, Loader2, Square, CheckCircle, RefreshCw, Plus, ChevronRight, Monitor, Zap, TrendingUp, BarChart3 } from 'lucide-react';
import KeyInput, { MiniMaxKeyInput } from './components/KeyInput';
import MediaInput from './components/MediaInput';
import ResultCard from './components/ResultCard';
import ProcessingAnimation from './components/ProcessingAnimation';
// import Gallery from './components/Gallery';
import ThumbnailStudio from './components/ThumbnailStudio';
import SaaShortsTab from './components/SaaShortsTab';
import UGCGallery from './components/UGCGallery';
import ScheduleWeekModal from './components/ScheduleWeekModal';
import { getApiUrl } from './config';
import { I18nProvider, useT } from './i18n/I18nProvider';
import { Skeleton, CardSkeleton, EngineStatusPill, EmptyState, StatCard, StepIndicator, toast } from './components/CFUI';
import DirectPublishButton from './components/DirectPublishButton';

// Enhanced "Encryption" using XOR + Base64 with a Salt
// This is better than plain Base64 but still client-side.
const SECRET_KEY = import.meta.env.VITE_ENCRYPTION_KEY || "OpenShorts-Static-Salt-Change-Me";
const ENCRYPTION_PREFIX = "ENC:";

const encrypt = (text) => {
  if (!text) return '';
  try {
    const xor = text.split('').map((c, i) =>
      String.fromCharCode(c.charCodeAt(0) ^ SECRET_KEY.charCodeAt(i % SECRET_KEY.length))
    ).join('');
    return ENCRYPTION_PREFIX + btoa(xor);
  } catch (e) {
    console.error("Encryption failed", e);
    return text;
  }
};

const decrypt = (text) => {
  if (!text) return '';
  if (text.startsWith(ENCRYPTION_PREFIX)) {
    try {
      const raw = text.slice(ENCRYPTION_PREFIX.length);
      // Check if it's plain base64 or our custom XOR (simple try)
      const xor = atob(raw);
      const result = xor.split('').map((c, i) =>
        String.fromCharCode(c.charCodeAt(0) ^ SECRET_KEY.charCodeAt(i % SECRET_KEY.length))
      ).join('');
      return result;
    } catch (_) {
      // Fallback if decryption fails (might be old plain text)
      return '';
    }
  }
  // Backward compatibility: If no prefix, assume old plain text (or return empty if you want to force re-login)
  // For migration: Return text as is, so it populates the field, and next save will encrypt it.
  return text;
};

// Simple TikTok icon sine Lucide might not have it or it varies
const TikTokIcon = ({ size = 16, className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M19.589 6.686a4.793 4.793 0 0 1-3.77-4.245V2h-3.445v13.672a2.896 2.896 0 0 1-5.201 1.743l-.002-.001.002.001a2.895 2.895 0 0 1 3.183-4.51v-3.5a6.329 6.329 0 0 0-5.394 10.692 6.33 6.33 0 0 0 10.857-4.424V8.687a8.182 8.182 0 0 0 4.773 1.526V6.79a4.831 4.831 0 0 1-1.003-.104z" />
  </svg>
);

const UserProfileSelector = ({ profiles, selectedUserId, onSelect }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!profiles || profiles.length === 0) return null;

  const selectedProfile = profiles.find(p => p.username === selectedUserId) || profiles[0];

  return (
    <div className="relative z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between bg-surface border border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-300 hover:bg-white/5 transition-colors min-w-[180px]"
      >
        <span className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-[10px] font-bold text-white">
            {selectedProfile?.username?.substring(0, 1).toUpperCase() || "U"}
          </div>
          <span className="font-medium text-white truncate max-w-[100px]">{selectedProfile?.username || "Select User"}</span>
        </span>
        <ChevronDown size={14} className={`text-zinc-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-2 right-0 w-64 bg-[#1a1a1a] border border-white/10 rounded-xl shadow-2xl overflow-hidden">
          <div className="max-h-60 overflow-y-auto custom-scrollbar">
            {profiles.map((profile) => (
              <button
                key={profile.username}
                onClick={() => {
                  onSelect(profile.username);
                  setIsOpen(false);
                }}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/5 transition-colors text-left group border-b border-white/5 last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center text-xs font-bold text-white border border-white/10 shrink-0">
                    {profile.username.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-zinc-200 group-hover:text-white transition-colors truncate">
                      {profile.username}
                    </div>
                    <div className="flex gap-2 mt-0.5">
                      {/* Status indicators */}
                      <div className={`flex items-center gap-1 text-[10px] ${profile.connected.includes('tiktok') ? 'text-zinc-300' : 'text-zinc-600'}`}>
                        <TikTokIcon size={10} />
                      </div>
                      <div className={`flex items-center gap-1 text-[10px] ${profile.connected.includes('instagram') ? 'text-pink-400' : 'text-zinc-600'}`}>
                        <Instagram size={10} />
                      </div>
                      <div className={`flex items-center gap-1 text-[10px] ${profile.connected.includes('youtube') ? 'text-red-400' : 'text-zinc-600'}`}>
                        <Youtube size={10} />
                      </div>
                    </div>
                  </div>
                </div>
                {selectedUserId === profile.username && <Check size={14} className="text-primary shrink-0" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const SESSION_KEY = 'openshorts_session';
const SESSION_MAX_AGE = 3600000; // 1 hour (matches server job retention)

// Mock polling function
const pollJob = async (jobId) => {
  const res = await fetch(getApiUrl(`/api/status/${jobId}`));
  if (!res.ok) throw new Error('Status check failed');
  return res.json();
};

// EnginePicker: one dropdown per capability (read-only for now; the registry
// is small — MiniMax is the only registered provider today. Phase 5 will add
// local OSS providers; the UI auto-renders new entries via the registry shape).
// ── Content Factory: panel components (Phase 7) ──────────────────────
// Each component is self-contained, pulls its own data, and lives in
// the main scroll area. They share the same glass-panel / badge
// styling as the rest of the dashboard.

function VoiceLabPanel() {
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

function AvatarStudioPanel() {
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

function MultilingualPanel() {
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

function ResearchPanel() {
  const [niche, setNiche] = useState('');
  const [trends, setTrends] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [keywordInput, setKeywordInput] = useState('');
  const [seoResult, setSeoResult] = useState(null);
  const [ideas, setIdeas] = useState([]);
  const [loading, setLoading] = useState('');

  const fetchTrends = async () => {
    setLoading('trends');
    try {
      const r = await fetch(getApiUrl(`/api/research/trends?niche=${encodeURIComponent(niche)}`));
      const d = await r.json();
      setTrends(d.trends || []);
    } catch (e) { console.error(e); }
    setLoading('');
  };

  const fetchKeywords = async () => {
    if (!keywordInput.trim()) return;
    setLoading('keywords');
    try {
      const r = await fetch(getApiUrl(`/api/research/keywords?q=${encodeURIComponent(keywordInput)}`));
      const d = await r.json();
      setKeywords(prev => [d, ...prev].slice(0, 20));
    } catch (e) { console.error(e); }
    setLoading('');
  };

  const fetchScore = async (topic) => {
    setLoading('score');
    try {
      const r = await fetch(getApiUrl(`/api/research/score?topic=${encodeURIComponent(topic)}`));
      const d = await r.json();
      setSeoResult(d);
    } catch (e) { console.error(e); }
    setLoading('');
  };

  const fetchIdeas = async () => {
    setLoading('ideas');
    try {
      const r = await fetch(getApiUrl('/api/research/ideas'), {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ niche, count: 5 }),
      });
      const d = await r.json();
      setIdeas(d.ideas || []);
    } catch (e) { console.error(e); }
    setLoading('');
  };

  const scoreColor = (s) => s >= 80 ? 'text-green-400' : s >= 60 ? 'text-amber-400' : s >= 40 ? 'text-orange-400' : 'text-red-400';

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Wand2 className="text-amber-400" size={24} />
        <h1 className="text-2xl font-bold">Research</h1>
      </div>
      <p className="text-zinc-400 text-sm">Find trending topics, research keywords, and generate video ideas.</p>

      {/* Trend Scanner */}
      <div className="bg-surface/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2"><Zap size={18} className="text-amber-400" /> Trend Scanner</h2>
        <div className="flex gap-3">
          <input value={niche} onChange={e => setNiche(e.target.value)} placeholder="Enter niche (e.g. AI, fitness, cooking)" className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-amber-500/50" onKeyDown={e => e.key === 'Enter' && fetchTrends()} />
          <button onClick={fetchTrends} disabled={loading === 'trends'} className="px-5 py-2 bg-amber-500/20 text-amber-400 rounded-lg text-sm font-medium hover:bg-amber-500/30 transition-colors disabled:opacity-50">
            {loading === 'trends' ? <Loader2 className="animate-spin inline" size={14} /> : 'Scan Trends'}
          </button>
        </div>
        {trends.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {trends.map((t, i) => (
              <div key={i} onClick={() => fetchScore(t.title)} className="bg-white/5 border border-white/10 rounded-xl p-4 cursor-pointer hover:border-amber-500/30 transition-all">
                <div className="font-medium text-white text-sm">{t.title}</div>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${t.traffic_level === 'rising' ? 'bg-green-500/20 text-green-400' : t.traffic_level === 'breakout' ? 'bg-red-500/20 text-red-400' : 'bg-zinc-500/20 text-zinc-400'}`}>{t.traffic_level}</span>
                  <span className="text-xs text-zinc-500">{t.search_volume?.toLocaleString()} searches</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Keyword Research */}
      <div className="bg-surface/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2"><FileText size={18} className="text-amber-400" /> Keyword Research</h2>
        <div className="flex gap-3">
          <input value={keywordInput} onChange={e => setKeywordInput(e.target.value)} placeholder="Enter keyword to research" className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-amber-500/50" onKeyDown={e => e.key === 'Enter' && fetchKeywords()} />
          <button onClick={fetchKeywords} disabled={loading === 'keywords'} className="px-5 py-2 bg-amber-500/20 text-amber-400 rounded-lg text-sm font-medium hover:bg-amber-500/30 transition-colors disabled:opacity-50">
            {loading === 'keywords' ? <Loader2 className="animate-spin inline" size={14} /> : 'Research'}
          </button>
        </div>
        {keywords.length > 0 && (
          <div className="space-y-2">
            {keywords.map((kw, i) => (
              <div key={i} className="flex items-center gap-4 bg-white/5 border border-white/10 rounded-lg px-4 py-3">
                <span className="font-medium text-white text-sm flex-1">{kw.keyword}</span>
                <span className="text-xs text-zinc-400">{kw.search_volume?.toLocaleString()} vol</span>
                <span className="text-xs text-zinc-400">{(kw.competition * 100).toFixed(0)}% comp</span>
                <span className={`text-sm font-bold ${scoreColor(kw.score)}`}>{kw.score?.toFixed(0)}</span>
                {kw.related_keywords?.length > 0 && (
                  <div className="flex gap-1 flex-wrap max-w-[200px]">
                    {kw.related_keywords.slice(0, 3).map((rk, j) => (
                      <span key={j} className="text-[10px] bg-white/5 px-1.5 py-0.5 rounded text-zinc-500">{rk}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SEO Score */}
      {seoResult && (
        <div className="bg-surface/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2"><CheckCircle size={18} className="text-amber-400" /> SEO Score: <span className={scoreColor(seoResult.score)}>{seoResult.score}</span></h2>
          <p className="text-zinc-400 text-sm">{seoResult.recommendation}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(seoResult.breakdown || {}).map(([key, val]) => (
              <div key={key} className="bg-white/5 rounded-lg p-3 text-center">
                <div className="text-xs text-zinc-500 mb-1">{key.replace(/_/g, ' ')}</div>
                <div className="text-lg font-bold text-white">{val.score}</div>
                {val.value !== undefined && <div className="text-[10px] text-zinc-600">{typeof val.value === 'number' ? val.value.toLocaleString() : val.value}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Idea Generator */}
      <div className="bg-surface/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2"><Sparkles size={18} className="text-amber-400" /> AI Idea Generator</h2>
          <button onClick={fetchIdeas} disabled={loading === 'ideas'} className="px-5 py-2 bg-amber-500/20 text-amber-400 rounded-lg text-sm font-medium hover:bg-amber-500/30 transition-colors disabled:opacity-50">
            {loading === 'ideas' ? <Loader2 className="animate-spin inline" size={14} /> : 'Generate Ideas'}
          </button>
        </div>
        {ideas.length > 0 && (
          <div className="space-y-3">
            {ideas.map((idea, i) => (
              <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-white">{idea.title}</div>
                    <div className="text-sm text-zinc-400 mt-1">{idea.hook}</div>
                    <div className="text-xs text-zinc-500 mt-2">{idea.description}</div>
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {idea.tags?.map((tag, j) => (
                        <span key={j} className="text-[10px] bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full">{tag}</span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <div className={`text-2xl font-bold ${scoreColor(idea.score)}`}>{idea.score?.toFixed(0)}</div>
                    <div className={`text-xs px-2 py-0.5 rounded-full mt-1 ${idea.estimated_views === 'viral' ? 'bg-red-500/20 text-red-400' : idea.estimated_views === 'high' ? 'bg-green-500/20 text-green-400' : 'bg-zinc-500/20 text-zinc-400'}`}>{idea.estimated_views}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AnalyticsPanel() {
  const [data, setData] = useState(null);
  const [platform, setPlatform] = useState('youtube');
  const [channelId, setChannelId] = useState('');
  const [loading, setLoading] = useState('');

  useEffect(() => {
    fetch(getApiUrl('/api/analytics/dashboard')).then(r => r.json()).then(setData).catch(() => {});
  }, []);

  const fetchChannel = async () => {
    if (!channelId.trim()) return;
    setLoading('channel');
    try {
      const r = await fetch(getApiUrl(`/api/analytics/channel/${platform}?channel_id=${channelId}`));
      const d = await r.json();
      setData(prev => ({ ...prev, channels: [...(prev?.channels || []), d] }));
    } catch (e) { console.error(e); }
    setLoading('');
  };

  const s = data?.summary || {};
  const platforms = data?.platforms || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Activity className="text-cyan-400" size={24} />
        <h1 className="text-2xl font-bold">Analytics</h1>
      </div>
      <p className="text-zinc-400 text-sm">Track performance across YouTube, TikTok, and Instagram.</p>

      {/* Platform Status */}
      <div className="grid grid-cols-3 gap-3">
        {['youtube', 'tiktok', 'instagram'].map(p => (
          <div key={p} className={`bg-surface/50 border rounded-xl p-4 text-center ${platforms[p] ? 'border-green-500/30' : 'border-white/10'}`}>
            <div className="text-sm font-medium capitalize text-white">{p}</div>
            <div className={`text-xs mt-1 ${platforms[p] ? 'text-green-400' : 'text-zinc-500'}`}>{platforms[p] ? 'Connected' : 'Not connected'}</div>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      {s.total_videos > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Videos', value: s.total_videos },
            { label: 'Total Views', value: s.total_views?.toLocaleString() },
            { label: 'Total Likes', value: s.total_likes?.toLocaleString() },
            { label: 'Avg Score', value: s.avg_score?.toFixed(1) },
          ].map(({ label, value }) => (
            <div key={label} className="bg-surface/50 border border-white/10 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-white">{value || '—'}</div>
              <div className="text-xs text-zinc-500 mt-1">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Channel Connect */}
      <div className="bg-surface/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2"><Youtube size={18} className="text-cyan-400" /> Connect Channel</h2>
        <div className="flex gap-3">
          <select value={platform} onChange={e => setPlatform(e.target.value)} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm">
            <option value="youtube">YouTube</option>
            <option value="tiktok">TikTok</option>
            <option value="instagram">Instagram</option>
          </select>
          <input value={channelId} onChange={e => setChannelId(e.target.value)} placeholder="Channel ID" className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-cyan-500/50" />
          <button onClick={fetchChannel} disabled={loading === 'channel'} className="px-5 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm font-medium hover:bg-cyan-500/30 transition-colors disabled:opacity-50">
            {loading === 'channel' ? <Loader2 className="animate-spin inline" size={14} /> : 'Track'}
          </button>
        </div>
      </div>

      {/* Top Videos */}
      {data?.top_videos?.length > 0 && (
        <div className="bg-surface/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2"><TrendingUp size={18} className="text-cyan-400" /> Top Videos</h2>
          <div className="space-y-2">
            {data.top_videos.map((v, i) => (
              <div key={i} className="flex items-center gap-4 bg-white/5 border border-white/10 rounded-lg px-4 py-3">
                <span className="text-sm font-bold text-zinc-500 w-6">#{i + 1}</span>
                <span className="flex-1 text-sm text-white truncate">{v.title || v.video_id}</span>
                <span className="text-xs text-zinc-400">{v.views?.toLocaleString()} views</span>
                <span className="text-xs text-zinc-400">{v.likes?.toLocaleString()} likes</span>
                <span className={`text-sm font-bold ${v.score >= 80 ? 'text-green-400' : v.score >= 50 ? 'text-amber-400' : 'text-zinc-400'}`}>{v.score}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {(!data || s.total_videos === 0) && (
        <div className="bg-surface/50 border border-white/10 rounded-2xl p-12 text-center">
          <Activity size={48} className="mx-auto text-zinc-600 mb-4" />
          <p className="text-zinc-400">No analytics data yet. Connect a channel or publish videos to start tracking.</p>
        </div>
      )}
    </div>
  );
}

function ContentFactoryPanel() {
  const [templates, setTemplates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [calendar, setCalendar] = useState([]);
  const [tab, setTab] = useState('templates');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [t, j, c] = await Promise.all([
        fetch(getApiUrl('/api/factory/templates')).then((r) => r.json()),
        fetch(getApiUrl('/api/factory/jobs')).then((r) => r.json()),
        fetch(getApiUrl('/api/factory/calendar')).then((r) => r.json()),
      ]);
      setTemplates(t.templates || []);
      setJobs(j.jobs || []);
      setCalendar(c.entries || []);
    } catch (_) {}
    finally { setLoading(false); }
  };
  useEffect(() => { fetchAll(); }, []);

  const runTemplate = async (template_id) => {
    const jobName = (name || template_id) + '-' + Date.now().toString(36);
    const fd = new FormData();
    fd.append('template_id', template_id);
    fd.append('name', jobName);
    fd.append('inputs_json', JSON.stringify({ placeholder: 'fill in inputs' }));
    const r = await fetch(getApiUrl('/api/factory/jobs'), { method: 'POST', body: fd });
    if (!r.ok) { toast('Failed to create job', 'error'); return; }
    const { job_id } = await r.json();
    // Kick off execution
    toast(`Started: ${jobName}`, 'success');
    const ex = await fetch(getApiUrl(`/api/factory/execute/${job_id}`), { method: 'POST' });
    if (!ex.ok) { toast(`Failed to start ${jobName}`, 'error'); await fetchAll(); return; }
    setTab('jobs');
    await fetchAll();
    // Poll every 2s until status is terminal
    const poll = async () => {
      const jr = await fetch(getApiUrl(`/api/factory/jobs/${job_id}`));
      if (!jr.ok) return;
      const j = await jr.json();
      await fetchAll();
      if (j.status === 'completed') {
        toast(`Done: ${jobName} (${(j.outputs || []).length} files, $${(j.cost_estimate || {}).total || 0} toFixed(2)})`, 'success');
      } else if (j.status === 'failed') {
        toast(`Failed: ${jobName} — ${j.error || 'unknown'}`, 'error');
      } else {
        setTimeout(poll, 2000);
      }
    };
    setTimeout(poll, 2000);
  };

  const ICONS = { Zap: Activity, Youtube: Youtube, LayoutGrid: LayoutGrid, Languages: Languages, Sparkles: Sparkles, FileVideo: FileVideo, Users: Users, Globe: Globe, Type: Type, Monitor: Monitor };

  return (
    <div className="h-full overflow-y-auto p-8 max-w-6xl mx-auto animate-[fadeIn_0.3s_ease-out]">
      <h1 className="text-2xl font-bold mb-2">Content Factory</h1>
      <p className="text-zinc-400 text-sm mb-6">Pick a template, batch-process, schedule, and measure — all in one panel.</p>

      <div className="flex gap-2 mb-6 border-b border-white/5">
        {['templates', 'jobs', 'calendar'].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm capitalize border-b-2 transition-colors ${
              tab === t ? 'border-violet-500 text-white' : 'border-transparent text-zinc-400 hover:text-white'
            }`}>{t}</button>
        ))}
      </div>

      {tab === 'templates' && (
        <>
          <input value={name} onChange={(e) => setName(e.target.value)}
            placeholder="Optional job name override"
            className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-zinc-600 mb-4 focus:outline-none focus:border-violet-500" />
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((t) => {
              const Icon = ICONS[t.icon] || Activity;
              return (
                <div key={t.id} className="glass-panel p-5 hover:border-violet-500/30 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <Icon size={20} className="text-violet-400" />
                    <span className="text-[10px] text-zinc-500 uppercase tracking-wider">~{t.estimated_minutes}min</span>
                  </div>
                  <h3 className="text-white font-semibold mb-1">{t.name}</h3>
                  <p className="text-xs text-zinc-400 mb-3 leading-relaxed">{t.description}</p>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {t.inputs.map((inp) => (
                      <span key={inp} className="text-[10px] bg-white/5 text-zinc-400 px-2 py-0.5 rounded">{inp}</span>
                    ))}
                  </div>
                  <button onClick={() => runTemplate(t.id)}
                    className="w-full text-xs bg-violet-600 hover:bg-violet-500 text-white py-2 rounded-lg font-medium">
                    Run this template
                  </button>
                </div>
              );
            })}
          </div>
        </>
      )}

      {tab === 'jobs' && (
        <div className="glass-panel p-6">
          {loading ? (
            <div className="space-y-2">
              <Skeleton w="w-full" h="h-16" />
              <Skeleton w="w-5/6" h="h-16" />
              <Skeleton w="w-4/6" h="h-16" />
            </div>
          ) : jobs.length === 0 ? (
            <EmptyState
              icon={Layers}
              title="No jobs yet"
              hint="Pick a template above and click Run. Jobs appear here with live logs and status."
            />
          ) : (
            <div className="space-y-2">
              {jobs.map((j) => (
                <div key={j.job_id} className="p-3 border border-white/5 rounded-lg hover:border-violet-500/30 transition-colors stagger-item">
                  <div className="flex items-center justify-between mb-1">
                    <div>
                      <p className="text-white font-medium">{j.name}</p>
                      <p className="text-xs text-zinc-500">{j.template_id} · {new Date(j.created_at * 1000).toLocaleString()}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded uppercase tracking-wider ${
                        j.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                        j.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                        'bg-violet-500/10 text-violet-400'
                      }`}>{j.status}</span>
                      {j.cost_estimate && j.cost_estimate.total != null && (
                        <span className="text-[10px] text-zinc-500">${j.cost_estimate.total.toFixed(2)}</span>
                      )}
                    </div>
                  </div>
                  {j.outputs && j.outputs.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {j.outputs.map((o) => (
                        <div key={o.path} className="flex items-center justify-between p-2 bg-black/20 rounded text-xs">
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-zinc-400 truncate">{o.name}</span>
                            {o.size != null && <span className="text-zinc-600">({o.size}b)</span>}
                          </div>
                          <div className="flex items-center gap-2">
                            {o.path && /\.mp4$/.test(o.path) && (
                              <DirectPublishButton
                                videoPath={o.path}
                                title={j.name + ' - ' + o.name}
                                description={'Generated by Content Factory via ' + j.template_id}
                              />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {j.logs && j.logs.length > 0 && (
                    <pre className="text-[10px] text-zinc-500 mt-2 whitespace-pre-wrap bg-black/30 p-2 rounded">{j.logs.join('\n')}</pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'calendar' && (
        <div className="glass-panel p-6">
          <p className="text-zinc-500 text-sm mb-4">
            Calendar view of scheduled content. Add jobs from the Templates tab, then drag to schedule.
            <br />
            <span className="text-violet-400">{calendar.length}</span> scheduled entries.
          </p>
          <div className="grid grid-cols-7 gap-1 text-xs text-center">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
              <div key={d} className="text-zinc-500 py-1">{d}</div>
            ))}
            {Array.from({ length: 28 }).map((_, i) => (
              <div key={i} className="aspect-square border border-white/5 rounded p-1 text-zinc-600">
                <span className="text-[10px]">{i + 1}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// One row per platform. Polls connection status and exposes Connect/Disconnect.
function SocialConnectRow({ platform, label, env, devUrl }) {
  const [status, setStatus] = useState(null);
  const [connecting, setConnecting] = useState(false);
  const fetchStatus = async () => {
    try {
      const r = await fetch(getApiUrl('/api/social/connections'));
      const d = await r.json();
      setStatus(d[platform] || { connected: false });
    } catch (_) { setStatus({ connected: false }); }
  };
  useEffect(() => { fetchStatus(); }, [platform]);
  const onConnect = async () => {
    setConnecting(true);
    try {
      const r = await fetch(getApiUrl(`/api/social/${platform}/connect`));
      const d = await r.json();
      if (d.url) {
        window.open(d.url, '_blank', 'noopener,noreferrer');
        setTimeout(fetchStatus, 5000);
      } else toast(d.detail || 'No URL returned', 'error');
    } catch (err) { toast(err.message, 'error'); }
    finally { setConnecting(false); }
  };
  const connected = status?.connected;
  return (
    <div className="flex items-center gap-3 p-3 border border-white/5 rounded-lg">
      <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-zinc-600'}`} />
      <div className="flex-1">
        <p className="text-sm text-white">{label}</p>
        <p className="text-[10px] text-zinc-500 font-mono">{env}</p>
      </div>
      {connected ? (
        <span className="text-xs text-green-400">Connected</span>
      ) : (
        <button onClick={onConnect} disabled={connecting}
          className="text-xs bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg">
          {connecting ? 'Opening…' : 'Connect'}
        </button>
      )}
      <a href={devUrl} target="_blank" rel="noopener noreferrer" className="text-zinc-500 hover:text-zinc-300 text-xs" title="Developer console">
        ↗
      </a>
    </div>
  );
}

function EnginePicker({ enginesByCap, enginesHealth, onRefresh }) {
  const caps = Object.entries(enginesByCap).filter(([, providers]) => providers && providers.length > 0);
  if (caps.length === 0) {
    return <div className="text-xs text-zinc-500 italic">No engines registered yet.</div>;
  }
  return (
    <div className="space-y-3">
      {caps.map(([cap, providers]) => {
        const health = enginesHealth[cap];
        const status = health
          ? health.healthy
            ? { color: 'text-green-400', label: 'healthy' }
            : /not set|missing key/i.test(health.detail || '')
              ? { color: 'text-amber-400', label: 'no key' }
              : { color: 'text-red-400', label: 'error' }
          : { color: 'text-zinc-500', label: 'unknown' };
        return (
          <div key={cap} className="flex items-center gap-3 p-3 border border-white/5 rounded-lg">
            <div className="w-32 shrink-0">
              <div className="text-sm text-white capitalize">{cap}</div>
              <div className={`text-[10px] ${status.color} uppercase tracking-wider`}>{status.label}</div>
            </div>
            <select
              defaultValue={providers[0].provider_id}
              disabled
              className="flex-1 bg-black/50 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-primary disabled:opacity-70"
            >
              {providers.map((p) => (
                <option key={p.provider_id} value={p.provider_id}>
                  {p.display_name} {p.cost_hint ? `(${p.cost_hint})` : ''}
                </option>
              ))}
            </select>
            <button
              onClick={onRefresh}
              className="text-[10px] text-zinc-400 hover:text-white border border-white/10 hover:bg-white/5 rounded px-2 py-1 transition-colors"
              title="Re-probe"
            >
              ⟳
            </button>
          </div>
        );
      })}
    </div>
  );
}

function App() {
  const { t } = useT();
  const [apiKey, setApiKey] = useState(localStorage.getItem('gemini_key') || '');
  const [minimaxKey, setMinimaxKey] = useState(() => {
    const stored = localStorage.getItem('minimax_key_v1');
    if (stored) return decrypt(stored);
    return '';
  });

  // Content Factory: engines registry + health (new in Phase 2)
  const [enginesByCap, setEnginesByCap] = useState({});
  const [enginesHealth, setEnginesHealth] = useState({});
  const fetchEngines = async () => {
    try {
      const [list, health] = await Promise.all([
        fetch(getApiUrl('/api/engines/list')).then((r) => (r.ok ? r.json() : {})),
        fetch(getApiUrl('/api/engines/health')).then((r) => (r.ok ? r.json() : {})),
      ]);
      setEnginesByCap(list || {});
      setEnginesHealth(health || {});
    } catch (_) {
      // silently ignore — UI just shows empty state
    }
  };
  // Social API State - Load encrypted or plain
  const [uploadPostKey, setUploadPostKey] = useState(() => {
    const stored = localStorage.getItem('uploadPostKey_v3');
    if (stored) return decrypt(stored);
    return '';
  });
  // ElevenLabs API State - Load encrypted
  const [elevenLabsKey, setElevenLabsKey] = useState(() => {
    const stored = localStorage.getItem('elevenLabsKey_v1');
    if (stored) return decrypt(stored);
    return '';
  });

  // fal.ai API State - Load encrypted
  const [falKey, setFalKey] = useState(() => {
    const stored = localStorage.getItem('falKey_v1');
    if (stored) return decrypt(stored);
    return '';
  });

  const [uploadUserId, setUploadUserId] = useState(() => localStorage.getItem('uploadUserId') || '');
  const [userProfiles, setUserProfiles] = useState([]); // List of {username, connected: []}
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, processing, complete, error
  const [results, setResults] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logsVisible, setLogsVisible] = useState(true);
  const [processingMedia, setProcessingMedia] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard'); // dashboard, settings

  const [sessionRecovered, setSessionRecovered] = useState(false);
  const [showScheduleWeek, setShowScheduleWeek] = useState(false);

  // Sync state for original video playback
  const [syncedTime, setSyncedTime] = useState(0);
  const [isSyncedPlaying, setIsSyncedPlaying] = useState(false);
  const [syncTrigger, setSyncTrigger] = useState(0);

  const handleClipPlay = (startTime) => {
    setSyncedTime(startTime);
    setIsSyncedPlaying(true);
    setSyncTrigger(prev => prev + 1);
  };

  const handleClipPause = () => {
    setIsSyncedPlaying(false);
  };

  // Session Recovery: Restore on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(SESSION_KEY);
      if (!saved) return;
      const session = JSON.parse(saved);
      if (Date.now() - session.timestamp > SESSION_MAX_AGE) {
        localStorage.removeItem(SESSION_KEY);
        return;
      }
      if (session.jobId && session.status && session.status !== 'idle') {
        setJobId(session.jobId);
        setResults(session.results || null);
        if (session.processingMedia) setProcessingMedia(session.processingMedia);
        if (session.activeTab) setActiveTab(session.activeTab);
        // If was processing, resume polling; if complete/error, just show results
        setStatus(session.status === 'processing' ? 'processing' : session.status);
        setSessionRecovered(true);
        setTimeout(() => setSessionRecovered(false), 5000);
      }
    } catch (_) {
      localStorage.removeItem(SESSION_KEY);
    }
  }, []);

  // Session Recovery: Save state changes
  useEffect(() => {
    if (status === 'idle') {
      localStorage.removeItem(SESSION_KEY);
      return;
    }
    try {
      const sessionData = {
        jobId,
        status,
        results,
        processingMedia: processingMedia?.type === 'url' ? processingMedia : null,
        activeTab,
        timestamp: Date.now()
      };
      localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
    } catch (_) {
      // localStorage full or serialization error - ignore
    }
  }, [jobId, status, results, activeTab]);

  useEffect(() => {
    // Encrypt Gemini Key too for consistency if desired, but user asked specifically about Social integration not saving well.
    // For now keeping gemini plain for compatibility unless requested.
    if (apiKey) localStorage.setItem('gemini_key', apiKey);
  }, [apiKey]);

  useEffect(() => {
    if (minimaxKey) {
      localStorage.setItem('minimax_key_v1', encrypt(minimaxKey));
    } else {
      localStorage.removeItem('minimax_key_v1');
    }
  }, [minimaxKey]);

  useEffect(() => {
    if (uploadPostKey) {
      localStorage.setItem('uploadPostKey_v3', encrypt(uploadPostKey));
    }
    if (uploadUserId) {
      localStorage.setItem('uploadUserId', uploadUserId);
    }
  }, [uploadPostKey, uploadUserId]);

  useEffect(() => {
    if (elevenLabsKey) {
      localStorage.setItem('elevenLabsKey_v1', encrypt(elevenLabsKey));
    }
  }, [elevenLabsKey]);

  useEffect(() => {
    if (falKey) {
      localStorage.setItem('falKey_v1', encrypt(falKey));
    }
  }, [falKey]);

  useEffect(() => {
    if (uploadPostKey && userProfiles.length === 0) {
      fetchUserProfiles();
    }
  }, [uploadPostKey]);

  // Content Factory: fetch engine registry + health when Settings tab opens
  useEffect(() => {
    if (activeTab === 'settings') {
      fetchEngines();
    }
  }, [activeTab]);

  useEffect(() => {
    let interval;
    if ((status === 'processing' || status === 'completed') && jobId) {
      interval = setInterval(async () => {
        try {
          const data = await pollJob(jobId);
          console.log("Job status:", data);

          // Update results if available (real-time)
          if (data.result) {
            setResults(data.result);
          }

          if (data.status === 'completed') {
            setStatus('complete');
            clearInterval(interval);
          } else if (data.status === 'failed') {
            setStatus('error');
            const errorMsg = data.error || (data.logs && data.logs.length > 0 ? data.logs[data.logs.length - 1] : "Process failed");
            setLogs(prev => [...prev, "Error: " + errorMsg]);
            clearInterval(interval);
          } else {
            // Update logs if available
            if (data.logs) setLogs(data.logs);
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [status, jobId]);


  const fetchUserProfiles = async () => {
    if (!uploadPostKey) return;
    try {
      const res = await fetch(getApiUrl('/api/social/user'), {
        headers: { 'X-Upload-Post-Key': uploadPostKey }
      });
      if (!res.ok) throw new Error("Failed to fetch");
      const data = await res.json();
      if (data.profiles && data.profiles.length > 0) {
        setUserProfiles(data.profiles);
        // Auto select first if none selected
        if (!uploadUserId) {
          setUploadUserId(data.profiles[0].username);
        }
      } else {
        alert("No profiles found for this API Key.");
      }
    } catch (e) {
      alert("Error fetching User Profiles. Please check key.");
      console.error(e);
    }
  };

  const handleProcess = async (data) => {
    const hasAnyKey = apiKey || minimaxKey;
    if (!hasAnyKey) {
      setShowKeyModal(true);
      return;
    }
    setStatus('processing');
    setLogs(["Starting process..."]);
    setResults(null);
    setProcessingMedia(data);

    try {
      let body;
      const buildHeaders = () => {
        const h = {};
        if (apiKey) h['X-Gemini-Key'] = apiKey;
        if (minimaxKey) h['X-MiniMax-Key'] = minimaxKey;
        return h;
      };

      if (data.type === 'url') {
        const headers = buildHeaders();
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify({ url: data.payload, acknowledged: !!data.acknowledged });
      } else {
        const formData = new FormData();
        formData.append('file', data.payload);
        formData.append('acknowledged', data.acknowledged ? 'true' : 'false');
        body = formData;
      }

      const res = await fetch(getApiUrl('/api/process'), {
        method: 'POST',
        headers: data.type === 'url' ? buildHeaders() : buildHeaders(),
        body
      });

      if (!res.ok) throw new Error(await res.text());
      const resData = await res.json();
      setJobId(resData.job_id);

    } catch (e) {
      setStatus('error');
      setLogs(l => [...l, `Error starting job: ${e.message}`]);
    }
  };

  const handleReset = () => {
    setStatus('idle');
    setJobId(null);
    setResults(null);
    setLogs([]);
    setProcessingMedia(null);
    localStorage.removeItem(SESSION_KEY);
  };

  // --- UI Components ---

  const Sidebar = () => (
    <div className="w-20 lg:w-64 bg-surface border-r border-white/5 flex flex-col h-full shrink-0 transition-all duration-300">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-white/5 rounded-lg flex items-center justify-center shrink-0 overflow-hidden border border-white/5">
          <img src="/logo-openshorts.png" alt="Logo" className="w-full h-full object-cover" />
        </div>
        <span className="font-bold text-lg text-white hidden lg:block tracking-tight">Content Factory</span>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-2">
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'dashboard' ? 'bg-primary/10 text-primary' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <LayoutDashboard size={20} />
          <span className="font-medium hidden lg:block">Clip Generator</span>
        </button>

        <button
          onClick={() => setActiveTab('saasshorts')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'saasshorts' ? 'bg-violet-500/10 text-violet-400' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <Sparkles size={20} />
          <span className="font-medium hidden lg:block">AI Shorts</span>
        </button>

        <button
          onClick={() => setActiveTab('ai-agent')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'ai-agent' ? 'bg-emerald-500/10 text-emerald-400' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <Bot size={20} />
          <span className="font-medium hidden lg:block">AI Agent</span>
        </button>

        <button
          onClick={() => setActiveTab('ugc-gallery')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'ugc-gallery' ? 'bg-violet-500/10 text-violet-400' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <LayoutGrid size={20} />
          <span className="font-medium hidden lg:block">UGC Gallery</span>
        </button>

        <button
          onClick={() => setActiveTab('thumbnails')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'thumbnails' ? 'bg-primary/10 text-primary' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <Image size={20} />
          <span className="font-medium hidden lg:block">YouTube Studio</span>
        </button>

        {/* ── Content Factory sections (Phase 7) ──────────────── */}
        <div className="pt-2 pb-1 px-3 text-[10px] uppercase tracking-wider text-zinc-600 hidden lg:block">
          Factory
        </div>
        <button
          onClick={() => setActiveTab('factory')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'factory' ? 'bg-violet-500/10 text-violet-400' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <Layers size={20} />
          <span className="font-medium hidden lg:block">Content Factory</span>
        </button>
        <button
          onClick={() => setActiveTab('voice-lab')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'voice-lab' ? 'bg-violet-500/10 text-violet-400' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <Mic size={20} />
          <span className="font-medium hidden lg:block">Voice Lab</span>
        </button>
        <button
          onClick={() => setActiveTab('avatar-studio')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'avatar-studio' ? 'bg-violet-500/10 text-violet-400' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <UserCircle size={20} />
          <span className="font-medium hidden lg:block">Avatar Studio</span>
        </button>
        <button
          onClick={() => setActiveTab('multilingual')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'multilingual' ? 'bg-emerald-500/10 text-emerald-400' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <Languages size={20} />
          <span className="font-medium hidden lg:block">Multilingual</span>
        </button>

        {/* ── Intelligence section (Phase 8) ──────────────── */}
        <div className="pt-2 pb-1 px-3 text-[10px] uppercase tracking-wider text-zinc-600 hidden lg:block">
          Intelligence
        </div>
        <button
          onClick={() => setActiveTab('research')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'research' ? 'bg-amber-500/10 text-amber-400' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <Wand2 size={20} />
          <span className="font-medium hidden lg:block">Research</span>
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'analytics' ? 'bg-cyan-500/10 text-cyan-400' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <Activity size={20} />
          <span className="font-medium hidden lg:block">Analytics</span>
        </button>

        {/* <button
          onClick={() => setActiveTab('gallery')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'gallery' ? 'bg-primary/10 text-primary' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <LayoutGrid size={20} />
          <span className="font-medium hidden lg:block">Gallery</span>
        </button> */}

        <button
          onClick={() => setActiveTab('settings')}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-colors ${activeTab === 'settings' ? 'bg-primary/10 text-primary' : 'text-zinc-400 hover:text-white hover:bg-white/5'}`}
        >
          <Settings size={20} />
          <span className="font-medium hidden lg:block">Settings</span>
        </button>
      </nav>

      <div className="p-4 border-t border-white/5 space-y-2">
        <a
          href="#"
          onClick={(e) => { e.preventDefault(); localStorage.removeItem('openshorts_skip_landing'); window.location.hash = ''; window.location.reload(); }}
          className="flex items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-xl transition-colors group"
        >
          <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center shrink-0">
            <Globe size={16} />
          </div>
          <div className="hidden lg:block overflow-hidden">
            <p className="text-sm font-bold text-white leading-none mb-0.5">Landing Page</p>
            <p className="text-[10px] text-zinc-400 group-hover:text-zinc-300 transition-colors truncate">View website</p>
          </div>
        </a>
        <a
          href="https://github.com/Jahanzaib211/content-factory"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 p-3 bg-white/5 hover:bg-white/10 rounded-xl transition-colors group"
        >
          <div className="w-8 h-8 rounded-full bg-white text-black flex items-center justify-center shrink-0">
            <svg height="20" viewBox="0 0 16 16" version="1.1" width="20" aria-hidden="true"><path fillRule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
          </div>
          <div className="hidden lg:block overflow-hidden">
            <p className="text-sm font-bold text-white leading-none mb-0.5">Open Source</p>
            <p className="text-[10px] text-zinc-400 group-hover:text-zinc-300 transition-colors truncate">Free & Community Driven</p>
          </div>
        </a>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-background overflow-hidden selection:bg-primary/30">
      <Sidebar />

      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Background Gradients */}
        <div className="absolute inset-0 overflow-hidden -z-10 pointer-events-none">
          <div className="absolute -top-[10%] -right-[10%] w-[50%] h-[50%] bg-primary/5 rounded-full blur-[120px]" />
        </div>

        {/* Top Header */}
        <header className="h-16 border-b border-white/5 bg-background/50 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-10">
          <div className="flex items-center gap-4">
            {status !== 'idle' && (
              <button
                onClick={handleReset}
                className="flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors"
              >
                <PlusCircle size={16} />
                <span className="hidden sm:inline">New Project</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-4">
            {userProfiles.length > 0 && (
              <UserProfileSelector
                profiles={userProfiles}
                selectedUserId={uploadUserId}
                onSelect={setUploadUserId}
              />
            )}

            {(!apiKey && !minimaxKey) && (
              <button
                onClick={() => setActiveTab('settings')}
                className="text-xs text-amber-400 bg-amber-500/10 hover:bg-amber-500/20 px-3 py-1 rounded-full border border-amber-500/30 transition-colors flex items-center gap-1.5"
                title="Set your AI provider key (Gemini or MiniMax)"
              >
                <AlertTriangle size={12} />
                AI Provider Key Missing
              </button>
            )}
          </div>
        </header>

        {/* Persistent Missing Keys Banner — AI provider only. Upload-Post is opt-in for publishing. */}
        {(!apiKey && !minimaxKey) && activeTab !== 'settings' && (
          <div className="mx-6 mt-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center justify-between gap-4 shrink-0 animate-[fadeIn_0.3s_ease-out]">
            <div className="flex items-center gap-3 text-sm text-amber-200">
              <KeyRound size={16} className="shrink-0 text-amber-400" />
              <div>
                <span className="font-semibold">AI provider key required.</span>{' '}
                <span className="text-amber-200/80">
                  Set your <strong className="text-amber-100">Gemini</strong> or <strong className="text-amber-100">MiniMax</strong> API key to generate clips, titles, and edits.
                </span>
              </div>
            </div>
            <button
              onClick={() => setActiveTab('settings')}
              className="shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black transition-colors"
            >
              Go to Settings
            </button>
          </div>
        )}

        {/* Optional Upload-Post reminder — only when user has results and is missing the publish key */}
        {!uploadPostKey && results && (status === 'complete' || results?.clips?.length > 0) && activeTab !== 'settings' && (
          <div className="mx-6 mt-3 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-between gap-4 shrink-0 animate-[fadeIn_0.3s_ease-out]">
            <div className="flex items-center gap-3 text-sm text-emerald-200">
              <Share2 size={16} className="shrink-0 text-emerald-400" />
              <div>
                <span className="font-semibold">Want to publish to TikTok / Reels / YouTube?</span>{' '}
                <span className="text-emerald-200/80">
                  Add your <strong className="text-emerald-100">Upload-Post</strong> key to enable one-click posting (optional).
                </span>
              </div>
            </div>
            <button
              onClick={() => setActiveTab('settings')}
              className="shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black transition-colors"
            >
              Configure
            </button>
          </div>
        )}

        {/* Session Recovery Banner */}
        {sessionRecovered && (
          <div className="mx-6 mt-2 p-3 bg-primary/10 border border-primary/20 rounded-xl flex items-center justify-between animate-[fadeIn_0.3s_ease-out] shrink-0">
            <div className="flex items-center gap-2 text-sm text-primary">
              <RotateCcw size={16} />
              <span className="font-medium">Session recovered</span>
              <span className="text-zinc-400 text-xs">Your previous work has been restored.</span>
            </div>
            <button onClick={() => setSessionRecovered(false)} className="text-zinc-500 hover:text-white transition-colors">
              <X size={14} />
            </button>
          </div>
        )}

        {/* Main Workspace */}
        <div className="flex-1 overflow-hidden relative">

          {/* View: Settings */}
          {activeTab === 'settings' && (
            <div className="h-full overflow-y-auto p-8 max-w-2xl mx-auto animate-[fadeIn_0.3s_ease-out]">
              <div className="flex items-center justify-between mb-8">
                <h1 className="text-2xl font-bold">{t('settings.title')}</h1>
                <div className="px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full text-[10px] text-green-400 font-medium flex items-center gap-2">
                  <Shield size={12} /> Privacy: keys only live in your browser (sent to backend just to process)
                </div>
              </div>
              <KeyInput
                onKeySet={setApiKey}
                savedKey={apiKey}
                title="Gemini API Key"
                iconClass="bg-accent/20 text-accent"
                placeholder="AIzaSy..."
                getKeyHref="https://aistudio.google.com/app/apikey"
                getKeyLabel="Get your free Gemini API Key here"
                storageKey="gemini_key"
              />
              <MiniMaxKeyInput
                onKeySet={setMinimaxKey}
                savedKey={minimaxKey}
              />

              <div className={`glass-panel p-6 mt-8 ${!uploadPostKey ? 'border-amber-500/30 ring-1 ring-amber-500/20' : ''}`}>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Social Integration</h2>
                  <span className="text-[10px] bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded text-amber-400 uppercase tracking-wider">Required</span>
                </div>
                <p className="text-xs text-zinc-500 mb-6 leading-relaxed">
                  Required to publish your clips to TikTok, Instagram Reels, and YouTube Shorts via <strong>Upload-Post</strong>.
                  Includes a <strong>free tier</strong> (no credit card required).
                </p>
                <div className="space-y-4">
                  <label className="block text-sm text-zinc-400">Upload-Post API Key</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={uploadPostKey}
                      onChange={(e) => setUploadPostKey(e.target.value)}
                      className="input-field"
                      placeholder="ey..."
                    />
                    <button onClick={fetchUserProfiles} className="btn-primary py-2 px-4 text-sm">
                      Connect
                    </button>
                  </div>
                  <p className="text-xs text-zinc-500 leading-relaxed">
                    Connect your Upload-Post account to enable one-click publishing.
                    <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <a href="https://app.upload-post.com/login" target="_blank" rel="noopener noreferrer" className="p-2 border border-white/5 rounded-lg hover:bg-white/5 transition-colors flex flex-col gap-1">
                        <span className="text-zinc-400 font-medium">1. Login</span>
                        <span className="text-[10px] text-zinc-600">Register account</span>
                      </a>
                      <a href="https://app.upload-post.com/manage-users" target="_blank" rel="noopener noreferrer" className="p-2 border border-white/5 rounded-lg hover:bg-white/5 transition-colors flex flex-col gap-1">
                        <span className="text-zinc-400 font-medium">2. Profiles</span>
                        <span className="text-[10px] text-zinc-600">Create & Connect</span>
                      </a>
                      <a href="https://app.upload-post.com/api-keys" target="_blank" rel="noopener noreferrer" className="p-2 border border-white/5 rounded-lg hover:bg-white/5 transition-colors flex flex-col gap-1">
                        <span className="text-zinc-400 font-medium">3. API Key</span>
                        <span className="text-[10px] text-zinc-600">Generate key</span>
                      </a>
                    </div>
                    <br />
                    <span className="text-zinc-600 italic">
                      Keys are only stored in your browser. They are sent to the backend only to process your request, never stored server-side.
                    </span>
                  </p>
                </div>
              </div>

              <div className="glass-panel p-6 mt-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Video Translation</h2>
                  <span className="text-[10px] bg-white/5 border border-white/5 px-2 py-0.5 rounded text-zinc-500 uppercase tracking-wider">Optional</span>
                </div>
                <p className="text-xs text-zinc-500 mb-6 leading-relaxed">
                  Translate your clips to different languages using <strong>ElevenLabs</strong> AI dubbing.
                  Automatically translates speech while preserving the original voice characteristics.
                </p>
                <div className="space-y-4">
                  <label className="block text-sm text-zinc-400">ElevenLabs API Key</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={elevenLabsKey}
                      onChange={(e) => setElevenLabsKey(e.target.value)}
                      className="input-field"
                      placeholder="sk_..."
                    />
                    <button
                      onClick={() => {
                        if (elevenLabsKey) {
                          localStorage.setItem('elevenLabsKey_v1', encrypt(elevenLabsKey));
                          alert('ElevenLabs API Key saved!');
                        }
                      }}
                      className="btn-primary py-2 px-4 text-sm"
                    >
                      Save
                    </button>
                  </div>
                  <p className="text-xs text-zinc-500 leading-relaxed">
                    Get your API key from ElevenLabs to enable video translation.
                    <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <a href="https://elevenlabs.io/sign-up" target="_blank" rel="noopener noreferrer" className="p-2 border border-white/5 rounded-lg hover:bg-white/5 transition-colors flex flex-col gap-1">
                        <span className="text-zinc-400 font-medium">1. Sign Up</span>
                        <span className="text-[10px] text-zinc-600">Create account</span>
                      </a>
                      <a href="https://elevenlabs.io/app/settings/api-keys" target="_blank" rel="noopener noreferrer" className="p-2 border border-white/5 rounded-lg hover:bg-white/5 transition-colors flex flex-col gap-1">
                        <span className="text-zinc-400 font-medium">2. API Key</span>
                        <span className="text-[10px] text-zinc-600">Generate key</span>
                      </a>
                    </div>
                    <br />
                    <span className="text-zinc-600 italic">
                      Keys are only stored in your browser. They are sent to the backend only to process your request, never stored server-side.
                    </span>
                  </p>
                </div>
              </div>

              <div className="glass-panel p-6 mt-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">AI Shorts (UGC Videos)</h2>
                  <span className="text-[10px] bg-violet-500/10 border border-violet-500/20 px-2 py-0.5 rounded text-violet-400 uppercase tracking-wider">New</span>
                </div>
                <p className="text-xs text-zinc-500 mb-6 leading-relaxed">
                  Generate UGC-style videos with AI actors for any product or business using <strong>fal.ai</strong>.
                  Just describe your product or paste a URL. Requires fal.ai + ElevenLabs API keys.
                </p>
                <div className="space-y-4">
                  <label className="block text-sm text-zinc-400">fal.ai API Key</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={falKey}
                      onChange={(e) => setFalKey(e.target.value)}
                      className="input-field"
                      placeholder="fal_..."
                    />
                    <button
                      onClick={() => {
                        if (falKey) {
                          localStorage.setItem('falKey_v1', encrypt(falKey));
                          alert('fal.ai API Key saved!');
                        }
                      }}
                      className="btn-primary py-2 px-4 text-sm"
                    >
                      Save
                    </button>
                  </div>
                  <p className="text-xs text-zinc-500 leading-relaxed">
                    Get your API key from fal.ai to enable AI actor video generation.
                    <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <a href="https://fal.ai/dashboard/keys" target="_blank" rel="noopener noreferrer" className="p-2 border border-white/5 rounded-lg hover:bg-white/5 transition-colors flex flex-col gap-1">
                        <span className="text-zinc-400 font-medium">1. Sign Up</span>
                        <span className="text-[10px] text-zinc-600">Create fal.ai account</span>
                      </a>
                      <a href="https://fal.ai/dashboard/keys" target="_blank" rel="noopener noreferrer" className="p-2 border border-white/5 rounded-lg hover:bg-white/5 transition-colors flex flex-col gap-1">
                        <span className="text-zinc-400 font-medium">2. API Key</span>
                        <span className="text-[10px] text-zinc-600">Generate key</span>
                      </a>
                    </div>
                    <br />
                    <span className="text-zinc-600 italic">
                      Keys are only stored in your browser. Sent to backend only to process requests.
                    </span>
                  </p>
                </div>
              </div>

              {/* ── Content Factory: Active Engines card ─────────────── */}
              <div className="glass-panel p-6 mt-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Active Engines</h2>
                  <span className="text-[10px] bg-green-500/10 border border-green-500/30 px-2 py-0.5 rounded text-green-400 uppercase tracking-wider">Recommended</span>
                </div>
                <p className="text-xs text-zinc-500 mb-6 leading-relaxed">
                  Content Factory runs the AI pipeline through pluggable <strong>engines</strong>.
                  Each capability (LLM, TTS, image, video, voice clone, music) has one or more
                  registered providers. Pick the active one per capability. Defaults preserve
                  current behavior; legacy providers stay available.
                </p>

                <EnginePicker
                  enginesByCap={enginesByCap}
                  enginesHealth={enginesHealth}
                  onRefresh={fetchEngines}
                />
              </div>

              {/* ── Content Factory: Free & Open Source (built-in) ──── */}
              <div className="glass-panel p-6 mt-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Free &amp; Open Source (built-in)</h2>
                  <span className="text-[10px] bg-green-500/10 border border-green-500/30 px-2 py-0.5 rounded text-green-400 uppercase tracking-wider">No API key</span>
                </div>
                <p className="text-xs text-zinc-500 mb-6 leading-relaxed">
                  Components already bundled with Content Factory &mdash; zero API key needed.
                  Phase 5 will add local OSS fallbacks (vLLM, ComfyUI, Wan 2.1, CosyVoice) that
                  show up here as additional engine options.
                </p>
                <ul className="space-y-2 text-sm text-zinc-300">
                  {[
                    { name: 'faster-whisper', desc: 'Speech-to-text, 99 languages, word-level timestamps' },
                    { name: 'FFmpeg', desc: 'Video processing, composition, subtitle burning' },
                    { name: 'MediaPipe', desc: 'Face detection & tracking' },
                    { name: 'YOLOv8', desc: 'Person & object detection' },
                    { name: 'PySceneDetect', desc: 'Scene boundary detection' },
                    { name: 'LiteLLM', desc: 'LLM routing (MiniMax / Gemini / local)' },
                    { name: 'Local filesystem', desc: 'Storage backend (no S3 needed)' },
                  ].map((c) => (
                    <li key={c.name} className="flex items-start gap-2">
                      <Check size={14} className="text-green-400 shrink-0 mt-1" />
                      <span><strong className="text-white">{c.name}</strong> &mdash; {c.desc}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* ── Content Factory: Self-Hosted Stack status card ──── */}
              <div className="glass-panel p-6 mt-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Self-Hosted Stack</h2>
                  <span className="text-[10px] bg-zinc-700/50 border border-zinc-600/30 px-2 py-0.5 rounded text-zinc-400 uppercase tracking-wider">Optional</span>
                </div>
                <p className="text-xs text-zinc-500 mb-6 leading-relaxed">
                  Health probe for every registered engine. <span className="text-green-400">Green</span> = healthy,{' '}
                  <span className="text-amber-400">amber</span> = missing API key,{' '}
                  <span className="text-red-400">red</span> = error. The Phase 5 self-hosted services
                  (vLLM, ComfyUI, Wan 2.1, CosyVoice, faster-whisper) will appear here as additional
                  providers become registered.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {Object.keys(enginesByCap).filter((c) => enginesByCap[c] && enginesByCap[c].length > 0).length === 0 ? (
                    <div className="col-span-2 space-y-2">
                      {Array.from({ length: 4 }).map((_, i) => (
                        <Skeleton key={i} w="w-full" h="h-10" />
                      ))}
                    </div>
                  ) : (
                    Object.entries(enginesByCap).flatMap(([cap, providers]) =>
                      providers.map((p) => {
                        const health = enginesHealth[cap];
                        const healthy = health && health.healthy;
                        const missingKey = health && !health.healthy && health.detail && /not set|missing key/i.test(health.detail);
                        const color = healthy ? 'text-emerald-400' : missingKey ? 'text-amber-400' : 'text-red-400';
                        const dot = healthy ? 'bg-emerald-400 engine-dot-healthy' : missingKey ? 'bg-amber-400' : 'bg-red-400';
                        return (
                          <div key={`${cap}:${p.provider_id}`} className="flex items-center gap-2 p-2 border border-white/5 rounded-lg hover:border-white/10 transition-colors">
                            <span className={`w-2 h-2 rounded-full ${dot}`} />
                            <span className={`text-xs ${color} capitalize font-medium`}>{cap}</span>
                            <span className="text-xs text-zinc-300 truncate">{p.display_name}</span>
                          </div>
                        );
                      })
                    )
                  )}
                </div>
                <button
                  onClick={fetchEngines}
                  className="mt-4 text-xs text-zinc-400 hover:text-white border border-white/10 hover:bg-white/5 rounded-lg px-3 py-1.5 transition-colors"
                >
                  Refresh health
                </button>
              </div>

              {/* ── Content Factory: Multilingual settings card ── */}
              <div className="glass-panel p-6 mt-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Multilingual</h2>
                  <span className="text-[10px] bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded text-emerald-400 uppercase tracking-wider">Built-in</span>
                </div>
                <p className="text-xs text-zinc-500 mb-4 leading-relaxed">
                  Pick the dashboard language. Content translation (STT → LLM → TTS) is handled by the Multilingual panel.
                </p>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-zinc-400">UI language:</span>
                  <LangPicker />
                  <a
                    href="#/multilingual"
                    onClick={() => setActiveTab('multilingual')}
                    className="ml-auto text-xs text-emerald-400 hover:text-emerald-300"
                  >
                    Open Multilingual panel →
                  </a>
                </div>
              </div>

              {/* ── Content Factory: Direct Social OAuth (free tier) ── */}
              <div className="glass-panel p-6 mt-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Direct Social Publishing</h2>
                  <span className="text-[10px] bg-green-500/10 border border-green-500/30 px-2 py-0.5 rounded text-green-400 uppercase tracking-wider">Free tier</span>
                </div>
                <p className="text-xs text-zinc-500 mb-4 leading-relaxed">
                  Connect your accounts directly via OAuth. No third-party middleware. YouTube = 10k free units/day.
                  TikTok &amp; Instagram require a developer app (free, with review).
                  <strong className="text-zinc-300"> Tokens are stored server-side encrypted</strong> in
                  <code className="text-zinc-400"> output/social_tokens.json</code>.
                </p>
                <div className="space-y-2">
                  {[
                    { id: 'youtube', label: 'YouTube', env: 'YOUTUBE_CLIENT_ID + YOUTUBE_CLIENT_SECRET', url: 'https://console.cloud.google.com/apis/credentials' },
                    { id: 'tiktok', label: 'TikTok', env: 'TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET', url: 'https://developers.tiktok.com/apps' },
                    { id: 'instagram', label: 'Instagram', env: 'INSTAGRAM_APP_ID + INSTAGRAM_APP_SECRET', url: 'https://developers.facebook.com/apps' },
                  ].map((p) => (
                    <SocialConnectRow key={p.id} platform={p.id} label={p.label} env={p.env} devUrl={p.url} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* View: SaaS Shorts */}
          {activeTab === 'saasshorts' && (
            <SaaShortsTab geminiApiKey={apiKey} minimaxApiKey={minimaxKey} elevenLabsKey={elevenLabsKey} falKey={falKey} uploadPostKey={uploadPostKey} uploadUserId={uploadUserId} />
          )}

          {/* View: AI Agent */}
          {activeTab === 'ai-agent' && (
            <div className="h-full overflow-y-auto custom-scrollbar p-6 md:p-10 animate-[fadeIn_0.3s_ease-out]">
              <div className="max-w-4xl mx-auto space-y-8">

                {/* Header */}
                <div className="space-y-3">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-[11px] uppercase tracking-wider text-emerald-400 font-semibold">
                    <Bot size={12} /> Autonomous Skill
                  </div>
                  <h1 className="text-3xl md:text-4xl font-black bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent">
                    Your Personal Clipping Team
                  </h1>
                  <p className="text-zinc-400 text-base md:text-lg leading-relaxed max-w-2xl">
                    Drop your videos in a folder and a team of AI clippers picks the viral moments, edits them, and queues them for your approval — like having a 24/7 short-form editing crew on autopilot.
                  </p>
                </div>

                {/* Mobile-format warning */}
                <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 flex items-start gap-3">
                  <Smartphone size={20} className="text-amber-400 shrink-0 mt-0.5" />
                  <div className="text-sm text-amber-100">
                    <p className="font-semibold text-amber-300 mb-1">Upload videos already in vertical (9:16) mobile format.</p>
                    <p className="text-amber-100/80 leading-relaxed">
                      The agent does not reframe horizontal footage. Make sure every source video is shot or pre-cropped to mobile/portrait format before dropping it into the input folder.
                    </p>
                  </div>
                </div>

                {/* Workflow */}
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="glass-panel p-5 space-y-2">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                      <Upload size={18} />
                    </div>
                    <h3 className="font-semibold text-white">1. Drop your videos</h3>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      Put your long-form vertical footage in the watched folder. The skill picks one video per run.
                    </p>
                  </div>

                  <div className="glass-panel p-5 space-y-2">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                      <Users size={18} />
                    </div>
                    <h3 className="font-semibold text-white">2. AI clippers work</h3>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      Whisper transcribes, Gemini 3 Flash spots viral beats, FFmpeg cuts each clip and adds a hook overlay.
                    </p>
                  </div>

                  <div className="glass-panel p-5 space-y-2">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                      <CheckCircle2 size={18} />
                    </div>
                    <h3 className="font-semibold text-white">3. You validate, it ships</h3>
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      Approve the candidates you like and the skill auto-publishes them to TikTok, Reels and YouTube Shorts via Upload-Post.
                    </p>
                  </div>
                </div>

                {/* Repo CTA */}
                <div className="glass-panel p-6 md:p-8 space-y-5">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                      <h2 className="text-xl font-bold text-white mb-1">skill-autoshorts</h2>
                      <p className="text-sm text-zinc-400">
                        The Claude Code skill that powers this workflow. Install it once and trigger it whenever you want a fresh batch of clips.
                      </p>
                    </div>
                    <a
                      href="https://github.com/mutonby/skill-autoshorts"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-primary py-2 px-4 text-sm flex items-center gap-2 shrink-0"
                    >
                      View on GitHub <ExternalLink size={14} />
                    </a>
                  </div>

                  <div className="bg-[#0c0c0e] border border-white/10 rounded-lg p-4 font-mono text-xs text-zinc-300 flex items-center justify-between gap-3">
                    <span className="truncate">git clone https://github.com/mutonby/skill-autoshorts</span>
                    <button
                      onClick={() => navigator.clipboard.writeText('git clone https://github.com/mutonby/skill-autoshorts')}
                      className="text-zinc-500 hover:text-white transition-colors shrink-0"
                      title="Copy"
                    >
                      <Copy size={14} />
                    </button>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-3 text-sm">
                    <div className="flex items-start gap-2 text-zinc-300">
                      <Check size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                      <span>Daily batch — picks one long video per run</span>
                    </div>
                    <div className="flex items-start gap-2 text-zinc-300">
                      <Check size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                      <span>Whisper transcription with word-level timing</span>
                    </div>
                    <div className="flex items-start gap-2 text-zinc-300">
                      <Check size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                      <span>Gemini 3 Flash multimodal moment detection</span>
                    </div>
                    <div className="flex items-start gap-2 text-zinc-300">
                      <Check size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                      <span>Auto-publish to TikTok, Reels & YouTube Shorts</span>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* View: UGC Gallery */}
          {activeTab === 'ugc-gallery' && (
            <UGCGallery />
          )}

          {/* View: Content Factory (Phase 7) */}
          {activeTab === 'factory' && <ContentFactoryPanel />}
          {activeTab === 'voice-lab' && <VoiceLabPanel />}
          {activeTab === 'avatar-studio' && <AvatarStudioPanel />}
          {activeTab === 'multilingual' && <MultilingualPanel />}

          {/* View: Intelligence (Phase 8) */}
          {activeTab === 'research' && <ResearchPanel />}
          {activeTab === 'analytics' && <AnalyticsPanel />}

          {/* View: Thumbnails */}
          {activeTab === 'thumbnails' && (
            <ThumbnailStudio geminiApiKey={apiKey} minimaxApiKey={minimaxKey} uploadPostKey={uploadPostKey} uploadUserId={uploadUserId} />
          )}

          {/* View: Gallery */}
          {/* {activeTab === 'gallery' && (
            <Gallery />
          )} */}

          {/* View: Dashboard (Idle) */}
          {activeTab === 'dashboard' && status === 'idle' && (
            <div className="h-full flex flex-col items-center justify-center p-6 animate-[fadeIn_0.3s_ease-out]">
              <div className="max-w-xl w-full text-center space-y-8">
                <div className="space-y-4">
                  <h1 className="text-4xl md:text-5xl font-black bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent">
                    Create Viral Shorts
                  </h1>
                  <p className="text-zinc-400 text-lg">
                    Drop your long-form video below to instantly generate viral clips with AI.
                  </p>
                </div>

                <MediaInput onProcess={handleProcess} isProcessing={status === 'processing'} />

                <div className="flex items-center justify-center gap-8 text-zinc-500 text-sm">
                  <span className="flex items-center gap-2"><Youtube size={16} /> YouTube</span>
                  <span className="flex items-center gap-2"><Instagram size={16} /> Instagram</span>
                  <span className="flex items-center gap-2"><TikTokIcon size={16} /> TikTok</span>
                </div>
              </div>
            </div>
          )}

          {/* View: Processing / Results (Split View) */}
          {activeTab === 'dashboard' && (status === 'processing' || status === 'complete' || status === 'error') && (
            <div className="h-full flex flex-col md:flex-row animate-[fadeIn_0.3s_ease-out]">

              {/* Left Panel: Preview & Status */}
              <div className={`${status === 'complete' ? 'w-full md:w-[30%] lg:w-[25%]' : 'w-full md:w-[55%] lg:w-[60%]'} h-full flex flex-col border-r border-white/5 bg-black/20 p-6 overflow-y-auto custom-scrollbar transition-all duration-700 ease-in-out`}>
                <div className="mb-6 flex items-center justify-between">
                  <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Activity className={`text-primary ${status === 'processing' ? 'animate-pulse' : ''}`} size={20} />
                    Live Analysis
                  </h2>
                  <span className={`text-xs px-2 py-1 rounded-full border ${status === 'processing' ? 'bg-primary/10 border-primary/20 text-primary' :
                    status === 'complete' ? 'bg-green-500/10 border-green-500/20 text-green-400' :
                      'bg-red-500/10 border-red-500/20 text-red-400'
                    }`}>
                    {status.toUpperCase()}
                  </span>
                </div>

                {/* Video Preview */}
                {processingMedia && (
                  <ProcessingAnimation
                    media={processingMedia}
                    isComplete={status === 'complete'}
                    syncedTime={syncedTime}
                    isSyncedPlaying={isSyncedPlaying}
                    syncTrigger={syncTrigger}
                  />
                )}

                {/* Logs Terminal */}
                <div className={`bg-[#0c0c0e] rounded-xl border border-white/10 overflow-hidden flex flex-col transition-all duration-500 ${status === 'complete' ? 'h-32 min-h-0 opacity-50 hover:opacity-100' : 'flex-1 min-h-[200px]'}`}>
                  <div className="px-4 py-2 border-b border-white/5 flex items-center justify-between bg-white/5 shrink-0">
                    <span className="text-xs font-mono text-zinc-400 flex items-center gap-2">
                      <Terminal size={12} /> System Logs
                    </span>
                    <button onClick={() => setLogsVisible(!logsVisible)} className="text-zinc-500 hover:text-white transition-colors">
                      {logsVisible ? <ChevronDown size={14} /> : <ChevronDown size={14} className="rotate-180" />}
                    </button>
                  </div>
                  {logsVisible && (
                    <div className="flex-1 p-4 overflow-y-auto font-mono text-xs space-y-1.5 custom-scrollbar text-zinc-400">
                      {logs.map((log, i) => (
                        <div key={i} className={`flex gap-2 ${log.toLowerCase().includes('error') ? 'text-red-400' : 'text-zinc-400'}`}>
                          <span className="text-zinc-700 shrink-0">{new Date().toLocaleTimeString()}</span>
                          <span>{log}</span>
                        </div>
                      ))}
                      {status === 'processing' && (
                        <div className="animate-pulse text-primary/70">_</div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Right Panel: Results Grid */}
              <div className={`${status === 'complete' ? 'w-full md:w-[70%] lg:w-[75%]' : 'w-full md:w-[45%] lg:w-[40%]'} h-full flex flex-col bg-background p-6 transition-all duration-700 ease-in-out`}>
                <h2 className="text-lg font-semibold mb-6 flex items-center gap-2 shrink-0">
                  <Sparkles className="text-yellow-400" size={20} />
                  Generated Shorts
                  {results?.clips?.length > 0 && (
                    <span className="text-xs bg-white/10 text-white px-2 py-0.5 rounded-full ml-auto">
                      {results.clips.length} Clips
                    </span>
                  )}
                  {results?.cost_analysis && (
                    <span className="text-xs bg-green-500/10 border border-green-500/20 text-green-400 px-2 py-0.5 rounded-full ml-2" title={`Input: ${results.cost_analysis.input_tokens} | Output: ${results.cost_analysis.output_tokens}`}>
                      ${results.cost_analysis.total_cost.toFixed(5)}
                    </span>
                  )}
                  {results?.clips?.length > 1 && status === 'complete' && (
                    <button
                      onClick={() => setShowScheduleWeek(true)}
                      className="ml-auto flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-purple-500/20 to-indigo-500/20 hover:from-purple-500/30 hover:to-indigo-500/30 border border-purple-500/30 text-purple-300 hover:text-purple-200 rounded-full text-xs font-bold transition-all"
                    >
                      <Calendar size={14} />
                      Programar Semana
                    </button>
                  )}
                </h2>

                <div className="flex-1 overflow-y-auto custom-scrollbar p-1">
                  {results && results.clips && results.clips.length > 0 ? (
                    <div className={`grid gap-4 pb-10 ${status === 'complete' ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-1'}`}>
                      {results.clips.map((clip, i) => (
                        <ResultCard
                          key={i}
                          clip={clip}
                          index={i}
                          jobId={jobId}
                          uploadPostKey={uploadPostKey}
                          uploadUserId={uploadUserId}
                          geminiApiKey={apiKey}
                          minimaxApiKey={minimaxKey}
                          elevenLabsKey={elevenLabsKey}
                          onPlay={(time) => handleClipPlay(time)}
                          onPause={handleClipPause}
                        />
                      ))}
                    </div>
                  ) : (
                    status === 'processing' ? (
                      <div className="h-full flex flex-col items-center justify-center text-zinc-500 space-y-4 opacity-50">
                        <div className="w-12 h-12 rounded-full border-2 border-zinc-800 border-t-primary animate-spin" />
                        <p className="text-sm">Waiting for clips...</p>
                      </div>
                    ) : status === 'error' ? (
                      <div className="h-full flex flex-col items-center justify-center text-red-400 space-y-2">
                        <p>Generation failed.</p>
                      </div>
                    ) : null
                  )}
                </div>
              </div>

            </div>
          )}

        </div>

      </main>

      {/* Missing API Key Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowKeyModal(false)}>
          <div className="bg-[#18181b] border border-white/10 rounded-2xl p-6 max-w-md w-full mx-4 space-y-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold text-white">
              {(!apiKey && !minimaxKey) && !uploadPostKey
                ? 'Required API Keys Missing'
                : (!apiKey && !minimaxKey)
                  ? 'AI Provider Key Required'
                  : 'Upload-Post API Key Required'}
            </h2>
            <p className="text-sm text-zinc-400">
              Content Factory needs an <strong className="text-zinc-200">AI provider</strong> key (Gemini <em>or</em> MiniMax) and an <strong className="text-zinc-200">Upload-Post</strong> API key. Both have free tiers.
            </p>

            {/* Gemini block */}
            <div className={`rounded-lg p-4 space-y-2 border ${!apiKey ? 'bg-blue-500/5 border-blue-500/30' : 'bg-white/5 border-white/10 opacity-70'}`}>
              <p className="text-xs font-semibold text-zinc-200 flex items-center gap-2">
                {apiKey ? <Check size={12} className="text-green-400" /> : <AlertTriangle size={12} className="text-amber-400" />}
                Gemini API Key {apiKey && <span className="text-green-400">— set</span>}
              </p>
              {!apiKey && (
                <>
                  <ol className="text-xs text-zinc-400 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-blue-400 underline">aistudio.google.com/app/apikey</a></li>
                    <li>Sign in with your Google account</li>
                    <li>Click "Create API Key"</li>
                    <li>Copy the key and paste it below</li>
                  </ol>
                  <input
                    type="text"
                    placeholder="Paste your Gemini API key here..."
                    className="w-full bg-black/50 border border-white/20 rounded-lg px-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-blue-500"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.target.value.trim()) {
                        setApiKey(e.target.value.trim());
                      }
                    }}
                  />
                </>
              )}
            </div>

            {/* MiniMax block */}
            <div className={`rounded-lg p-4 space-y-2 border ${!minimaxKey ? 'bg-violet-500/5 border-violet-500/30' : 'bg-white/5 border-white/10 opacity-70'}`}>
              <p className="text-xs font-semibold text-zinc-200 flex items-center gap-2">
                {minimaxKey ? <Check size={12} className="text-green-400" /> : <AlertTriangle size={12} className="text-amber-400" />}
                MiniMax API Key {minimaxKey && <span className="text-green-400">— set</span>}{!minimaxKey && !apiKey && <span className="text-amber-400/70 ml-1">(alternative)</span>}
              </p>
              {!minimaxKey && (
                <>
                  <p className="text-xs text-zinc-400">
                    Use MiniMax instead of Gemini for video analysis, titles, and edits. Same OpenAI-compatible API.
                  </p>
                  <ol className="text-xs text-zinc-400 space-y-1 list-decimal list-inside">
                    <li>Go to <a href="https://api.MiniMax.io" target="_blank" rel="noopener noreferrer" className="text-violet-400 underline">api.MiniMax.io</a></li>
                    <li>Sign in and create an API key</li>
                    <li>Copy the key (starts with <code className="text-violet-300">sk-cp-</code> or <code className="text-violet-300">eyJ</code>) and paste it below</li>
                  </ol>
                  <input
                    type="text"
                    placeholder="sk-cp-..."
                    className="w-full bg-black/50 border border-white/20 rounded-lg px-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-violet-500"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.target.value.trim()) {
                        setMinimaxKey(e.target.value.trim());
                      }
                    }}
                  />
                </>
              )}
            </div>

            {/* Upload-Post block */}
            <div className={`rounded-lg p-4 space-y-2 border ${!uploadPostKey ? 'bg-emerald-500/5 border-emerald-500/30' : 'bg-white/5 border-white/10 opacity-70'}`}>
              <p className="text-xs font-semibold text-zinc-200 flex items-center gap-2">
                {uploadPostKey ? <Check size={12} className="text-green-400" /> : <AlertTriangle size={12} className="text-amber-400" />}
                Upload-Post API Key {uploadPostKey && <span className="text-green-400">— set</span>}
              </p>
              {!uploadPostKey && (
                <>
                  <p className="text-xs text-zinc-400">
                    Required to publish your clips to TikTok, Instagram Reels, and YouTube Shorts. Free tier available, no credit card needed.
                  </p>
                  <ol className="text-xs text-zinc-400 space-y-1 list-decimal list-inside">
                    <li>Register at <a href="https://app.upload-post.com/login" target="_blank" rel="noopener noreferrer" className="text-violet-400 underline">app.upload-post.com</a></li>
                    <li>Connect your TikTok, Instagram, or YouTube accounts</li>
                    <li>Go to <a href="https://app.upload-post.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-violet-400 underline">API Keys</a> and generate one</li>
                    <li>Paste it below</li>
                  </ol>
                  <input
                    type="text"
                    placeholder="Paste your Upload-Post API key here..."
                    className="w-full bg-black/50 border border-white/20 rounded-lg px-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.target.value.trim()) {
                        setUploadPostKey(e.target.value.trim());
                      }
                    }}
                  />
                </>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowKeyModal(false)}
                className="flex-1 text-sm text-zinc-400 py-2 rounded-lg border border-white/10 hover:bg-white/5 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => { setShowKeyModal(false); setActiveTab('settings'); }}
                className="flex-1 text-sm text-white py-2 rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors font-medium"
              >
                Go to Settings
              </button>
            </div>
          </div>
        </div>
      )}

      <ScheduleWeekModal
        isOpen={showScheduleWeek}
        onClose={() => setShowScheduleWeek(false)}
        clips={results?.clips || []}
        jobId={jobId}
        uploadPostKey={uploadPostKey}
        uploadUserId={uploadUserId}
      />
    </div>
  );
}

function LangPicker() {
  const { lang, setLang, SUPPORTED } = useT();
  return (
    <select
      value={lang}
      onChange={(e) => setLang(e.target.value)}
      className="bg-black/50 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-emerald-500"
    >
      {SUPPORTED.map((l) => (
        <option key={l} value={l}>{l.toUpperCase()}</option>
      ))}
    </select>
  );
}

export default function WrappedApp() {
  return (
    <I18nProvider>
      <App />
    </I18nProvider>
  );
}
