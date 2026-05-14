'use client';

import { Job } from '@/lib/types';

interface StatusBadgeProps {
  status: Job['status'];
  className?: string;
}

const statusConfig: Record<Job['status'], { label: string; bg: string; color: string; border: string }> = {
  ready: {
    label: 'READY',
    bg: 'var(--green-soft)',
    color: 'var(--green-ink)',
    border: 'var(--green)',
  },
  discovered: {
    label: 'DISCOVERED',
    bg: 'var(--blue-soft)',
    color: 'var(--blue-ink)',
    border: 'var(--blue)',
  },
  applied: {
    label: 'APPLIED',
    bg: 'var(--purple-soft)',
    color: 'var(--purple-ink)',
    border: 'var(--purple)',
  },
  interview: {
    label: 'INTERVIEW',
    bg: 'var(--amber-soft)',
    color: 'var(--amber-ink)',
    border: 'var(--amber)',
  },
  offer: {
    label: 'OFFER',
    bg: 'var(--green-soft)',
    color: '#1a5c2a',
    border: '#22c55e',
  },
  rejected: {
    label: 'REJECTED',
    bg: 'var(--red-soft)',
    color: 'var(--red)',
    border: 'var(--red)',
  },
  archived: {
    label: 'ARCHIVED',
    bg: 'var(--card)',
    color: 'var(--ink-3)',
    border: 'var(--ink-4)',
  },
};

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const config = statusConfig[status] ?? statusConfig.discovered;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold tracking-wider ${className}`}
      style={{
        background: config.bg,
        color: config.color,
        border: `1px solid color-mix(in srgb, ${config.border} 30%, transparent)`,
      }}
    >
      {config.label}
    </span>
  );
}
