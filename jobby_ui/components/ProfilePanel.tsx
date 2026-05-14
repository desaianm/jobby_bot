'use client';

import { useState } from 'react';
import { User, Mail, MapPin, Briefcase, Plus, Trash2, Play, Settings } from 'lucide-react';
import { Preset } from '@/lib/types';

const DEFAULT_PRESETS: Preset[] = [
  { id: '1', name: 'AI Engineer — Toronto', search_term: 'AI Engineer', location: 'Toronto, ON', is_remote: false, results_wanted: 25, country_indeed: 'Canada' },
  { id: '2', name: 'Remote ML Roles', search_term: 'Machine Learning Engineer', location: '', is_remote: true, results_wanted: 30, country_indeed: 'USA' },
];

interface ProfilePanelProps {
  onRunPreset: (preset: Preset) => void;
}

export default function ProfilePanel({ onRunPreset }: ProfilePanelProps) {
  const [presets, setPresets] = useState<Preset[]>(DEFAULT_PRESETS);
  const [editingPreset, setEditingPreset] = useState<Partial<Preset> | null>(null);

  const handleAddPreset = () => {
    if (!editingPreset?.name || !editingPreset?.search_term) return;
    const newPreset: Preset = {
      id: Date.now().toString(),
      name: editingPreset.name,
      search_term: editingPreset.search_term,
      location: editingPreset.location || '',
      is_remote: editingPreset.is_remote || false,
      results_wanted: editingPreset.results_wanted || 25,
      country_indeed: editingPreset.country_indeed || 'Canada',
    };
    setPresets((prev) => [...prev, newPreset]);
    setEditingPreset(null);
  };

  const handleDeletePreset = (id: string) => {
    setPresets((prev) => prev.filter((p) => p.id !== id));
  };

  return (
    <div className="flex-1 overflow-y-auto" style={{ padding: 28 }}>
      <div className="max-w-2xl mx-auto">
        {/* Profile header */}
        <div className="animate-fadeIn">
          <div className="eyebrow mb-2" style={{ color: 'var(--purple)' }}>Profile</div>
          <h1 className="font-display text-[28px]" style={{ letterSpacing: '-0.03em', lineHeight: 1.1 }}>
            Your workspace
          </h1>
          <p className="mt-2 text-[14px]" style={{ color: 'var(--ink-2)' }}>
            Manage your profile, preferences, and search presets.
          </p>
        </div>

        {/* User card */}
        <div className="card-warm rounded-xl p-5 mt-6 animate-fadeInUp">
          <div className="flex items-center gap-4">
            <div
              className="flex items-center justify-center rounded-xl"
              style={{
                width: 56, height: 56,
                background: 'linear-gradient(135deg, var(--purple-soft) 0%, var(--blue-soft) 100%)',
                border: '1px solid var(--purple)',
              }}
            >
              <User size={24} style={{ color: 'var(--purple-ink)' }} />
            </div>
            <div>
              <h3 className="text-[16px] font-semibold">Anmol Desai</h3>
              <div className="flex items-center gap-3 mt-1 text-[12px]" style={{ color: 'var(--ink-3)' }}>
                <span className="flex items-center gap-1"><Mail size={11} /> adcan288@gmail.com</span>
                <span className="flex items-center gap-1"><MapPin size={11} /> Toronto, ON</span>
              </div>
            </div>
          </div>
        </div>

        {/* Preferences */}
        <div className="card-warm rounded-xl p-5 mt-4 animate-fadeInUp" style={{ animationDelay: '60ms' }}>
          <div className="flex items-center gap-2 mb-4">
            <Settings size={14} style={{ color: 'var(--ink-3)' }} />
            <span className="text-[13px] font-bold">Preferences</span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="eyebrow block mb-1.5">Default Location</label>
              <input type="text" defaultValue="Toronto, ON" className="input-warm w-full" />
            </div>
            <div>
              <label className="eyebrow block mb-1.5">Default Country</label>
              <select className="input-warm w-full">
                <option>Canada</option>
                <option>USA</option>
                <option>United Kingdom</option>
              </select>
            </div>
            <div>
              <label className="eyebrow block mb-1.5">Target Role</label>
              <input type="text" defaultValue="AI/ML Engineer" className="input-warm w-full" />
            </div>
            <div>
              <label className="eyebrow block mb-1.5">Experience Level</label>
              <select className="input-warm w-full">
                <option>Senior</option>
                <option>Mid</option>
                <option>Junior</option>
                <option>Staff+</option>
              </select>
            </div>
          </div>
        </div>

        {/* Search Presets */}
        <div className="card-warm rounded-xl p-5 mt-4 animate-fadeInUp" style={{ animationDelay: '120ms' }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Briefcase size={14} style={{ color: 'var(--accent)' }} />
              <span className="text-[13px] font-bold">Search Presets</span>
            </div>
            <button
              onClick={() => setEditingPreset({ name: '', search_term: '', location: 'Toronto, ON', country_indeed: 'Canada', results_wanted: 25, is_remote: false })}
              className="btn-warm text-[12px] py-1.5 px-2.5"
            >
              <Plus size={12} /> New Preset
            </button>
          </div>

          {/* Preset list */}
          <div className="flex flex-col gap-2 stagger-children">
            {presets.map((preset) => (
              <div
                key={preset.id}
                className="flex items-center gap-3 p-3 rounded-lg animate-fadeInUp"
                style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
              >
                <div className="flex-1 min-w-0">
                  <div className="text-[13px] font-semibold">{preset.name}</div>
                  <div className="text-[11px] mt-0.5" style={{ color: 'var(--ink-3)' }}>
                    {preset.search_term} · {preset.location || 'Any location'} · {preset.results_wanted} results
                    {preset.is_remote && ' · Remote'}
                  </div>
                </div>
                <button
                  onClick={() => onRunPreset(preset)}
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-md text-[11px] font-semibold transition-all"
                  style={{ background: 'var(--accent)', color: 'white' }}
                >
                  <Play size={10} fill="currentColor" /> Run
                </button>
                <button
                  onClick={() => handleDeletePreset(preset.id)}
                  className="p-1.5 rounded-md transition-colors"
                  style={{ color: 'var(--ink-4)' }}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>

          {/* Add preset form */}
          {editingPreset && (
            <div className="mt-3 p-3 rounded-lg" style={{ background: 'var(--card)', border: '1px solid var(--accent)', borderStyle: 'dashed' }}>
              <div className="grid grid-cols-2 gap-3">
                <input
                  placeholder="Preset name"
                  value={editingPreset.name || ''}
                  onChange={(e) => setEditingPreset({ ...editingPreset, name: e.target.value })}
                  className="input-warm text-[12px]"
                />
                <input
                  placeholder="Search term"
                  value={editingPreset.search_term || ''}
                  onChange={(e) => setEditingPreset({ ...editingPreset, search_term: e.target.value })}
                  className="input-warm text-[12px]"
                />
                <input
                  placeholder="Location"
                  value={editingPreset.location || ''}
                  onChange={(e) => setEditingPreset({ ...editingPreset, location: e.target.value })}
                  className="input-warm text-[12px]"
                />
                <select
                  value={editingPreset.country_indeed || 'Canada'}
                  onChange={(e) => setEditingPreset({ ...editingPreset, country_indeed: e.target.value })}
                  className="input-warm text-[12px]"
                >
                  <option>Canada</option>
                  <option>USA</option>
                  <option>United Kingdom</option>
                </select>
              </div>
              <div className="flex items-center gap-2 mt-3">
                <button onClick={handleAddPreset} className="btn-accent text-[12px] py-1.5">Save Preset</button>
                <button onClick={() => setEditingPreset(null)} className="btn-warm text-[12px] py-1.5">Cancel</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
