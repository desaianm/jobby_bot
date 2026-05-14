'use client';

import { useState } from 'react';
import {
  MapPin, Calendar, DollarSign, ExternalLink, Download, CheckCircle, FileText,
  ChevronDown, ChevronRight, Flame, Trash2, ArrowRight, Clock,
} from 'lucide-react';
import { Job } from '@/lib/types';
import StatusBadge from './StatusBadge';

interface JobDetailProps {
  job: Job | null;
  onUpdate: (id: number, data: Partial<Job>) => void;
}

const STATUS_FLOW: { value: Job['status']; label: string; bg: string; color: string; border: string }[] = [
  { value: 'discovered', label: 'Discovered', bg: 'var(--blue-soft)', color: 'var(--blue-ink)', border: 'color-mix(in srgb, var(--blue) 30%, transparent)' },
  { value: 'ready', label: 'Ready', bg: 'var(--green-soft)', color: 'var(--green-ink)', border: 'color-mix(in srgb, var(--green) 30%, transparent)' },
  { value: 'applied', label: 'Applied', bg: 'var(--purple-soft)', color: 'var(--purple-ink)', border: 'color-mix(in srgb, var(--purple) 30%, transparent)' },
  { value: 'interview', label: 'Interview', bg: 'var(--amber-soft)', color: 'var(--amber-ink)', border: 'color-mix(in srgb, var(--amber) 30%, transparent)' },
  { value: 'offer', label: 'Offer', bg: 'rgba(34,197,94,0.1)', color: '#1a5c2a', border: 'color-mix(in srgb, #22c55e 30%, transparent)' },
  { value: 'rejected', label: 'Rejected', bg: 'var(--red-soft)', color: 'var(--red)', border: 'color-mix(in srgb, var(--red) 30%, transparent)' },
];

function formatDescription(raw: string): string {
  return raw
    // Escape HTML
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // Bold: **text**
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:var(--ink);font-weight:600">$1</strong>')
    // Headings: lines that are entirely bold become h4
    .replace(/^(<strong[^>]*>)(.+?)(<\/strong>)$/gm, '<h4 style="font-size:14px;font-weight:700;color:var(--ink);margin:16px 0 6px;font-family:var(--font-display)">$2</h4>')
    // Horizontal rules: --- or ===
    .replace(/^-{3,}$/gm, '<hr style="border:none;border-top:1px solid var(--border);margin:12px 0"/>')
    .replace(/^={3,}$/gm, '<hr style="border:none;border-top:1px solid var(--border);margin:12px 0"/>')
    // Bullet points: * item or - item
    .replace(/^[*\-]\s+(.+)$/gm, '<li style="margin-left:16px;padding-left:4px;list-style:disc;margin-bottom:3px">$1</li>')
    // Wrap consecutive <li> in <ul>
    .replace(/((?:<li[^>]*>.*?<\/li>\n?)+)/g, '<ul style="margin:6px 0">$1</ul>')
    // Paragraphs: double newlines
    .replace(/\n{2,}/g, '</p><p style="margin:10px 0">')
    // Single newlines within paragraphs
    .replace(/\n/g, '<br/>')
    // Wrap in paragraph
    .replace(/^/, '<p style="margin:0">')
    .replace(/$/, '</p>');
}

function getFitColor(score?: number): string {
  if (score === undefined || score === null) return 'var(--ink-4)';
  if (score >= 85) return 'var(--green)';
  if (score >= 70) return 'var(--amber)';
  return 'var(--red)';
}

