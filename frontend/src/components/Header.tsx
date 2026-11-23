import React, { useEffect, useState } from 'react';
import { Play, RefreshCw, ChevronDown } from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api } from '../services/api';
import type { Project } from '../services/api';

export const Header: React.FC = () => {
  const { activeProject, hardware, refreshHardware, refreshQueue, setTab, setActiveProject } = useStudioStore();
  const [allProjects, setAllProjects] = useState<Project[]>([]);

  useEffect(() => {
    api.getProjects().then(setAllProjects).catch(console.error);
  }, [activeProject]);

  const handleStartBatch = async () => {
    if (!activeProject) return;
    await api.startQueue(activeProject.id);
    await refreshQueue();
    setTab('queue');
  };

  const handleClearVram = async () => {
    await api.clearVram();
    await refreshHardware();
  };

  return (
    <header className="h-14 bg-studio-900 border-b border-studio-800 flex items-center justify-between px-6 z-10 select-none">
      {/* Title & Project Selector */}
      <div className="flex items-center gap-3">
        {allProjects.length > 0 ? (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-zinc-400">Project:</span>
            <div className="relative">
              <select
                value={activeProject?.id || ''}
                onChange={(e) => {
                  if (e.target.value) setActiveProject(e.target.value);
                }}
                className="bg-studio-850 hover:bg-studio-800 text-white font-semibold py-1 pl-2.5 pr-7 rounded-lg border border-studio-700 text-xs appearance-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-purple-500"
              >
                {allProjects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.manga_title} &bull; Ch. {p.chapter_num} ({p.page_count}p)
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-zinc-400 absolute right-2 top-2 pointer-events-none" />
            </div>

            {activeProject && (
              <span className={`text-[11px] px-2 py-0.5 rounded-full font-mono uppercase border ${
                activeProject.status === 'completed'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : activeProject.status === 'processing'
                  ? 'bg-purple-500/10 text-purple-400 border-purple-500/30 animate-pulse'
                  : 'bg-zinc-800 text-zinc-400 border-zinc-700'
              }`}>
                {activeProject.status}
              </span>
            )}
          </div>
        ) : (
          <span className="text-sm text-zinc-400">No project selected</span>
        )}
      </div>

      {/* Action Controls & Hardware Summary */}
      <div className="flex items-center gap-3">
        {/* VRAM Fast Flush */}
        {hardware?.gpu.available && (
          <button
            onClick={handleClearVram}
            title="Flush GPU VRAM Cache"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-studio-800 hover:bg-studio-700 text-zinc-300 text-xs font-mono transition-colors border border-studio-700"
          >
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
            <span>{Math.round(hardware.gpu.used_vram_mb)} MB</span>
          </button>
        )}

        {/* Start / Jump to Queue Button */}
        {activeProject && (
          <button
            onClick={handleStartBatch}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-medium shadow-md transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            <span>Process Chapter</span>
          </button>
        )}
      </div>
    </header>
  );
};
