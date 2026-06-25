import React, { useState, useEffect } from 'react';
import { getApiUrl } from '../config';
import { toast } from './CFUI';

export default function SocialConnectRow({ platform, label, env, devUrl }) {
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