export default function JobDetail({ job, onUpdate }: JobDetailProps) {
  const [projectsExpanded, setProjectsExpanded] = useState(false);
  const [moreActionsExpanded, setMoreActionsExpanded] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  if (!job) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center" style={{ background: 'var(--bg)', color: 'var(--ink-4)' }}>
        <FileText size={48} className="mb-4 opacity-20" />
        <p className="font-display text-[18px]" style={{ color: 'var(--ink-3)' }}>Select a job to view details</p>
        <p className="text-[13px] mt-1">Choose a job from the pipeline on the left</p>
      </div>
    );
  }

  const handleStatusChange = async (newStatus: Job['status']) => {
    if (isUpdating || newStatus === job.status) return;
    setIsUpdating(true);
    try { await onUpdate(job.id, { status: newStatus }); } finally { setIsUpdating(false); }
  };

  const siteLabel = job.site?.toUpperCase() ?? 'JOB BOARD';

  return (
    <div className="flex-1 overflow-y-auto" style={{ background: 'var(--bg)' }}>
      <div className="max-w-3xl mx-auto px-6 py-6 animate-slideInRight">
        {/* Title */}
        <div className="flex items-start justify-between gap-4 mb-1">
          <h1 className="font-display text-[22px] flex-1" style={{ letterSpacing: '-0.02em', lineHeight: 1.2, color: 'var(--ink)' }}>
            {job.title}
          </h1>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span
              className="text-[10px] font-bold tracking-wider px-2 py-1 rounded"
              style={{ background: 'var(--blue-soft)', color: 'var(--blue-ink)', border: '1px solid color-mix(in srgb, var(--blue) 25%, transparent)' }}
            >
              {siteLabel}
            </span>
            {job.job_url && (
              <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-[11px] font-medium transition-colors" style={{ color: 'var(--ink-3)' }}>
                VIEW <ExternalLink size={11} />
              </a>
            )}
          </div>
        </div>

        <p className="text-[14px] mb-4" style={{ color: 'var(--ink-2)' }}>{job.company}</p>

        {/* Meta */}
        <div className="flex flex-wrap items-center gap-4 text-[13px] mb-4" style={{ color: 'var(--ink-2)' }}>
          {job.location && <span className="flex items-center gap-1.5"><MapPin size={13} style={{ color: 'var(--ink-3)' }} />{job.location}</span>}
          {job.date_posted && job.date_posted !== 'nan' && <span className="flex items-center gap-1.5"><Calendar size={13} style={{ color: 'var(--ink-3)' }} />{job.date_posted}</span>}
          {job.salary && <span className="flex items-center gap-1.5"><DollarSign size={13} style={{ color: 'var(--ink-3)' }} />{job.salary}</span>}
        </div>

        {/* Status row */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <StatusBadge status={job.status} />
          {job.status_updated_at && (
            <span className="flex items-center gap-1 text-[10px]" style={{ color: 'var(--ink-4)' }}>
              <Clock size={10} />
              {new Date(job.status_updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
          )}
        </div>

        {/* Status flow buttons */}
        <div className="flex items-center gap-1.5 mb-5 flex-wrap">
          {STATUS_FLOW.filter((s) => s.value !== job.status).map((s) => (
            <button
              key={s.value}
              onClick={() => handleStatusChange(s.value)}
              disabled={isUpdating}
              className="text-[11px] py-1 px-2.5 rounded-md font-medium border transition-colors disabled:opacity-50"
              style={{ background: s.bg, color: s.color, borderColor: s.border }}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Fit score */}
        {job.fit_score !== undefined && job.fit_score !== null && (
          <div className="mb-5">
            <div className="flex items-center justify-between mb-1.5">
              <span className="eyebrow">Fit Score</span>
              <span className="font-display text-[20px] font-bold" style={{ color: getFitColor(job.fit_score) }}>{job.fit_score}</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--card)' }}>
              <div
                className="h-full rounded-full"
                style={{ width: `${job.fit_score}%`, background: `linear-gradient(90deg, ${getFitColor(job.fit_score)}, color-mix(in srgb, ${getFitColor(job.fit_score)} 70%, var(--accent)))`, animation: 'barFill 0.6s ease-out' }}
              />
            </div>
          </div>
        )}

        {/* Actions grid */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <button className="btn-warm lift"><Download size={14} /> Download PDF</button>
          {job.job_url ? (
            <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="btn-warm lift"><ExternalLink size={14} /> Open Listing</a>
          ) : (
            <button disabled className="btn-warm opacity-50 cursor-not-allowed"><ExternalLink size={14} /> Open Listing</button>
          )}
        </div>

        {/* Fit Assessment */}
        {job.fit_assessment && (
          <div className="mb-5 animate-fadeInUp">
            <div className="flex items-center gap-2 mb-2">
              <Flame size={14} style={{ color: 'var(--accent)' }} />
              <span className="eyebrow" style={{ color: 'var(--accent)' }}>Fit Assessment</span>
            </div>
            <p className="card-warm rounded-lg p-3 text-[13px] leading-relaxed" style={{ color: 'var(--ink-2)' }}>{job.fit_assessment}</p>
          </div>
        )}

        {/* Tailored Summary */}
        {job.tailored_summary && (
          <div className="mb-5">
            <div className="eyebrow mb-2">Tailored Summary</div>
            <p className="card-warm rounded-lg p-3 text-[13px] leading-relaxed italic" style={{ color: 'var(--ink-2)' }}>{job.tailored_summary}</p>
          </div>
        )}

        {/* Description */}
        {job.description && job.description !== 'nan' && (
          <div className="mb-5">
            <div className="eyebrow mb-2">Job Description</div>
            <div
              className="card-warm rounded-lg px-5 py-4 text-[13.5px] leading-[1.75] max-h-[70vh] overflow-y-auto job-description"
              style={{ color: 'var(--ink-2)' }}
              dangerouslySetInnerHTML={{ __html: formatDescription(job.description) }}
            />
          </div>
        )}

        {/* Expandable sections */}
        <button
          onClick={() => setProjectsExpanded(!projectsExpanded)}
          className="w-full flex items-center justify-between btn-warm mb-2"
        >
          <span>Projects</span>
          {projectsExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        {projectsExpanded && (
          <div className="mb-3 px-3 py-3 rounded-lg text-[13px] italic" style={{ background: 'var(--card)', color: 'var(--ink-3)' }}>
            No projects linked to this job.
          </div>
        )}

        <button
          onClick={() => setMoreActionsExpanded(!moreActionsExpanded)}
          className="w-full flex items-center justify-between btn-warm"
        >
          <span>More actions</span>
          {moreActionsExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        {moreActionsExpanded && (
          <div className="mt-1 card-warm rounded-lg p-2 flex flex-col gap-0.5">
            <button className="text-left text-[13px] py-1.5 px-2 rounded-md transition-colors" style={{ color: 'var(--ink-2)' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--card)'; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
            >Send application email</button>
            <div style={{ borderTop: '1px solid var(--border)', margin: '4px 0' }} />
            <button
              onClick={() => handleStatusChange('archived')}
              disabled={isUpdating}
              className="flex items-center gap-2 text-left text-[13px] py-1.5 px-2 rounded-md transition-colors disabled:opacity-50"
              style={{ color: 'var(--red)' }}
            >
              <Trash2 size={13} /> Remove from list
            </button>
          </div>
        )}

        <div className="h-6" />
      </div>
    </div>
  );
}
