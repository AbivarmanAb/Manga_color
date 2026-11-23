import React from 'react';
import { 
  LayoutDashboard, 
  PlusCircle, 
  FolderKanban, 
  Palette, 
  Users, 
  Image as ImageIcon, 
  ListOrdered, 
  Download, 
  Settings as SettingsIcon,
  Cpu,
  Sparkles
} from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import type { NavigationTab } from '../stores/useStudioStore';

export const Sidebar: React.FC = () => {
  const { currentTab, setTab, activeProject, hardware } = useStudioStore();

  const navItems: { id: NavigationTab; label: string; icon: React.ReactNode }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
    { id: 'new-project', label: 'New Project', icon: <PlusCircle className="w-5 h-5" /> },
    { id: 'projects', label: 'Manga Library', icon: <FolderKanban className="w-5 h-5" /> },
    { id: 'studio', label: 'Colorization Studio', icon: <Palette className="w-5 h-5" /> },
    { id: 'characters', label: 'Character Memory', icon: <Users className="w-5 h-5" /> },
    { id: 'references', label: 'Reference Manager', icon: <ImageIcon className="w-5 h-5" /> },
    { id: 'queue', label: 'Processing Queue', icon: <ListOrdered className="w-5 h-5" /> },
    { id: 'exports', label: 'Export Center', icon: <Download className="w-5 h-5" /> },
    { id: 'settings', label: 'Hardware & Models', icon: <SettingsIcon className="w-5 h-5" /> },
  ];

  return (
    <aside className="w-64 bg-studio-900 border-r border-studio-800 flex flex-col justify-between select-none">
      <div>
        {/* Logo / Brand */}
        <div className="p-5 border-b border-studio-800/80 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-cyan-400 p-[2px] shadow-glow-purple">
            <div className="w-full h-full bg-studio-950 rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-purple-400 animate-pulse" />
            </div>
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wide text-white uppercase flex items-center gap-1.5">
              Manga AI
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono">STUDIO</span>
            </h1>
            <p className="text-[11px] text-zinc-400">Intelligent Colorization</p>
          </div>
        </div>

        {/* Current Active Project Chip */}
        {activeProject && (
          <div className="mx-3 mt-3 p-2.5 rounded-lg bg-studio-850 border border-studio-700/60">
            <div className="text-[10px] font-medium text-zinc-400 uppercase tracking-wider">Active Manga</div>
            <div className="text-xs font-semibold text-white truncate mt-0.5">{activeProject.manga_title}</div>
            <div className="text-[11px] text-purple-400">Chapter {activeProject.chapter_num} &bull; {activeProject.page_count} Pages</div>
          </div>
        )}

        {/* Navigation Links */}
        <nav className="p-3 space-y-1 mt-2">
          {navItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-purple-600/20 text-purple-300 border border-purple-500/40 shadow-sm'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-studio-800/60'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Hardware Telemetry Badge */}
      <div className="p-3 border-t border-studio-800/80 bg-studio-950/60">
        <div className="p-2.5 rounded-lg bg-studio-900 border border-studio-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <div className="text-left">
              <div className="text-[11px] font-semibold text-zinc-200 truncate max-w-[120px]">
                {hardware?.gpu.available ? 'RTX 5060' : 'CPU Mode'}
              </div>
              <div className="text-[10px] text-zinc-400 font-mono">
                {hardware?.gpu.available
                  ? `${Math.round(hardware.gpu.used_vram_mb)} / ${Math.round(hardware.gpu.total_vram_mb)} MB`
                  : 'CPU Engine'}
              </div>
            </div>
          </div>
          <span className={`w-2.5 h-2.5 rounded-full ${hardware?.gpu.available ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-amber-400'}`} />
        </div>
      </div>
    </aside>
  );
};
