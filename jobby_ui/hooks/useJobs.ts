'use client';

import useSWR from 'swr';
import { api } from '@/lib/api';
import { Job, Stats, TabFilter } from '@/lib/types';

const statusMap: Record<TabFilter, string | undefined> = {
  all: undefined,
  ready: 'ready',
  discovered: 'discovered',
  applied: 'applied',
};

export function useJobs(activeTab: TabFilter) {
  const status = statusMap[activeTab];
  const key = status ? `/api/jobs?status=${status}` : '/api/jobs';

  const { data, error, isLoading, mutate } = useSWR<Job[]>(key, () =>
    api.getJobs(status)
  );

  return {
    jobs: data ?? [],
    isLoading,
    isError: !!error,
    mutate,
  };
}

export function useStats() {
  const { data, error, isLoading, mutate } = useSWR<Stats>('/api/stats', () =>
    api.getStats()
  );

  return {
    stats: data ?? { discovered: 0, ready: 0, applied: 0, total: 0 },
    isLoading,
    isError: !!error,
    mutate,
  };
}
