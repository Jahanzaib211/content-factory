import React, { useState, useEffect } from 'react';
import { Activity, Youtube, LayoutGrid, Languages, Sparkles, FileVideo, Users, Globe, Type, Monitor, Layers } from 'lucide-react';
import { getApiUrl } from '../config';
import { Skeleton, EmptyState, toast } from './CFUI';
import DirectPublishButton from './DirectPublishButton';

export default function ContentFactoryPanel() {
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
