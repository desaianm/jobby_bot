'use client';

import { useState } from 'react';
import { X, Zap } from 'lucide-react';
import { PipelineRequest } from '@/lib/types';

interface RunPipelineModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: PipelineRequest) => void;
}

export default function RunPipelineModal({ isOpen, onClose, onSubmit }: RunPipelineModalProps) {
  const [form, setForm] = useState<PipelineRequest>({
    search_term: '', location: 'Toronto, ON', is_remote: false, results_wanted: 25, country_indeed: 'Canada',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.search_term.trim()) { setError('Search term is required'); return; }
    setError(null);
    setIsSubmitting(true);
    try { await onSubmit(form); onClose(); } catch (err) { setError(err instanceof Error ? err.message : 'Failed'); } finally { setIsSubmitting(false); }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center animate-fadeIn"
      style={{ background: 'rgba(30,24,16,0.25)', backdropFilter: 'blur(4px)' }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="card-warm rounded-xl w-full max-w-md mx-4 animate-fadeInUp" style={{ boxShadow: 'var(--shadow-lg)' }}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: '1px solid var(--border)' }}>
          <div>
            <h2 className="font-display text-[17px] font-semibold" style={{ letterSpacing: '-0.02em' }}>Run Pipeline</h2>
            <p className="text-[11px] mt-0.5" style={{ color: 'var(--ink-3)' }}>Configure and launch a job search</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-md transition-colors" style={{ color: 'var(--ink-3)' }}>
            <X size={16} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-5 py-4 flex flex-col gap-4">
          <div>
            <label className="eyebrow block mb-1.5">Search Term <span style={{ color: 'var(--accent)' }}>*</span></label>
            <input type="text" value={form.search_term} onChange={(e) => setForm({ ...form, search_term: e.target.value })} placeholder="e.g. Senior Software Engineer" className="input-warm w-full" />
          </div>
          <div>
            <label className="eyebrow block mb-1.5">Location</label>
            <input type="text" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="e.g. Toronto, ON" className="input-warm w-full" />
          </div>
          <div>
            <label className="eyebrow block mb-1.5">Country</label>
            <select value={form.country_indeed} onChange={(e) => setForm({ ...form, country_indeed: e.target.value })} className="input-warm w-full">
              <option value="Canada">Canada</option>
              <option value="USA">USA</option>
              <option value="UK">United Kingdom</option>
              <option value="Australia">Australia</option>
            </select>
          </div>
          <div>
            <label className="eyebrow block mb-1.5">Max Results</label>
            <input type="number" min={1} max={100} value={form.results_wanted} onChange={(e) => setForm({ ...form, results_wanted: parseInt(e.target.value, 10) || 25 })} className="input-warm w-full" />
          </div>

          {/* Remote toggle */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[13px] font-medium">Remote only</p>
              <p className="text-[11px] mt-0.5" style={{ color: 'var(--ink-3)' }}>Filter for remote positions</p>
            </div>
            <button
              type="button"
              onClick={() => setForm({ ...form, is_remote: !form.is_remote })}
              className="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
              style={{ background: form.is_remote ? 'var(--accent)' : 'var(--ink-4)' }}
            >
              <span className="inline-block h-4 w-4 transform rounded-full bg-white transition-transform" style={{ transform: form.is_remote ? 'translateX(22px)' : 'translateX(4px)', boxShadow: 'var(--shadow-xs)' }} />
            </button>
          </div>

          {error && <p className="text-[12px] px-3 py-2 rounded-lg" style={{ color: 'var(--red)', background: 'var(--red-soft)' }}>{error}</p>}

          <div className="flex items-center gap-3 pt-1">
            <button type="button" onClick={onClose} className="btn-warm flex-1 justify-center">Cancel</button>
            <button type="submit" disabled={isSubmitting} className="btn-accent flex-1 justify-center disabled:opacity-60">
              <Zap size={13} />
              {isSubmitting ? 'Searching...' : 'Run Pipeline'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
