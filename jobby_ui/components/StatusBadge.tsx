'use client';

interface StatusBadgeProps {
  status: 'discovered' | 'ready' | 'applied' | 'archived';
  className?: string;
}

const statusConfig = {
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
