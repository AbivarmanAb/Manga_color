import React, { useEffect, useState } from 'react';
import { FolderKanban, Plus, Trash2, Palette } from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api } from '../services/api';
import type { Project } from '../services/api';

export const ProjectsList: React.FC = () => {
  const { setTab, setActiveProject } = useStudioStore();
  const [projects, setProjects] = useState<Project[]>([]);

  const fetchProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this manga project?')) {
      await api.deleteProject(id);
      await fetchProjects();
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 select-none">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <FolderKanban className="w-6 h-6 text-purple-400" />
            Manga Projects Library
          </h1>
          <p className="text-xs text-zinc-400">All registered manga series, chapters, and colorization workspaces.</p>
        </div>

        <button
          onClick={() => setTab('new-project')}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-glow-purple transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Project</span>
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl border border-studio-800 text-center space-y-3">
          <FolderKanban className="w-12 h-12 text-zinc-600 mx-auto" />
          <div className="text-sm font-semibold text-zinc-300">No Projects Found</div>
          <p className="text-xs text-zinc-500">Create a new project to start colorizing manga.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((p) => (
            <div
              key={p.id}
              onClick={async () => {
                await setActiveProject(p.id);
                setTab('studio');
              }}
              className="glass-panel p-6 rounded-2xl border border-studio-800 hover:border-purple-500/60 cursor-pointer transition-all duration-200 group flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-bold text-white group-hover:text-purple-300 transition-colors">
                      {p.manga_title}
                    </h3>
                    <div className="text-xs text-purple-400 font-medium">Chapter {p.chapter_num}</div>
                  </div>

                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase border ${
                    p.status === 'completed'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-zinc-800 text-zinc-400 border-zinc-700'
                  }`}>
                    {p.status}
                  </span>
                </div>

                <p className="text-xs text-zinc-400 line-clamp-2">
                  {p.description || `Manga colorization project in ${p.coloring_style.replace('_', ' ')} style.`}
                </p>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-studio-800/80 text-center text-xs">
                  <div className="p-2 rounded-lg bg-studio-800/50">
                    <div className="font-bold text-white">{p.page_count}</div>
                    <div className="text-[10px] text-zinc-500">Pages</div>
                  </div>
                  <div className="p-2 rounded-lg bg-studio-800/50">
                    <div className="font-bold text-cyan-400">{p.completed_page_count}</div>
                    <div className="text-[10px] text-zinc-500">Colored</div>
                  </div>
                  <div className="p-2 rounded-lg bg-studio-800/50">
                    <div className="font-bold text-purple-400">{p.character_count}</div>
                    <div className="text-[10px] text-zinc-500">Characters</div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-studio-800/80 mt-4">
                <span className="text-[11px] text-zinc-500 capitalize">{p.mode.replace('_', ' ')}</span>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => handleDelete(e, p.id)}
                    className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-studio-800 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600/20 text-purple-300 group-hover:bg-purple-600 group-hover:text-white text-xs font-semibold transition-all">
                    <Palette className="w-3.5 h-3.5" />
                    <span>Studio</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
