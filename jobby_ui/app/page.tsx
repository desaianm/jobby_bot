'use client';

import { useState, useCallback, useEffect } from 'react';
import { SWRConfig } from 'swr';
import Sidebar from '@/components/Sidebar';
import Dashboard from '@/components/Dashboard';
import JobList from '@/components/JobList';
import JobDetail from '@/components/JobDetail';
import ChatPanel from '@/components/ChatPanel';
import ProfilePanel from '@/components/ProfilePanel';
import RunPipelineModal from '@/components/RunPipelineModal';
import { useJobs, useStats } from '@/hooks/useJobs';
import { api } from '@/lib/api';
import { Job, TabFilter, View, PipelineRequest, Preset } from '@/lib/types';

function App() {
  const [view, setView] = useState<View>('dashboard');
  const [activeTab, setActiveTab] = useState<TabFilter>('discovered');
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isPipelineModalOpen, setIsPipelineModalOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Fetch all jobs for dashboard (unfiltered)
  const { jobs: allJobs, mutate: mutateAllJobs } = useJobs('all');
  const { jobs: filteredJobs, isLoading, mutate: mutateJobs } = useJobs(activeTab);
  const { stats, mutate: mutateStats } = useStats();

  // Persist sidebar state
  useEffect(() => {
    const saved = localStorage.getItem('jobby-sidebar-collapsed');
    if (saved === '1') setSidebarCollapsed(true);
  }, []);
  useEffect(() => {
    localStorage.setItem('jobby-sidebar-collapsed', sidebarCollapsed ? '1' : '0');
  }, [sidebarCollapsed]);

  const handleTabChange = useCallback((tab: TabFilter) => {
    setActiveTab(tab);
    setSelectedJob(null);
  }, []);

  const handleJobSelect = useCallback((job: Job) => {
    setSelectedJob(job);
  }, []);

  const handleJobUpdate = useCallback(
    async (id: number, data: Partial<Job>) => {
      try {
        const updated = await api.updateJob(id, data);
        setSelectedJob((prev) => (prev?.id === id ? { ...prev, ...updated } : prev));
        await mutateJobs();
        await mutateAllJobs();
        await mutateStats();
      } catch (err) {
        console.error('Failed to update job:', err);
      }
    },
    [mutateJobs, mutateAllJobs, mutateStats]
  );

  const handleDeleteJobs = useCallback(
    async (ids: number[]) => {
      for (const id of ids) {
        try {
          await api.updateJob(id, { status: 'archived' });
        } catch (err) {
          console.error('Failed to archive job:', err);
        }
      }
      if (selectedJob && ids.includes(selectedJob.id)) setSelectedJob(null);
      await mutateJobs();
      await mutateAllJobs();
      await mutateStats();
    },
    [selectedJob, mutateJobs, mutateAllJobs, mutateStats]
  );

  const handleRunPipeline = useCallback(async (data: PipelineRequest) => {
    await api.runPipeline(data);
    await mutateJobs();
    await mutateAllJobs();
    await mutateStats();
  }, [mutateJobs, mutateAllJobs, mutateStats]);

  const handleRunPreset = useCallback((preset: Preset) => {
    handleRunPipeline({
      search_term: preset.search_term,
      location: preset.location,
      is_remote: preset.is_remote,
      results_wanted: preset.results_wanted,
      country_indeed: preset.country_indeed,
    });
  }, [handleRunPipeline]);

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg)' }}>
      {/* Sidebar */}
      <Sidebar
        view={view}
        onViewChange={setView}
        stats={stats}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
        onRunPipeline={() => setIsPipelineModalOpen(true)}
      />

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0 min-h-0">
        {view === 'dashboard' && (
          <Dashboard
            stats={stats}
            jobs={allJobs}
            onViewChange={setView}
            onJobSelect={(job) => { setSelectedJob(job); setView('pipeline'); }}
          />
        )}

        {view === 'pipeline' && (
          <div className="flex flex-1 overflow-hidden">
            <JobList
              jobs={filteredJobs}
              activeTab={activeTab}
              onTabChange={handleTabChange}
              selectedJobId={selectedJob?.id ?? null}
              onJobSelect={handleJobSelect}
              stats={stats}
              isLoading={isLoading}
              onDeleteJobs={handleDeleteJobs}
            />
            <JobDetail job={selectedJob} onUpdate={handleJobUpdate} />
          </div>
        )}

        {view === 'chat' && <ChatPanel />}

        {view === 'profile' && <ProfilePanel onRunPreset={handleRunPreset} />}
      </main>

      {/* Pipeline modal */}
      <RunPipelineModal
        isOpen={isPipelineModalOpen}
        onClose={() => setIsPipelineModalOpen(false)}
        onSubmit={handleRunPipeline}
      />
    </div>
  );
}

export default function Home() {
  return (
    <SWRConfig value={{ revalidateOnFocus: false, dedupingInterval: 5000, errorRetryCount: 2 }}>
      <App />
    </SWRConfig>
  );
}
