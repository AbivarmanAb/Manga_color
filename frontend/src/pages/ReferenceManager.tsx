import React, { useState } from 'react';
import { Image as ImageIcon, Upload, Sparkles, Check } from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api, BASE_ORIGIN } from '../services/api';

export const ReferenceManager: React.FC = () => {
  const { activeProject, pages, refreshCharacters } = useStudioStore();
  const [charName, setCharName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const previewPages = pages.filter((p) => p.is_colored_preview);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject || !file || !charName) return;

    setUploading(true);
    try {
      await api.uploadReferenceImage(activeProject.id, charName, file);
      setSuccess(`Character profile created for ${charName} with extracted colors!`);
      setCharName('');
      setFile(null);
      await refreshCharacters();
      setTimeout(() => setSuccess(null), 4000);
    } catch (err: any) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="p-12 text-center text-zinc-500">
        <ImageIcon className="w-12 h-12 mx-auto text-zinc-600 mb-2" />
        <p className="text-sm">Please select an active manga project first.</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 select-none">
      <div>
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
          <ImageIcon className="w-6 h-6 text-cyan-400" />
          Reference Manager (Mode B & Mode C)
        </h1>
        <p className="text-xs text-zinc-400">
          Official artbooks, colored cover pages, and character reference swatches.
        </p>
      </div>

      {success && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Official Character Reference Card (Mode C) */}
        <div className="glass-panel p-6 rounded-2xl border border-studio-800 space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Upload className="w-4 h-4 text-purple-400" />
            Upload Official Reference (Mode C)
          </h2>
          <p className="text-xs text-zinc-400">
            Upload an official color illustration or anime screenshot. The AI will extract dominant colors and link them to character identity memory.
          </p>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-medium text-zinc-300">Character Name</label>
              <input
                type="text"
                required
                value={charName}
                onChange={(e) => setCharName(e.target.value)}
                placeholder="e.g. Roronoa Zoro"
                className="w-full px-3 py-2 rounded-lg bg-studio-800 border border-studio-700 text-white text-xs focus:outline-none focus:border-purple-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-zinc-300">Reference Image</label>
              <input
                type="file"
                required
                accept="image/*"
                onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                className="w-full text-xs text-zinc-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-purple-600/30 file:text-purple-300 hover:file:bg-purple-600/50"
              />
            </div>

            <button
              type="submit"
              disabled={uploading || !file || !charName}
              className="w-full py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-md disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{uploading ? 'Extracting Swatches...' : 'Ingest & Extract Palette'}</span>
            </button>
          </form>
        </div>

        {/* Mode B: Automatically Detected Preview Pages */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-studio-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-emerald-400" />
              Detected Colored Preview Pages ({previewPages.length})
            </h2>
          </div>

          <p className="text-xs text-zinc-400">
            Pages with high color saturation (covers, colored inserts) are automatically identified and used to guide subsequent black-and-white chapter pages.
          </p>

          {previewPages.length === 0 ? (
            <div className="p-8 text-center text-zinc-500 rounded-xl bg-studio-900/50 border border-studio-800">
              <p className="text-xs">No colored preview pages detected in this chapter.</p>
              <p className="text-[11px] text-zinc-600 mt-1">Operating in Mode A (Pure B&W manga colorization).</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {previewPages.map((page) => (
                <div key={page.id} className="p-2 rounded-xl bg-studio-800/60 border border-studio-700/60 space-y-2">
                  <div className="aspect-[3/4] rounded-lg overflow-hidden bg-studio-900">
                    <img
                      src={`${BASE_ORIGIN}${page.original_url}`}
                      alt={page.filename}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="text-[11px] font-semibold text-white truncate px-1">
                    Page {page.page_number}: {page.filename}
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
