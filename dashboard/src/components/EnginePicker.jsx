import React from 'react';

export default function EnginePicker({ enginesByCap, enginesHealth, onRefresh }) {
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
