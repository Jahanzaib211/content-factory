import React, { useState, useEffect } from 'react';
import { RefreshCw, FileVideo, Image, Volume2, FileText, Trash2, Loader2, Play, X, Download, ExternalLink } from 'lucide-react';
import { getApiUrl } from '../config';
import { toast } from './CFUI';

export default function GalleryPanel() {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ source: '', template_id: '', status: '', tag: '', search: '' });
  const [editingItem, setEditingItem] = useState(null);
  const [caption, setCaption] = useState('');
  const [previewItem, setPreviewItem] = useState(null); // For inline video preview modal

  const fetchGallery = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.source) params.set('source', filter.source);
      if (filter.template_id) params.set('template_id', filter.template_id);
      if (filter.status) params.set('status', filter.status);
      if (filter.tag) params.set('tag', filter.tag);
      if (filter.search) params.set('search', filter.search);
      const url = getApiUrl(`/api/gallery?${params.toString()}`);
      const [itemsRes, statsRes] = await Promise.all([
        fetch(url).then(r => r.json()),
        fetch(getApiUrl('/api/gallery/stats')).then(r => r.json()),
      ]);
      setItems(itemsRes.items || []);
      setStats(statsRes);
    } catch (_) {
      toast('Failed to load gallery', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchGallery(); }, [filter]);

  const publish = async (item) => {
    try {
      const r = await fetch(getApiUrl(`/api/gallery/${item.id}/publish`), {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ caption: item.caption, tags: item.tags }),
      });
      if (r.ok) { toast('Published!', 'success'); fetchGallery(); }
      else toast('Publish failed', 'error');
    } catch { toast('Publish failed', 'error'); }
  };

  const deleteItem = async (item) => {
    if (!confirm('Delete this item?')) return;
    try {
      const r = await fetch(getApiUrl(`/api/gallery/${item.id}`), { method: 'DELETE' });
      if (r.ok) { toast('Deleted', 'success'); fetchGallery(); }
    } catch { toast('Delete failed', 'error'); }
  };

  const saveCaption = async () => {
    if (!editingItem) return;
    try {
      const r = await fetch(getApiUrl(`/api/gallery/${editingItem.id}`), {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ caption }),
      });
      if (r.ok) { toast('Saved', 'success'); setEditingItem(null); fetchGallery(); }
    } catch { toast('Save failed', 'error'); }
  };

  const typeColors = { video: 'text-violet-400', image: 'text-emerald-400', audio: 'text-amber-400', text: 'text-zinc-400' };
  const statusColors = { draft: 'bg-zinc-500/20 text-zinc-400', published: 'bg-emerald-500/20 text-emerald-400', failed: 'bg-red-500/20 text-red-400' };

  return (
    <div className="h-full flex flex-col overflow-hidden p-4 md:p-6 animate-[fadeIn_0.3s_ease-out]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Gallery</h2>
          <p className="text-zinc-400 text-sm">All generated content in one place</p>
        </div>
        <button onClick={fetchGallery} className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-zinc-400">
          <RefreshCw size={18} />
        </button>
      </div>

      {/* Stats bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
          {[
            ['Total', stats.total_items],
            ['Videos', stats.by_type?.video || 0],
            ['Images', stats.by_type?.image || 0],
            ['Audio', stats.by_type?.audio || 0],
            ['Published', stats.by_status?.published || 0],
          ].map(([label, val]) => (
            <div key={label} className="bg-white/5 rounded-xl p-3 text-center">
              <div className="text-lg font-bold text-white">{val}</div>
              <div className="text-xs text-zinc-400">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        <input
          type="text" placeholder="Search..."
          value={filter.search} onChange={e => setFilter(f => ({ ...f, search: e.target.value }))}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white w-48"
        />
        <select value={filter.source} onChange={e => setFilter(f => ({ ...f, source: e.target.value }))}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white">
          <option value="">All sources</option>
          <option value="clip">Clip</option><option value="factory">Factory</option>
          <option value="saasshorts">SaaShorts</option><option value="avatar">Avatar</option>
          <option value="multilingual">Multilingual</option><option value="upload">Upload</option>
        </select>
        <select value={filter.status} onChange={e => setFilter(f => ({ ...f, status: e.target.value }))}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white">
          <option value="">All statuses</option>
          <option value="draft">Draft</option><option value="published">Published</option>
        </select>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center text-zinc-400">
          <Loader2 className="animate-spin mr-2" size={20} /> Loading gallery...
        </div>
      ) : items.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-zinc-400">
          <Image size={48} className="mb-4 text-zinc-600" />
          <p className="text-lg">No items yet</p>
          <p className="text-sm">Content will appear here after generation</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {items.map(item => (
            <div key={item.id} className="bg-white/5 rounded-xl p-4 border border-white/5 hover:border-white/10 transition flex flex-col">
              {/* Thumbnail / Inline player for videos */}
              {item.file_type === 'video' ? (
                <div className="w-full aspect-[9/16] bg-zinc-800 rounded-lg mb-3 flex items-center justify-center relative overflow-hidden group">
                  <video
                    src={getApiUrl(item.file_url || `/api/gallery/${item.id}/file`)}
                    className="w-full h-full object-cover"
                    muted
                    playsInline
                    onMouseEnter={(e) => e.currentTarget.play().catch(() => {})}
                    onMouseLeave={(e) => { e.currentTarget.pause(); e.currentTarget.currentTime = 0; }}
                    onClick={() => setPreviewItem(item)}
                  />
                  <button
                    onClick={() => setPreviewItem(item)}
                    className="absolute inset-0 flex items-center justify-center bg-black/30 opacity-0 group-hover:opacity-100 transition cursor-pointer"
                  >
                    <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                      <Play size={20} className="text-white ml-1" />
                    </div>
                  </button>
                  <div className="absolute bottom-1 right-1 bg-black/70 text-xs px-1.5 py-0.5 rounded text-zinc-300">
                    {item.file_type}
                  </div>
                </div>
              ) : item.file_type === 'image' ? (
                <div className="w-full aspect-video bg-zinc-800 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
                  <img
                    src={getApiUrl(item.file_url || `/api/gallery/${item.id}/file`)}
                    alt={item.title}
                    className="w-full h-full object-cover cursor-pointer"
                    onClick={() => setPreviewItem(item)}
                  />
                </div>
              ) : item.file_type === 'audio' ? (
                <div className="w-full bg-zinc-800 rounded-lg mb-3 p-2">
                  <audio
                    src={getApiUrl(item.file_url || `/api/gallery/${item.id}/file`)}
                    controls
                    className="w-full h-8"
                  />
                </div>
              ) : (
                <div className="w-full h-16 bg-zinc-800 rounded-lg mb-3 flex items-center justify-center">
                  <FileText size={24} className="text-zinc-400/50" />
                </div>
              )}

              {/* Info */}
              <div className="flex-1">
                <div className="font-semibold text-white text-sm truncate">{item.title || 'Untitled'}</div>
                <div className="text-xs text-zinc-400 mt-1 line-clamp-2">{item.caption || 'No caption'}</div>
              </div>

              {/* Meta */}
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <span className={`text-xs font-mono ${typeColors[item.file_type] || 'text-zinc-400'}`}>{item.file_type}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[item.status] || 'bg-zinc-500/20 text-zinc-400'}`}>{item.status}</span>
                {item.file_size > 0 && (
                  <span className="text-xs text-zinc-500">{(item.file_size / 1048576).toFixed(1)}MB</span>
                )}
              </div>

              {/* Tags */}
              {item.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {item.tags.slice(0, 3).map(t => (
                    <span key={t} className="text-xs bg-white/5 text-zinc-400 px-1.5 py-0.5 rounded">#{t}</span>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-1.5 mt-3">
                <button onClick={() => { setEditingItem(item); setCaption(item.caption); }}
                  className="flex-1 text-xs bg-white/5 hover:bg-white/10 text-zinc-300 rounded-lg py-1.5 transition">
                  Edit
                </button>
                <button onClick={() => publish(item)}
                  className="flex-1 text-xs bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-lg py-1.5 transition">
                  Publish
                </button>
                <button onClick={() => deleteItem(item)}
                  className="text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg px-2 py-1.5 transition">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit modal */}
      {editingItem && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setEditingItem(null)}>
          <div className="bg-zinc-900 rounded-2xl p-6 w-full max-w-md border border-white/10" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white mb-4">Edit Caption</h3>
            <textarea value={caption} onChange={e => setCaption(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm h-24 resize-none mb-4" />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setEditingItem(null)} className="px-4 py-2 text-zinc-400 hover:text-white text-sm">Cancel</button>
              <button onClick={saveCaption} className="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/80">Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Inline Preview Modal */}
      {previewItem && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" onClick={() => setPreviewItem(null)}>
          <div className="relative max-w-2xl w-full" onClick={e => e.stopPropagation()}>
            <button
              onClick={() => setPreviewItem(null)}
              className="absolute -top-2 -right-2 z-10 w-10 h-10 rounded-full bg-zinc-900 hover:bg-zinc-800 flex items-center justify-center text-white border border-white/20"
              title="Close (Esc)"
            >
              <X size={20} />
            </button>
            <div className="bg-zinc-900 rounded-2xl overflow-hidden border border-white/10">
              <div className="bg-black flex items-center justify-center max-h-[70vh]">
                {previewItem.file_type === 'video' && (
                  <video
                    src={getApiUrl(previewItem.file_url || `/api/gallery/${previewItem.id}/file`)}
                    controls autoPlay
                    className="max-h-[70vh] w-auto"
                  />
                )}
                {previewItem.file_type === 'image' && (
                  <img
                    src={getApiUrl(previewItem.file_url || `/api/gallery/${previewItem.id}/file`)}
                    alt={previewItem.title}
                    className="max-h-[70vh] w-auto object-contain"
                  />
                )}
                {previewItem.file_type === 'audio' && (
                  <audio
                    src={getApiUrl(previewItem.file_url || `/api/gallery/${previewItem.id}/file`)}
                    controls autoPlay
                    className="w-full p-4"
                  />
                )}
              </div>
              <div className="p-4 flex items-center justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-semibold text-white truncate">{previewItem.title}</h3>
                  <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{previewItem.caption}</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <a
                    href={getApiUrl(previewItem.file_url || `/api/gallery/${previewItem.id}/file`)}
                    download
                    className="px-3 py-1.5 bg-violet-500/20 hover:bg-violet-500/30 text-violet-400 rounded-lg text-xs flex items-center gap-1.5"
                  >
                    <Download size={12} /> Download
                  </a>
                  <a
                    href={getApiUrl(previewItem.file_url || `/api/gallery/${previewItem.id}/file`)}
                    target="_blank" rel="noopener noreferrer"
                    className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-zinc-300 rounded-lg text-xs flex items-center gap-1.5"
                  >
                    <ExternalLink size={12} /> Open
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
