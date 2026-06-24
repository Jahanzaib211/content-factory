// Shared UI primitives for Content Factory panels.
//
// Includes shimmer skeletons, status badges, and empty-state cards.
// All components are pure — no fetches, no side effects.

import { Loader2, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

// ── Skeleton (shimmer) ──────────────────────────────────────────────
// Use while data is loading. Pass `lines` for multi-line text, `w` for width.
export function Skeleton({ className = '', w = 'w-full', h = 'h-4', lines = 1 }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={`shimmer rounded-md ${w} ${h}`}
          style={{ width: i === lines - 1 && lines > 1 ? '70%' : undefined }}
        />
      ))}
    </div>
  );
}

// ── Card skeleton (full panel placeholder) ─────────────────────────
export function CardSkeleton({ className = '' }) {
  return (
    <div className={`glass-panel p-6 space-y-3 ${className}`}>
      <Skeleton w="w-1/3" h="h-6" />
      <Skeleton w="w-full" h="h-4" />
      <Skeleton w="w-5/6" h="h-4" />
      <Skeleton w="w-2/3" h="h-4" />
    </div>
  );
}

// ── Engine status pill ─────────────────────────────────────────────
export function EngineStatusPill({ status }) {
  if (!status) {
    return (
      <span className="inline-flex items-center gap-1.5 text-[10px] px-2 py-0.5 rounded-full bg-zinc-700/50 text-zinc-400 uppercase tracking-wider">
        <span className="w-1.5 h-1.5 rounded-full bg-zinc-500" />
        unknown
      </span>
    );
  }
  if (status.healthy) {
    return (
      <span className="inline-flex items-center gap-1.5 text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 uppercase tracking-wider">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 engine-dot-healthy" />
        healthy
      </span>
    );
  }
  const isMissingKey = /not set|missing key|api_key/i.test(status.detail || '');
  const color = isMissingKey ? 'amber' : 'red';
  const label = isMissingKey ? 'no key' : 'error';
  return (
    <span className={`inline-flex items-center gap-1.5 text-[10px] px-2 py-0.5 rounded-full bg-${color}-500/10 border border-${color}-500/20 text-${color}-400 uppercase tracking-wider`}>
      <span className={`w-1.5 h-1.5 rounded-full bg-${color}-400`} />
      {label}
    </span>
  );
}

// ── Empty state ───────────────────────────────────────────────────
export function EmptyState({ icon: Icon = Loader2, title, hint, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 text-zinc-400">
        <Icon size={24} />
      </div>
      <p className="text-zinc-300 font-medium mb-1">{title}</p>
      {hint && <p className="text-xs text-zinc-500 max-w-md">{hint}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

// ── Stat card ──────────────────────────────────────────────────────
export function StatCard({ icon: Icon, label, value, hint, tone = 'default' }) {
  const toneColors = {
    default: 'text-zinc-300',
    primary: 'text-primary',
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    violet: 'text-violet-400',
    pink: 'text-pink-400',
  };
  return (
    <div className="glass-panel p-4 stagger-item">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-zinc-500 uppercase tracking-wider">{label}</span>
        {Icon && <Icon size={14} className={toneColors[tone] || toneColors.default} />}
      </div>
      <div className={`text-2xl font-bold ${toneColors[tone] || toneColors.default}`}>{value}</div>
      {hint && <div className="text-[10px] text-zinc-500 mt-1">{hint}</div>}
    </div>
  );
}

// ── Step indicator ────────────────────────────────────────────────
export function StepIndicator({ steps, current }) {
  return (
    <div className="flex items-center gap-1">
      {steps.map((s, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={s} className="flex items-center gap-1">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
              done ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' :
              active ? 'bg-primary/20 text-primary border border-primary/40' :
              'bg-white/5 text-zinc-500 border border-white/10'
            }`}>
              {done ? <CheckCircle2 size={12} /> : i + 1}
            </div>
            {i < steps.length - 1 && (
              <div className={`w-4 h-px ${done ? 'bg-emerald-500/40' : 'bg-white/10'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Toast (minimal in-app notification) ───────────────────────────
let _toastId = 0;
export function toast(message, kind = 'info', ttl = 4000) {
  if (typeof document === 'undefined') return;
  const id = ++_toastId;
  const colors = {
    info: 'bg-zinc-800 border-zinc-700 text-white',
    success: 'bg-emerald-900/80 border-emerald-500/40 text-emerald-100',
    error: 'bg-red-900/80 border-red-500/40 text-red-100',
    warn: 'bg-amber-900/80 border-amber-500/40 text-amber-100',
  };
  const root = document.getElementById('cf-toast-root') || (() => {
    const el = document.createElement('div');
    el.id = 'cf-toast-root';
    el.className = 'fixed bottom-4 right-4 z-50 space-y-2';
    document.body.appendChild(el);
    return el;
  })();
  const el = document.createElement('div');
  el.className = `px-4 py-3 rounded-xl border backdrop-blur-md shadow-2xl text-sm max-w-sm content-fade ${colors[kind] || colors.info}`;
  el.textContent = message;
  root.appendChild(el);
  setTimeout(() => {
    el.style.transition = 'opacity 300ms';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 320);
  }, ttl);
}
