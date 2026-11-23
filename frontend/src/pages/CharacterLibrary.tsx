import React, { useEffect, useState } from 'react';
import { Users, Lock, Unlock, Sparkles, RefreshCw, Check } from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api } from '../services/api';

export const CharacterLibrary: React.FC = () => {
  const { activeProject, characters, refreshCharacters } = useStudioStore();
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    refreshCharacters();
  }, [activeProject]);

  const handleColorChange = async (charId: string, field: string, value: string) => {
    await api.updateCharacter(charId, { [field]: value });
    await refreshCharacters();
  };

  const handleToggleLock = async (charId: string, currentLock: boolean) => {
    await api.updateCharacter(charId, { is_locked: !currentLock });
    await refreshCharacters();
  };

  const handlePropagate = async (charId: string) => {
    const res = await api.propagateCharacter(charId);
    setSuccessMessage(res.message);
    setTimeout(() => setSuccessMessage(null), 4000);
  };

  if (!activeProject) {
    return (
      <div className="p-12 text-center text-zinc-500">
        <Users className="w-12 h-12 mx-auto text-zinc-600 mb-2" />
        <p className="text-sm">Please select or open a manga project first.</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 select-none">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-purple-400" />
            Character Color Memory System (CCMS)
          </h1>
          <p className="text-xs text-zinc-400">
            Persistent character identity registry for <span className="text-white font-semibold">{activeProject.manga_title}</span>. 
            Palette swatches are locked and automatically maintained across all pages.
          </p>
        </div>

        <button
          onClick={refreshCharacters}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-studio-800 hover:bg-studio-700 text-zinc-300 text-xs font-medium border border-studio-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>{successMessage}</span>
        </div>
      )}

      {characters.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl border border-studio-800 text-center space-y-3">
          <Users className="w-12 h-12 text-zinc-600 mx-auto" />
          <div className="text-sm font-semibold text-zinc-300">No Characters Identified Yet</div>
          <p className="text-xs text-zinc-500">
            Run Chapter Analysis or Batch Processing to automatically recognize recurring characters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {characters.map((char) => (
            <div
              key={char.id}
              className="glass-panel p-6 rounded-2xl border border-studio-800 space-y-5 flex flex-col justify-between"
            >
              <div className="space-y-4">
                {/* Character Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-white text-base">{char.name}</h3>
                    <div className="text-[11px] text-zinc-400">
                      Appearances: Pages {char.first_appearance_page} &ndash; {char.last_appearance_page}
                    </div>
                  </div>

                  <button
                    onClick={() => handleToggleLock(char.id, char.is_locked)}
                    title={char.is_locked ? 'Colors are locked' : 'Click to lock colors'}
                    className={`p-2 rounded-lg border transition-all ${
                      char.is_locked
                        ? 'bg-purple-600/20 text-purple-300 border-purple-500/40'
                        : 'bg-studio-800 text-zinc-400 border-studio-700 hover:text-zinc-200'
                    }`}
                  >
                    {char.is_locked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                  </button>
                </div>

                {/* Color Swatches Grid */}
                <div className="space-y-3 pt-2 border-t border-studio-800/80">
                  <div className="text-xs font-semibold text-zinc-300">Locked Palette Swatches</div>

                  <div className="grid grid-cols-3 gap-2.5">
                    {/* Hair */}
                    <div className="space-y-1">
                      <div className="text-[10px] text-zinc-400">Hair</div>
                      <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-studio-800/80 border border-studio-700">
                        <input
                          type="color"
                          value={char.hair_color}
                          onChange={(e) => handleColorChange(char.id, 'hair_color', e.target.value)}
                          className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent"
                        />
                        <span className="text-[10px] font-mono text-zinc-300">{char.hair_color}</span>
                      </div>
                    </div>

                    {/* Skin */}
                    <div className="space-y-1">
                      <div className="text-[10px] text-zinc-400">Skin</div>
                      <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-studio-800/80 border border-studio-700">
                        <input
                          type="color"
                          value={char.skin_color}
                          onChange={(e) => handleColorChange(char.id, 'skin_color', e.target.value)}
                          className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent"
                        />
                        <span className="text-[10px] font-mono text-zinc-300">{char.skin_color}</span>
                      </div>
                    </div>

                    {/* Eyes */}
                    <div className="space-y-1">
                      <div className="text-[10px] text-zinc-400">Eyes</div>
                      <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-studio-800/80 border border-studio-700">
                        <input
                          type="color"
                          value={char.eye_color}
                          onChange={(e) => handleColorChange(char.id, 'eye_color', e.target.value)}
                          className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent"
                        />
                        <span className="text-[10px] font-mono text-zinc-300">{char.eye_color}</span>
                      </div>
                    </div>

                    {/* Primary Outfit */}
                    <div className="space-y-1">
                      <div className="text-[10px] text-zinc-400">Outfit (Primary)</div>
                      <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-studio-800/80 border border-studio-700">
                        <input
                          type="color"
                          value={char.primary_outfit_color}
                          onChange={(e) => handleColorChange(char.id, 'primary_outfit_color', e.target.value)}
                          className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent"
                        />
                        <span className="text-[10px] font-mono text-zinc-300">{char.primary_outfit_color}</span>
                      </div>
                    </div>

                    {/* Secondary Outfit */}
                    <div className="space-y-1">
                      <div className="text-[10px] text-zinc-400">Outfit (Detail)</div>
                      <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-studio-800/80 border border-studio-700">
                        <input
                          type="color"
                          value={char.secondary_outfit_color}
                          onChange={(e) => handleColorChange(char.id, 'secondary_outfit_color', e.target.value)}
                          className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent"
                        />
                        <span className="text-[10px] font-mono text-zinc-300">{char.secondary_outfit_color}</span>
                      </div>
                    </div>

                    {/* Accent */}
                    <div className="space-y-1">
                      <div className="text-[10px] text-zinc-400">Accent</div>
                      <div className="flex items-center gap-1.5 p-1.5 rounded-lg bg-studio-800/80 border border-studio-700">
                        <input
                          type="color"
                          value={char.accent_color || '#EF4444'}
                          onChange={(e) => handleColorChange(char.id, 'accent_color', e.target.value)}
                          className="w-5 h-5 rounded cursor-pointer border-0 bg-transparent"
                        />
                        <span className="text-[10px] font-mono text-zinc-300">{char.accent_color || '#EF4444'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action: Propagate to Chapter */}
              <div className="pt-4 border-t border-studio-800/80">
                <button
                  onClick={() => handlePropagate(char.id)}
                  className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 text-xs font-semibold border border-purple-500/30 transition-all"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Propagate to All Chapter Pages</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
