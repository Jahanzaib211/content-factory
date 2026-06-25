import React, { useState } from 'react';
import { Wand2, Zap, FileText, CheckCircle, Sparkles, Loader2 } from 'lucide-react';
import { getApiUrl } from '../config';

export default function ResearchPanel() {
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
