'use client';

import { useState } from 'react';
import { Search, MapPin, Trash2, CheckSquare, Square } from 'lucide-react';
import { Job, TabFilter, Stats } from '@/lib/types';
import JobCard from './JobCard';

const CA_KEYWORDS = ['toronto', 'ontario', 'canada', 'vancouver', 'montreal', 'calgary', 'ottawa', ', on', ', bc', ', ab', ', qc'];

function isCanadianJob(job: Job): boolean {
  const loc = (job.location ?? '').toLowerCase();
  return CA_KEYWORDS.some((kw) => loc.includes(kw));
}

interface JobListProps {
  jobs: Job[];
  activeTab: TabFilter;
  onTabChange: (tab: TabFilter) => void;
  selectedJobId: number | null;
  onJobSelect: (job: Job) => void;
  stats: Stats;
  isLoading: boolean;
  onDeleteJobs: (ids: number[]) => void;
}

const tabs: { key: TabFilter; label: string; statKey: keyof Stats }[] = [
  { key: 'ready', label: 'Ready', statKey: 'ready' },
  { key: 'discovered', label: 'New', statKey: 'discovered' },
  { key: 'applied', label: 'Applied', statKey: 'applied' },
  { key: 'all', label: 'All', statKey: 'total' },
];

export default function JobList({
  jobs, activeTab, onTabChange, selectedJobId, onJobSelect, stats, isLoading, onDeleteJobs,
}: JobListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [canadaOnly, setCanadaOnly] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const filteredJobs = jobs.filter((job) => {
    if (canadaOnly && !isCanadianJob(job)) return false;
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return job.title.toLowerCase().includes(q) || job.company.toLowerCase().includes(q) || (job.location?.toLowerCase().includes(q) ?? false);
  });

  const allSelected = filteredJobs.length > 0 && filteredJobs.every((j) => selectedIds.has(j.id));

  const handleToggleAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredJobs.map((j) => j.id)));
    }
  };

  const handleDeleteSelected = () => {
    if (selectedIds.size === 0) return;
    onDeleteJobs(Array.from(selectedIds));
    setSelectedIds(new Set());
  };

  return (
    <div
      className="flex flex-col h-full flex-shrink-0"
      style={{ width: 380, minWidth: 380, background: 'var(--surface)', borderRight: '1px solid var(--border)' }}
    >
      {/* Tabs — underline style */}
      <div className="flex items-center gap-0.5 px-3 pt-3 flex-shrink-0" style={{ borderBottom: '1px solid var(--border)' }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { onTabChange(tab.key); setSelectedIds(new Set()); }}
            className="flex items-center gap-1.5 px-3 pb-2.5 text-[12px] font-semibold transition-colors relative"
            style={{ color: activeTab === tab.key ? 'var(--accent)' : 'var(--ink-3)' }}
          >
            {tab.label}
            <span
              className="font-mono text-[10px] font-bold px-1 rounded"
              style={{
                background: activeTab === tab.key ? 'var(--accent-soft)' : 'var(--card)',
                color: activeTab === tab.key ? 'var(--accent)' : 'var(--ink-4)',
              }}
            >
              {stats[tab.statKey]}
            </span>
            {/* Active underline */}
            {activeTab === tab.key && (
              <div
                className="absolute bottom-0 left-2 right-2 h-[2px] rounded-full"
                style={{ background: 'var(--accent)' }}
              />
            )}
          </button>
        ))}
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 flex-shrink-0" style={{ borderBottom: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2">
          <button onClick={handleToggleAll} className="p-1 rounded" style={{ color: 'var(--ink-3)' }}>
            {allSelected ? <CheckSquare size={14} /> : <Square size={14} />}
          </button>
          {selectedIds.size > 0 && (
            <>
              <span className="text-[11px] font-medium" style={{ color: 'var(--ink-3)' }}>{selectedIds.size} selected</span>
              <button
                onClick={handleDeleteSelected}
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium transition-colors"
                style={{ color: 'var(--red)', background: 'var(--red-soft)' }}
              >
                <Trash2 size={11} /> Delete
              </button>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setCanadaOnly((v) => !v)}
            title={canadaOnly ? 'Showing Canada only' : 'Show Canada only'}
            className="flex items-center gap-1 px-2 py-1.5 rounded-md text-[11px] font-medium transition-colors"
            style={{
              background: canadaOnly ? 'var(--red-soft)' : 'var(--card)',
              color: canadaOnly ? 'var(--red)' : 'var(--ink-3)',
              border: `1px solid ${canadaOnly ? 'var(--red)' : 'var(--border)'}`,
            }}
          >
            <MapPin size={10} /> 🍁
          </button>

          <div className="relative">
            <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2" style={{ color: 'var(--ink-4)' }} />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-warm text-[11px] pl-6 pr-3 py-1.5 w-24"
            />
          </div>
        </div>
      </div>

      {/* Job list */}
      <div className="flex-1 overflow-y-auto stagger-children">
        {isLoading ? (
          <div className="flex flex-col gap-3 p-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="animate-fadeInUp" style={{ animationDelay: `${i * 40}ms` }}>
                <div className="h-4 rounded w-3/4 mb-2" style={{ background: 'var(--card)', animation: 'shimmer 1.5s infinite', backgroundSize: '200% 100%', backgroundImage: `linear-gradient(90deg, var(--card) 0%, var(--hover) 50%, var(--card) 100%)` }} />
                <div className="h-3 rounded w-1/2 mb-1" style={{ background: 'var(--card)' }} />
                <div className="h-3 rounded w-1/3" style={{ background: 'var(--card)' }} />
              </div>
            ))}
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40" style={{ color: 'var(--ink-3)' }}>
            <p className="text-[13px]">No jobs found</p>
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="mt-2 text-[12px] font-medium" style={{ color: 'var(--accent)' }}>
                Clear search
              </button>
            )}
          </div>
        ) : (
          filteredJobs.map((job) => (
            <JobCard key={job.id} job={job} isSelected={selectedJobId === job.id} onClick={() => onJobSelect(job)} />
          ))
        )}
      </div>
    </div>
  );
}
