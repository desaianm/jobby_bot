'use client';

import { Layers, CheckCircle, Search, TrendingUp, ArrowRight, Flame, MessageSquare, Trophy } from 'lucide-react';
import { Job, Stats, View } from '@/lib/types';

interface DashboardProps {
  stats: Stats;
  jobs: Job[];
  onViewChange: (v: View) => void;
  onJobSelect: (job: Job) => void;
}

const STAT_CARDS: { key: keyof Stats; label: string; hint: string; icon: typeof Layers; tone: string }[] = [
  { key: 'total',      label: 'Total Jobs',  hint: 'In your pipeline',    icon: Layers,        tone: 'blue' },
  { key: 'applied',    label: 'Applied',     hint: 'Submitted',           icon: CheckCircle,   tone: 'accent' },
  { key: 'interview',  label: 'Interview',   hint: 'In progress',         icon: MessageSquare, tone: 'amber' },
  { key: 'offer',      label: 'Offers',      hint: 'Received',            icon: Trophy,        tone: 'green' },
  { key: 'ready',      label: 'Ready',       hint: 'Awaiting action',     icon: TrendingUp,    tone: 'purple' },
  { key: 'discovered', label: 'Discovered',  hint: 'Newly scraped',       icon: Search,        tone: 'blue' },
];

const TONE_STYLES: Record<string, { gradient: string; iconBg: string; textColor: string }> = {
  blue:   { gradient: 'linear-gradient(135deg, var(--blue-soft) 0%, rgba(255,255,255,0.5) 100%)', iconBg: 'var(--blue)', textColor: 'var(--blue-ink)' },
  green:  { gradient: 'linear-gradient(135deg, var(--green-soft) 0%, rgba(255,255,255,0.5) 100%)', iconBg: 'var(--green)', textColor: 'var(--green-ink)' },
  accent: { gradient: 'linear-gradient(135deg, var(--accent-soft) 0%, rgba(255,255,255,0.5) 100%)', iconBg: 'var(--accent)', textColor: '#7C3A1E' },
  purple: { gradient: 'linear-gradient(135deg, var(--purple-soft) 0%, rgba(255,255,255,0.5) 100%)', iconBg: 'var(--purple)', textColor: 'var(--purple-ink)' },
  amber:  { gradient: 'linear-gradient(135deg, var(--amber-soft) 0%, rgba(255,255,255,0.5) 100%)', iconBg: 'var(--amber)', textColor: 'var(--amber-ink)' },
};

function getFitColor(score: number): string {
  if (score >= 85) return 'var(--green)';
  if (score >= 70) return 'var(--amber)';
  return 'var(--red)';
}

