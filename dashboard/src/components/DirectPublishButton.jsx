// DirectPublishButton: one-click publish to YouTube / TikTok / Instagram
// via the new /api/social/post-video endpoint (direct OAuth, no Upload-Post).
// Shows a per-platform button based on connection status.
//
// Falls back to showing a "Connect <platform>" CTA if the user hasn't
// connected the account yet.

import { useEffect, useState } from 'react';
import { Youtube, Instagram, Send, Loader2, CheckCircle2, ExternalLink } from 'lucide-react';
import { getApiUrl } from '../config';

const PLATFORMS = [
  { id: 'youtube',  label: 'YouTube',    icon: Youtube,   color: 'red' },
  { id: 'tiktok',   label: 'TikTok',     icon: Send,      color: 'pink' },
  { id: 'instagram', label: 'Instagram', icon: Instagram, color: 'pink' },
];

export default function DirectPublishButton({ videoPath, title, description = '' }) {
  const [connections, setConnections] = useState({});
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState({}); // { youtube: bool, ... }
  const [result, setResult] = useState(null); // last publish result

  const fetchConnections = async () => {
    try {
      const r = await fetch(getApiUrl('/api/social/connections'));
      if (r.ok) setConnections(await r.json());
    } catch (_) {}
    finally { setLoading(false); }
  };
  useEffect(() => { fetchConnections(); }, []);

  const onPublish = async (platform) => {
    setPublishing((p) => ({ ...p, [platform]: true }));
    setResult(null);
    try {
      const fd = new FormData();
      fd.append('platform', platform);
      fd.append('video_path', videoPath);
      fd.append('title', title || 'Untitled');
      fd.append('description', description);
      const r = await fetch(getApiUrl('/api/social/post-video'), { method: 'POST', body: fd });
      const d = await r.json();
      if (!r.ok) {
        setResult({ platform, ok: false, detail: d.detail || r.statusText });
      } else {
        setResult({ platform, ok: true, url: d.url || d.id });
      }
    } catch (e) {
      setResult({ platform, ok: false, detail: e.message });
    } finally {
      setPublishing((p) => ({ ...p, [platform]: false }));
    }
  };

  if (loading) return <div className="shimmer h-9 w-48 rounded-lg" />;

  const connectedPlatforms = PLATFORMS.filter((p) => connections[p.id]?.connected);

  if (connectedPlatforms.length === 0) {
    return (
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <span>No social accounts connected.</span>
        <a href="#/settings" onClick={(e) => { e.preventDefault(); window.location.hash = '#app'; window.dispatchEvent(new CustomEvent('cf-navigate', { detail: 'settings' })); }} className="text-violet-400 hover:text-violet-300 underline">
          Connect in Settings →
        </a>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {connectedPlatforms.map((p) => {
        const Icon = p.icon;
        const busy = publishing[p.id];
        const isResult = result?.platform === p.id;
        const colorClass = p.color === 'red'
          ? 'bg-red-600 hover:bg-red-500'
          : 'bg-pink-600 hover:bg-pink-500';
        return (
          <div key={p.id} className="flex items-center gap-1">
            <button
              onClick={() => onPublish(p.id)}
              disabled={busy}
              className={`flex items-center gap-1.5 text-xs ${colorClass} disabled:opacity-50 text-white px-3 py-1.5 rounded-lg font-medium transition-all active:scale-95`}
              title={`Publish to ${p.label} via direct OAuth`}
            >
              {busy ? <Loader2 size={12} className="animate-spin" /> : <Icon size={12} />}
              {busy ? 'Publishing…' : p.label}
            </button>
            {isResult && result.ok && (
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300"
              >
                <CheckCircle2 size={12} /> View <ExternalLink size={10} />
              </a>
            )}
            {isResult && !result.ok && (
              <span className="text-xs text-red-400" title={result.detail}>failed</span>
            )}
          </div>
        );
      })}
    </div>
  );
}
