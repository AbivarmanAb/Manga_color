import React, { useState } from 'react';
import { 
  FolderPlus, 
  Upload, 
  FileText, 
  Archive, 
  Check, 
  ArrowRight, 
  ArrowLeft,
  Sparkles,
  Layers,
  Palette,
  Image as ImageIcon
} from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api } from '../services/api';

export const NewProjectWizard: React.FC = () => {
  const { setTab, setActiveProject } = useStudioStore();
  
  const [step, setStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Form Data
  const [title, setTitle] = useState('');
  const [mangaTitle, setMangaTitle] = useState('');
  const [chapterNum, setChapterNum] = useState('1');
  const [description, setDescription] = useState('');
  const [mode, setMode] = useState<'new_manga' | 'preview_reference' | 'character_reference' | 'combined'>('combined');
  const [coloringStyle, setColoringStyle] = useState('vibrant_anime');
  const [outputResolution, setOutputResolution] = useState('original');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...filesArray]);
    }
  };

  const handleCreateAndAnalyze = async () => {
    if (!title || !mangaTitle) {
      setError('Please provide a project name and manga title.');
      return;
    }
    if (selectedFiles.length === 0) {
      setError('Please upload at least one manga page, PDF, or ZIP archive.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Create project
      const project = await api.createProject({
        title,
        manga_title: mangaTitle,
        chapter_num: chapterNum,
        description,
        mode,
        coloring_style: coloringStyle,
        output_resolution: outputResolution,
      });

      // 2. Upload files
      await api.uploadFiles(project.id, selectedFiles);

      // 3. Trigger initial chapter analysis (detect characters & preview pages)
      await api.analyzeChapter(project.id);

      // 4. Set as active project and navigate to studio!
      await setActiveProject(project.id);
      setTab('studio');
    } catch (err: any) {
      console.error(err);
      setError(err?.message || 'Failed to create project.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto select-none">
      {/* Wizard Header */}
      <div className="text-center space-y-2 mb-8">
        <h1 className="text-2xl font-extrabold text-white">Create Manga Colorization Project</h1>
        <p className="text-zinc-400 text-xs">Configure your chapter, upload pages, and initialize character memory.</p>
        
        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 pt-4">
          {[1, 2, 3, 4, 5].map((s) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                step === s
                  ? 'bg-purple-600 text-white shadow-glow-purple'
                  : step > s
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                  : 'bg-studio-800 text-zinc-500'
              }`}>
                {step > s ? <Check className="w-4 h-4" /> : s}
              </div>
              {s < 5 && <div className={`w-8 h-[2px] ${step > s ? 'bg-emerald-500/50' : 'bg-studio-800'}`} />}
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Wizard Content Card */}
      <div className="glass-panel p-8 rounded-2xl border border-studio-800 shadow-studio-card min-h-[380px]">
        {/* STEP 1: Project Information */}
        {step === 1 && (
          <div className="space-y-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <FolderPlus className="w-5 h-5 text-purple-400" />
              Step 1: Project Details
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Project Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. One Piece Chapter 1000 Color"
                  className="w-full px-3.5 py-2.5 rounded-lg bg-studio-800 border border-studio-700 text-white text-sm focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Manga Title</label>
                <input
                  type="text"
                  value={mangaTitle}
                  onChange={(e) => setMangaTitle(e.target.value)}
                  placeholder="e.g. One Piece"
                  className="w-full px-3.5 py-2.5 rounded-lg bg-studio-800 border border-studio-700 text-white text-sm focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Chapter Number</label>
                <input
                  type="text"
                  value={chapterNum}
                  onChange={(e) => setChapterNum(e.target.value)}
                  placeholder="e.g. 1000"
                  className="w-full px-3.5 py-2.5 rounded-lg bg-studio-800 border border-studio-700 text-white text-sm focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Output Resolution</label>
                <select
                  value={outputResolution}
                  onChange={(e) => setOutputResolution(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg bg-studio-800 border border-studio-700 text-white text-sm focus:outline-none focus:border-purple-500"
                >
                  <option value="original">Original Resolution</option>
                  <option value="2x">2x Enhanced High-Res</option>
                </select>
              </div>

              <div className="md:col-span-2 space-y-1.5">
                <label className="text-xs font-medium text-zinc-300">Description (Optional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  placeholder="Notes about this chapter or translation..."
                  className="w-full px-3.5 py-2 rounded-lg bg-studio-800 border border-studio-700 text-white text-sm focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: File Upload */}
        {step === 2 && (
          <div className="space-y-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Upload className="w-5 h-5 text-cyan-400" />
              Step 2: Upload Manga Pages
            </h2>

            <div className="border-2 border-dashed border-studio-700 hover:border-purple-500 rounded-xl p-8 text-center space-y-3 bg-studio-900/50 transition-colors">
              <div className="flex justify-center gap-3 text-zinc-400">
                <ImageIcon className="w-8 h-8 text-purple-400" />
                <Archive className="w-8 h-8 text-cyan-400" />
                <FileText className="w-8 h-8 text-indigo-400" />
              </div>
              <div className="text-sm font-medium text-zinc-200">
                Drop your manga pages, ZIP archive, or PDF document here
              </div>
              <div className="text-xs text-zinc-400">
                Supports PNG, JPG, JPEG, WebP, ZIP, and PDF
              </div>
              <label className="inline-block mt-2 px-5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium cursor-pointer shadow-md transition-all">
                Browse Files
                <input
                  type="file"
                  multiple
                  accept=".png,.jpg,.jpeg,.webp,.zip,.pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
            </div>

            {selectedFiles.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs font-semibold text-zinc-300">
                  Selected Files ({selectedFiles.length}):
                </div>
                <div className="max-h-36 overflow-y-auto space-y-1 pr-2">
                  {selectedFiles.map((file, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs px-3 py-1.5 rounded bg-studio-800/80 text-zinc-300">
                      <span className="truncate max-w-sm">{file.name}</span>
                      <span className="text-zinc-500 font-mono">{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* STEP 3: Colorization Mode */}
        {step === 3 && (
          <div className="space-y-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              Step 3: Select Colorization Mode
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setMode('combined')}
                className={`p-4 rounded-xl text-left border transition-all ${
                  mode === 'combined'
                    ? 'bg-purple-600/20 border-purple-500 ring-1 ring-purple-500 text-white'
                    : 'bg-studio-800 border-studio-700 text-zinc-300 hover:bg-studio-700/60'
                }`}
              >
                <div className="font-bold text-sm text-purple-300">Combined Mode (Recommended)</div>
                <p className="text-xs text-zinc-400 mt-1">
                  Combines automated AI character detection, color previews if present, and allows manual official references.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setMode('new_manga')}
                className={`p-4 rounded-xl text-left border transition-all ${
                  mode === 'new_manga'
                    ? 'bg-purple-600/20 border-purple-500 ring-1 ring-purple-500 text-white'
                    : 'bg-studio-800 border-studio-700 text-zinc-300 hover:bg-studio-700/60'
                }`}
              >
                <div className="font-bold text-sm text-cyan-300">Mode A: Completely B&W Manga</div>
                <p className="text-xs text-zinc-400 mt-1">
                  No preview images. AI detects recurring characters and generates matching anime palettes.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setMode('preview_reference')}
                className={`p-4 rounded-xl text-left border transition-all ${
                  mode === 'preview_reference'
                    ? 'bg-purple-600/20 border-purple-500 ring-1 ring-purple-500 text-white'
                    : 'bg-studio-800 border-studio-700 text-zinc-300 hover:bg-studio-700/60'
                }`}
              >
                <div className="font-bold text-sm text-emerald-300">Mode B: Colored Preview Pages</div>
                <p className="text-xs text-zinc-400 mt-1">
                  Extracts official colors from cover or color spreads and applies them to subsequent B&W panels.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setMode('character_reference')}
                className={`p-4 rounded-xl text-left border transition-all ${
                  mode === 'character_reference'
                    ? 'bg-purple-600/20 border-purple-500 ring-1 ring-purple-500 text-white'
                    : 'bg-studio-800 border-studio-700 text-zinc-300 hover:bg-studio-700/60'
                }`}
              >
                <div className="font-bold text-sm text-pink-300">Mode C: Official Character References</div>
                <p className="text-xs text-zinc-400 mt-1">
                  Guided by uploaded anime character sheets or artbook illustrations.
                </p>
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: Coloring Style */}
        {step === 4 && (
          <div className="space-y-5">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Palette className="w-5 h-5 text-pink-400" />
              Step 4: Select Coloring Style
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { id: 'vibrant_anime', label: 'Vibrant Anime', desc: 'Punchy anime colors, saturated eyes & hair, high-energy contrast.' },
                { id: 'classic_manga', label: 'Classic Japanese Manga', desc: 'Authentic warm publication tone with subtle vintage watercolor shading.' },
                { id: 'cinematic_anime', label: 'Cinematic Anime', desc: 'Moody lighting, deep shadows, atmospheric cinematic tone.' },
                { id: 'soft_anime', label: 'Soft Pastel Anime', desc: 'Gentle pastel hues, luminous skin tones, dreamy aesthetic.' },
              ].map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setColoringStyle(s.id)}
                  className={`p-4 rounded-xl text-left border transition-all ${
                    coloringStyle === s.id
                      ? 'bg-purple-600/20 border-purple-500 ring-1 ring-purple-500 text-white'
                      : 'bg-studio-800 border-studio-700 text-zinc-300 hover:bg-studio-700/60'
                  }`}
                >
                  <div className="font-bold text-sm">{s.label}</div>
                  <p className="text-xs text-zinc-400 mt-1">{s.desc}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* STEP 5: Start Analysis */}
        {step === 5 && (
          <div className="space-y-6 text-center py-4">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-tr from-purple-600 to-cyan-400 p-0.5 shadow-glow-purple">
              <div className="w-full h-full bg-studio-950 rounded-[14px] flex items-center justify-center">
                <Sparkles className="w-8 h-8 text-purple-400 animate-spin" />
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-xl font-bold text-white">Ready to Initialize Chapter</h2>
              <p className="text-zinc-400 text-xs max-w-md mx-auto">
                The studio will extract all pages, identify preview pages vs B&W pages, 
                detect characters, and seed the Character Color Memory System.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-studio-800/80 border border-studio-700 text-left max-w-md mx-auto text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-zinc-400">Manga:</span>
                <span className="font-semibold text-white">{mangaTitle} Ch. {chapterNum}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Uploaded Files:</span>
                <span className="text-purple-300 font-mono">{selectedFiles.length} file(s)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Coloring Style:</span>
                <span className="text-cyan-300 capitalize">{coloringStyle.replace('_', ' ')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Hardware:</span>
                <span className="text-emerald-400">RTX 5060 Local Acceleration</span>
              </div>
            </div>
          </div>
        )}

        {/* Wizard Navigation Footer */}
        <div className="flex items-center justify-between pt-8 border-t border-studio-800/80 mt-6">
          {step > 1 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s - 1)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-studio-800 hover:bg-studio-700 text-zinc-300 text-xs font-medium transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </button>
          ) : <div />}

          {step < 5 ? (
            <button
              type="button"
              onClick={() => {
                if (step === 1 && (!title || !mangaTitle)) {
                  setError('Please fill in project name and manga title.');
                  return;
                }
                if (step === 2 && selectedFiles.length === 0) {
                  setError('Please upload manga pages or archives.');
                  return;
                }
                setError(null);
                setStep((s) => s + 1);
              }}
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              <span>Next Step</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              disabled={loading}
              onClick={handleCreateAndAnalyze}
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500 hover:from-purple-500 hover:to-cyan-400 text-white text-xs font-bold shadow-glow-purple disabled:opacity-50 transition-all"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Analyzing Chapter...' : 'Start AI Analysis'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