export default function Dashboard({ stats, jobs, onViewChange, onJobSelect }: DashboardProps) {
  const topMatches = [...jobs]
    .filter((j) => j.fit_score !== undefined && j.fit_score !== null)
    .sort((a, b) => (b.fit_score ?? 0) - (a.fit_score ?? 0))
    .slice(0, 5);

  const recentJobs = [...jobs]
    .sort((a, b) => (b.id ?? 0) - (a.id ?? 0))
    .slice(0, 6);

  return (
    <div className="flex-1 overflow-y-auto" style={{ padding: 28 }}>
      {/* Hero */}
      <div
        className="rounded-xl p-6 mb-6 animate-fadeIn"
        style={{
          background: 'linear-gradient(135deg, var(--accent-soft) 0%, var(--purple-soft) 50%, var(--blue-soft) 100%)',
          border: '1px solid rgba(200,107,58,0.15)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <div className="eyebrow mb-2" style={{ color: 'var(--accent)' }}>Agent Online</div>
        <h1 className="font-display text-[36px] font-normal" style={{ letterSpacing: '-0.03em', lineHeight: 1.1 }}>
          The hunt is <em className="font-display" style={{ fontStyle: 'italic', color: 'var(--ink-2)' }}>on.</em>
        </h1>
        <p className="mt-2 text-[14px]" style={{ color: 'var(--ink-2)', maxWidth: 420 }}>
          {stats.total} jobs in your pipeline. {stats.applied} applied, {stats.interview} interviewing, {stats.offer} offers.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-4 mb-6 stagger-children">
        {STAT_CARDS.map((card) => {
          const tone = TONE_STYLES[card.tone];
          const Icon = card.icon;
          return (
            <div
              key={card.key}
              className="rounded-xl p-4 animate-fadeInUp"
              style={{
                background: tone.gradient,
                border: `1px solid color-mix(in srgb, ${tone.iconBg} 20%, transparent)`,
                minHeight: 110,
                display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
              }}
            >
              <div
                className="flex items-center justify-center rounded-lg"
                style={{ width: 32, height: 32, background: tone.iconBg, color: 'white' }}
              >
                <Icon size={14} />
              </div>
              <div className="mt-3">
                <div className="font-display font-bold" style={{ fontSize: 30, color: tone.textColor, lineHeight: 1 }}>
                  {stats[card.key]}
                </div>
                <div className="text-[12px] font-semibold mt-1">{card.label}</div>
                <div className="eyebrow mt-0.5" style={{ fontSize: 9 }}>{card.hint}</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Top Matches */}
        <div className="card-warm rounded-xl p-5 animate-fadeInUp" style={{ animationDelay: '100ms' }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Flame size={14} style={{ color: 'var(--accent)' }} />
              <span className="text-[13px] font-bold" style={{ color: 'var(--accent)' }}>Top Matches</span>
            </div>
            <button
              onClick={() => onViewChange('pipeline')}
              className="flex items-center gap-1 text-[11px] font-medium"
              style={{ color: 'var(--ink-3)' }}
            >
              View all <ArrowRight size={10} />
            </button>
          </div>
          {topMatches.length === 0 ? (
            <p className="text-[13px]" style={{ color: 'var(--ink-3)' }}>No scored jobs yet. Run the pipeline to discover matches.</p>
          ) : (
            <div className="flex flex-col gap-2 stagger-children">
              {topMatches.map((job) => (
                <button
                  key={job.id}
                  onClick={() => { onJobSelect(job); onViewChange('pipeline'); }}
                  className="lift flex items-center gap-3 p-2.5 rounded-lg text-left transition-colors"
                  style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
                >
                  <div
                    className="flex items-center justify-center rounded-md font-display text-[13px] font-bold flex-shrink-0"
                    style={{
                      width: 32, height: 32,
                      background: `color-mix(in srgb, ${getFitColor(job.fit_score!)} 12%, transparent)`,
                      border: `1px solid ${getFitColor(job.fit_score!)}`,
                      color: getFitColor(job.fit_score!),
                    }}
                  >
                    {job.fit_score}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[12px] font-semibold truncate">{job.title}</div>
                    <div className="text-[11px] truncate" style={{ color: 'var(--ink-3)' }}>{job.company}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Recent activity */}
        <div className="card-warm rounded-xl p-5 animate-fadeInUp" style={{ animationDelay: '150ms' }}>
          <div className="flex items-center justify-between mb-4">
            <span className="text-[13px] font-bold" style={{ color: 'var(--ink-2)' }}>Recent Jobs</span>
            <button
              onClick={() => onViewChange('pipeline')}
              className="flex items-center gap-1 text-[11px] font-medium"
              style={{ color: 'var(--ink-3)' }}
            >
              View all <ArrowRight size={10} />
            </button>
          </div>
          {recentJobs.length === 0 ? (
            <p className="text-[13px]" style={{ color: 'var(--ink-3)' }}>No jobs yet. Run the pipeline to start discovering.</p>
          ) : (
            <div className="flex flex-col gap-1.5 stagger-children">
              {recentJobs.map((job) => (
                <button
                  key={job.id}
                  onClick={() => { onJobSelect(job); onViewChange('pipeline'); }}
                  className="flex items-center gap-2.5 py-2 px-2 rounded-md text-left hover:bg-[var(--card)] transition-colors animate-fadeInUp"
                >
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{
                      background: job.status === 'offer' ? '#22c55e' : job.status === 'interview' ? 'var(--amber)' : job.status === 'applied' ? 'var(--purple)' : job.status === 'ready' ? 'var(--green)' : job.status === 'rejected' ? 'var(--red)' : 'var(--ink-4)',
                    }}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-[12px] font-medium truncate">{job.title}</div>
                    <div className="text-[10px] truncate" style={{ color: 'var(--ink-3)' }}>{job.company} · {job.location}</div>
                  </div>
                  <span className="eyebrow flex-shrink-0" style={{ fontSize: 9 }}>{job.status}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
