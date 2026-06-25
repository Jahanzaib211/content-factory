import React, { useState, useEffect } from 'react';
import { Check, X, AlertCircle, Loader2, Server, Key, RefreshCw, Zap } from 'lucide-react';
import { getApiUrl } from '../config';

export default function EngineStatusPanel() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const res = await fetch(getApiUrl('/api/engines/health'));
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHealth(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHealth(); }, []);

  const freeLocal = ['faster-whisper', 'edge-tts', 'mediapipe', 'yolov8', 'scenedetect', 'local', 'flux-local', 'comfyui', 'localdiffusion', 'edge_tts'];

  const isFree = (providerId) => {
    if (!providerId) return false;
    const id = providerId.toLowerCase();
    return freeLocal.some(k => id.includes(k)) || id.includes('local') || id.includes('free') || id === 'edge-tts' || id === 'faster-whisper';
  };

  const renderCapability = (cap, engines) => {
    if (!Array.isArray(engines)) return null;
    return (
      <div key={cap} className="bg-white/5 rounded-xl p-4 border border-white/5">
        <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Server size={12} className="text-zinc-500" />
          {cap.replace(/_/g, ' ')}
        </h3>
        <div className="space-y-1.5">
          {engines.map((e, i) => {
            const free = isFree(e.provider);
            return (
              <div key={i} className="flex items-center gap-2 text-xs">
                {e.healthy ? (
                  <Check size={12} className="text-emerald-400 shrink-0" />
                ) : (
                  <X size={12} className="text-red-400 shrink-0" />
                )}
                <span className="text-zinc-300 truncate flex-1">{e.display_name || e.provider}</span>
                {free ? (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">FREE</span>
                ) : e.requires_key ? (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 font-bold flex items-center gap-0.5">
                    <Key size={8} /> NEEDS KEY
                  </span>
                ) : (
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-400 font-bold">PAID</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const totalEngines = health ? Object.values(health).reduce((acc, v) => acc + (Array.isArray(v) ? v.length : 0), 0) : 0;
  const healthyCount = health ? Object.values(health).reduce((acc, v) => {
    if (!Array.isArray(v)) return acc;
    return acc + v.filter(e => e.healthy).length;
  }, 0) : 0;
  const freeCount = health ? Object.values(health).reduce((acc, v) => {
    if (!Array.isArray(v)) return acc;
    return acc + v.filter(e => isFree(e.provider)).length;
  }, 0) : 0;

  return (
    <div className="h-full flex flex-col overflow-hidden p-4 md:p-6 animate-[fadeIn_0.3s_ease-out]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Server size={20} /> Engine Status
          </h2>
          <p className="text-zinc-400 text-sm">Real-time health of all AI services</p>
        </div>
        <button onClick={fetchHealth} disabled={loading} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-zinc-400 disabled:opacity-50">
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {loading && !health && (
        <div className="flex-1 flex items-center justify-center text-zinc-400">
          <Loader2 className="animate-spin mr-2" size={20} /> Checking all engines...
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-center gap-2">
          <AlertCircle size={14} /> Failed to fetch engine health: {error}
        </div>
      )}

      {health && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3 text-center">
              <div className="text-lg font-bold text-emerald-400">{freeCount}</div>
              <div className="text-xs text-zinc-400 flex items-center justify-center gap-1">
                <Zap size={10} /> Free engines
              </div>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3 text-center">
              <div className="text-lg font-bold text-white">{healthyCount}/{totalEngines}</div>
              <div className="text-xs text-zinc-400">Healthy</div>
            </div>
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 text-center">
              <div className="text-lg font-bold text-amber-400">{totalEngines - healthyCount}</div>
              <div className="text-xs text-zinc-400 flex items-center justify-center gap-1">
                <Key size={10} /> Need key
              </div>
            </div>
          </div>

          {/* Engine grid */}
          <div className="flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(health).map(([cap, engines]) => renderCapability(cap, engines))}
          </div>
        </>
      )}
    </div>
  );
}