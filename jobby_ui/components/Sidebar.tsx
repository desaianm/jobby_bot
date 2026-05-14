'use client';

import { LayoutDashboard, Layers, MessageCircle, User, ChevronLeft, ChevronRight, Zap } from 'lucide-react';
import { View, Stats } from '@/lib/types';

const NAV_ITEMS: { id: View; label: string; icon: typeof LayoutDashboard; tone: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, tone: 'blue' },
  { id: 'pipeline',  label: 'Pipeline',  icon: Layers,          tone: 'accent' },
  { id: 'chat',      label: 'Chat',      icon: MessageCircle,   tone: 'green' },
  { id: 'profile',   label: 'Profile',   icon: User,            tone: 'purple' },
];

const TONE_MAP: Record<string, { bg: string; active: string; text: string }> = {
  blue:   { bg: 'var(--blue-soft)',   active: 'var(--blue)',   text: 'var(--blue-ink)' },
  accent: { bg: 'var(--accent-soft)', active: 'var(--accent)', text: 'white' },
  green:  { bg: 'var(--green-soft)',  active: 'var(--green)',  text: 'var(--green-ink)' },
  purple: { bg: 'var(--purple-soft)', active: 'var(--purple)', text: 'var(--purple-ink)' },
};

interface SidebarProps {
  view: View;
  onViewChange: (v: View) => void;
  stats: Stats;
  collapsed: boolean;
  onToggle: () => void;
  onRunPipeline: () => void;
}

export default function Sidebar({ view, onViewChange, stats, collapsed, onToggle, onRunPipeline }: SidebarProps) {
  return (
    <aside
      className="flex flex-col h-full flex-shrink-0 transition-all duration-200"
      style={{
        width: collapsed ? 64 : 220,
        background: 'var(--bg-alt)',
        borderRight: '1px solid var(--border)',
      }}
    >
      {/* Brand */}
      <div className="flex items-center gap-3 px-4 pt-5 pb-4">
        <div
          className="flex items-center justify-center flex-shrink-0 rounded-lg"
          style={{
            width: 34, height: 34,
            background: 'linear-gradient(135deg, var(--accent) 0%, #D4864E 100%)',
            boxShadow: '0 2px 8px rgba(200,107,58,0.25)',
          }}
        >
          <span className="font-display text-white text-lg font-bold" style={{ lineHeight: 1, marginTop: 1 }}>J</span>
        </div>
        {!collapsed && (
          <div className="flex flex-col" style={{ lineHeight: 1.1 }}>
            <span className="font-display text-[15px] font-semibold" style={{ color: 'var(--ink)', letterSpacing: '-0.02em' }}>Jobby</span>
            <span className="eyebrow mt-0.5" style={{ fontSize: 9, letterSpacing: '0.14em' }}>AI assistant</span>
          </div>
        )}
      </div>

      {/* Nav */}
      {!collapsed && <div className="eyebrow px-4 mb-1">Workspace</div>}
      <nav className="flex flex-col gap-1 px-2">
        {NAV_ITEMS.map((item) => {
          const active = view === item.id;
          const tone = TONE_MAP[item.tone];
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              title={collapsed ? item.label : undefined}
              className="flex items-center gap-2.5 rounded-lg transition-all duration-150"
              style={{
                padding: collapsed ? '10px' : '8px 10px',
                justifyContent: collapsed ? 'center' : 'flex-start',
                background: active ? tone.bg : 'transparent',
                color: active ? tone.text : 'var(--ink-3)',
              }}
            >
              <div
                className="flex items-center justify-center rounded-md flex-shrink-0"
                style={{
                  width: 28, height: 28,
                  background: active ? tone.active : 'var(--card)',
                  color: active ? 'white' : 'var(--ink-3)',
                  transition: 'all 0.15s ease',
                }}
              >
                <Icon size={14} strokeWidth={1.8} />
              </div>
              {!collapsed && (
                <span className="text-[13px] font-medium" style={{ color: active ? tone.text : 'var(--ink-2)' }}>
                  {item.label}
                </span>
              )}
              {!collapsed && item.id === 'pipeline' && stats.total > 0 && (
                <span
                  className="ml-auto font-mono text-[11px] font-bold rounded-full px-1.5"
                  style={{
                    background: active ? tone.active : 'var(--card)',
                    color: active ? 'white' : 'var(--ink-3)',
                  }}
                >
                  {stats.total}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Stats snapshot */}
      {!collapsed && (
        <>
          <div className="eyebrow px-4 mt-5 mb-2">Snapshot</div>
          <div className="grid grid-cols-3 gap-2 px-3">
            {([
              ['Ready', 'var(--green)', stats.ready],
              ['Applied', 'var(--accent)', stats.applied],
              ['New', 'var(--blue)', stats.discovered],
            ] as const).map(([label, color, n]) => (
              <div key={label} className="flex flex-col items-center py-2 rounded-lg" style={{ background: 'var(--card)' }}>
                <span className="font-mono text-[15px] font-extrabold" style={{ color, lineHeight: 1 }}>{n}</span>
                <span className="text-[9px] mt-1 font-medium" style={{ color: 'var(--ink-3)' }}>{label}</span>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="flex-1" />

      {/* Run pipeline shortcut */}
      {!collapsed && (
        <div className="px-3 mb-3">
          <button
            onClick={onRunPipeline}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-[13px] font-semibold transition-all duration-150"
            style={{
              background: 'linear-gradient(135deg, var(--accent) 0%, #D4864E 100%)',
              color: 'white',
              boxShadow: '0 2px 8px rgba(200,107,58,0.20)',
            }}
          >
            <Zap size={14} />
            Run Pipeline
          </button>
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center py-3 transition-colors"
        style={{ borderTop: '1px solid var(--border)', color: 'var(--ink-4)' }}
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </aside>
  );
}
