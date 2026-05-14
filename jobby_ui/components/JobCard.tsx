'use client';

import { Job } from '@/lib/types';

interface JobCardProps {
  job: Job;
  isSelected: boolean;
  onClick: () => void;
}

function getFitColor(score?: number): string {
  if (score === undefined || score === null) return 'var(--ink-4)';
  if (score >= 85) return 'var(--green)';
  if (score >= 70) return 'var(--amber)';
  return 'var(--red)';
}

export default function JobCard({ job, isSelected, onClick }: JobCardProps) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left px-4 py-3 flex items-start gap-3 transition-all duration-150 animate-fadeInUp"
      style={{
        borderBottom: '1px solid var(--border)',
        borderLeft: isSelected ? '3px solid var(--accent)' : '3px solid transparent',
        background: isSelected ? 'var(--accent-softer)' : 'var(--surface)',
      }}
      onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.background = 'var(--card)'; }}
      onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.background = 'var(--surface)'; }}
    >
      {/* Status dot */}
      <div className="flex-shrink-0 mt-1.5">
        <span
          className="block w-2 h-2 rounded-full"
          style={{
            background: job.status === 'ready' ? 'var(--green)' : job.status === 'applied' ? 'var(--purple)' : 'var(--ink-4)',
          }}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="text-[13px] font-semibold leading-snug truncate" style={{ color: 'var(--ink)' }}>
            {job.title}
          </p>
          {job.fit_score !== undefined && job.fit_score !== null && (
            <span
              className="font-mono text-[12px] font-extrabold flex-shrink-0 px-1.5 py-0.5 rounded"
              style={{
                color: getFitColor(job.fit_score),
                background: `color-mix(in srgb, ${getFitColor(job.fit_score)} 10%, transparent)`,
              }}
            >
              {job.fit_score}
            </span>
          )}
        </div>
        <p className="text-[11px] mt-0.5 truncate" style={{ color: 'var(--ink-3)' }}>
          {job.company}{job.location ? ` · ${job.location}` : ''}
        </p>
        {job.salary && (
          <p className="text-[10px] mt-0.5 truncate font-mono" style={{ color: 'var(--ink-4)' }}>{job.salary}</p>
        )}
      </div>
    </button>
  );
}
