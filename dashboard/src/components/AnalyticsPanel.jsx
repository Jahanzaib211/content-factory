import React, { useState, useEffect } from 'react';
import { Activity, Youtube, TrendingUp, Loader2 } from 'lucide-react';
import { getApiUrl } from '../config';

export default function AnalyticsPanel() {
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
