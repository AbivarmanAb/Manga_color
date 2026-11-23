import React, { useEffect, useState } from 'react';
import { 
  Sparkles, 
  FolderPlus, 
  Cpu, 
  Layers, 
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api } from '../services/api';
import type { Project } from '../services/api';

export const Dashboard: React.FC = () => {
  const { hardware, refreshHardware, setTab, setActiveProject } = useStudioStore();
  const [projects, setProjects] = useState<Project[]>([]);

  const loadData = async () => {
    try {
      const projs = await api.getProjects();
      setProjects(projs);
      await refreshHardware();
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(refreshHardware, 3000);
    return () => clearInterval(interval);
  }, []);

  const totalPages = projects.reduce((acc, p) => acc + (p.page_count || 0), 0);
  const completedPages = projects.reduce((acc, p) => acc + (p.completed_page_count || 0), 0);
  const totalCharacters = projects.reduce((acc, p) => acc + (p.character_count || 0), 0);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 select-none">
      {/* Top Welcome & Quick Action Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-purple-950/60 via-studio-900 to-studio-900 border border-purple-800/40 p-8 shadow-studio-card">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5" />
              <span>NVIDIA RTX 5060 Accelerated &bull; Zero Cloud Fees</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Manga AI Colorization Studio
            </h1>
            <p className="text-zinc-400 text-sm max-w-2xl">
              Transform black-and-white manga pages into publication-quality full-color chapters 
              with intelligent character identity memory and strict line art preservation.
            </p>
          </div>

          <button
            onClick={() => setTab('new-project')}
            className="flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 text-white font-semibold text-sm shadow-glow-purple transition-all duration-200"
          >
            <FolderPlus className="w-5 h-5" />
            <span>New Manga Project</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-xl border border-studio-800 space-y-2">
          <div className="text-xs font-medium text-zinc-400">Total Projects</div>
          <div className="text-2xl font-bold text-white">{projects.length}</div>
          <div className="text-xs text-zinc-500">Manga chapters in library</div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-studio-800 space-y-2">
          <div className="text-xs font-medium text-zinc-400">Pages Processed</div>
          <div className="text-2xl font-bold text-cyan-400">{completedPages} <span className="text-xs text-zinc-500 font-normal">/ {totalPages}</span></div>
          <div className="text-xs text-zinc-500">Full color pages rendered</div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-studio-800 space-y-2">
          <div className="text-xs font-medium text-zinc-400">Character Memory Profiles</div>
          <div className="text-2xl font-bold text-purple-400">{totalCharacters}</div>
          <div className="text-xs text-zinc-500">Consistent palettes locked</div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-studio-800 space-y-2">
          <div className="text-xs font-medium text-zinc-400">GPU VRAM Status</div>
          <div className="text-2xl font-bold text-emerald-400">
            {hardware?.gpu.available 
              ? `${Math.round(hardware.gpu.used_vram_mb)} MB` 
              : 'CPU Only'}
          </div>
          <div className="text-xs text-zinc-500 font-mono">
            {hardware?.gpu.available ? `${hardware.gpu.device_name}` : 'Local Inference'}
          </div>
        </div>
      </div>

      {/* Two Column Grid: Hardware Inspector & Recent Projects */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Hardware Status Card */}
        <div className="glass-panel p-6 rounded-2xl border border-studio-800 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              Hardware Telemetry
            </h3>
            <button onClick={refreshHardware} className="text-zinc-500 hover:text-zinc-300">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {hardware && (
            <div className="space-y-4">
              {/* GPU VRAM Meter */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-400">VRAM ({hardware.gpu.device_name})</span>
                  <span className="font-mono text-zinc-200">
                    {Math.round(hardware.gpu.used_vram_mb)} / {Math.round(hardware.gpu.total_vram_mb)} MB ({hardware.gpu.utilization_percent}%)
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-studio-800 overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-cyan-400 transition-all duration-300"
                    style={{ width: `${Math.min(100, (hardware.gpu.used_vram_mb / (hardware.gpu.total_vram_mb || 1)) * 100)}%` }}
                  />
                </div>
              </div>

              {/* System RAM */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-400">System RAM (16 GB DDR5)</span>
                  <span className="font-mono text-zinc-200">{hardware.ram.used_gb} / {hardware.ram.total_gb} GB ({hardware.ram.percent}%)</span>
                </div>
                <div className="w-full h-2 rounded-full bg-studio-800 overflow-hidden">
                  <div 
                    className="h-full bg-indigo-500 transition-all duration-300"
                    style={{ width: `${hardware.ram.percent}%` }}
                  />
                </div>
              </div>

              {/* CPU Usage */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-400">CPU Usage ({hardware.cpu.cores} Cores)</span>
                  <span className="font-mono text-zinc-200">{hardware.cpu.percent}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-studio-800 overflow-hidden">
                  <div 
                    className="h-full bg-cyan-500 transition-all duration-300"
                    style={{ width: `${hardware.cpu.percent}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          <div className="p-3 rounded-lg bg-studio-800/60 border border-studio-700/50 text-[11px] text-zinc-400 space-y-1">
            <div className="font-semibold text-zinc-300">Memory Protection Active</div>
            <p>Pages are processed sequentially to guarantee RTX 5060 8GB VRAM limits are strictly respected.</p>
          </div>
        </div>

        {/* Recent Projects Table */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-studio-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Recent Manga Projects
            </h3>
            <button 
              onClick={() => setTab('projects')} 
              className="text-xs text-purple-400 hover:text-purple-300 font-medium flex items-center gap-1"
            >
              View All ({projects.length})
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {projects.length === 0 ? (
            <div className="py-12 text-center text-zinc-500 space-y-3">
              <FolderPlus className="w-10 h-10 mx-auto text-zinc-600" />
              <p className="text-sm">No manga projects created yet.</p>
              <button
                onClick={() => setTab('new-project')}
                className="px-4 py-2 rounded-lg bg-purple-600/30 hover:bg-purple-600/50 text-purple-300 text-xs font-medium border border-purple-500/40"
              >
                Create Your First Project
              </button>
            </div>
          ) : (
            <div className="divide-y divide-studio-800">
              {projects.slice(0, 5).map((p) => (
                <div key={p.id} className="py-3.5 flex items-center justify-between gap-4">
                  <div className="space-y-0.5">
                    <div className="text-sm font-semibold text-white">{p.manga_title}</div>
                    <div className="text-xs text-zinc-400">
                      Chapter {p.chapter_num} &bull; {p.page_count} Pages &bull; Style: <span className="capitalize text-zinc-300">{p.coloring_style.replace('_', ' ')}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase border ${
                      p.status === 'completed'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-zinc-800 text-zinc-400 border-zinc-700'
                    }`}>
                      {p.status}
                    </span>

                    <button
                      onClick={async () => {
                        await setActiveProject(p.id);
                        setTab('studio');
                      }}
                      className="px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 text-xs font-medium border border-purple-500/30 transition-colors"
                    >
                      Open Studio
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
