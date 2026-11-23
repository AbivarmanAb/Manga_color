import React, { useState, useEffect } from 'react';
import { Download, FileText, Archive, RefreshCw } from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api, BASE_ORIGIN } from '../services/api';

export const ExportCenter: React.FC = () => {
  const { activeProject } = useStudioStore();
  const [scale, setScale] = useState('original');
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportingZip, setExportingZip] = useState(false);
  const [downloads, setDownloads] = useState<{ name: string; url: string; size: number }[]>([]);

  const fetchRecords = async () => {
    if (!activeProject) return;
    try {
      const records = await api.getExportRecords(activeProject.id);
      const formatted = records.map((r: any) => ({
        name: r.filename,
        url: `${BASE_ORIGIN}${r.download_url}`,
        size: r.file_size_bytes,
      }));
      setDownloads(formatted);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [activeProject]);

  const handleExportPdf = async () => {
    if (!activeProject) return;
    setExportingPdf(true);
    try {
      const res = await api.exportPdf(activeProject.id, scale);
      const downloadItem = {
        name: res.filename,
        url: `${BASE_ORIGIN}${res.download_url}`,
        size: res.file_size_bytes,
      };
      setDownloads((prev) => [downloadItem, ...prev.filter((d) => d.name !== downloadItem.name)]);
      // Trigger automatic browser download
      window.open(downloadItem.url, '_blank');
    } catch (err) {
      console.error(err);
    } finally {
      setExportingPdf(false);
    }
  };

  const handleExportZip = async () => {
    if (!activeProject) return;
    setExportingZip(true);
    try {
      const res = await api.exportZip(activeProject.id, scale);
      const downloadItem = {
        name: res.filename,
        url: `${BASE_ORIGIN}${res.download_url}`,
        size: res.file_size_bytes,
      };
      setDownloads((prev) => [downloadItem, ...prev.filter((d) => d.name !== downloadItem.name)]);
      window.open(downloadItem.url, '_blank');
    } catch (err) {
      console.error(err);
    } finally {
      setExportingZip(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="p-12 text-center text-zinc-500">
        <Download className="w-12 h-12 mx-auto text-zinc-600 mb-2" />
        <p className="text-sm">Please select an active manga project first.</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 select-none">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <Download className="w-6 h-6 text-purple-400" />
            Export & Download Center
          </h1>
          <p className="text-xs text-zinc-400">
            Generate high-resolution publication-quality PDFs and ZIP archives for{' '}
            <span className="text-white font-semibold">{activeProject.manga_title}</span> Ch. {activeProject.chapter_num}.
          </p>
        </div>

        <button
          onClick={fetchRecords}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-studio-800 hover:bg-studio-700 text-zinc-300 text-xs font-medium border border-studio-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Files</span>
        </button>
      </div>

      {/* Resolution Selector Card */}
      <div className="glass-panel p-6 rounded-2xl border border-studio-800 space-y-4">
        <div className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Export Resolution</div>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setScale('original')}
            className={`p-4 rounded-xl text-left border transition-all ${
              scale === 'original'
                ? 'bg-purple-600/20 border-purple-500 ring-1 ring-purple-500 text-white'
                : 'bg-studio-800 border-studio-700 text-zinc-300 hover:bg-studio-700/60'
            }`}
          >
            <div className="font-bold text-sm">Original Manga Resolution</div>
            <p className="text-xs text-zinc-400 mt-1">Preserves 100% of raw page dimensions without resampling.</p>
          </button>

          <button
            onClick={() => setScale('2x')}
            className={`p-4 rounded-xl text-left border transition-all ${
              scale === '2x'
                ? 'bg-purple-600/20 border-purple-500 ring-1 ring-purple-500 text-white'
                : 'bg-studio-800 border-studio-700 text-zinc-300 hover:bg-studio-700/60'
            }`}
          >
            <div className="font-bold text-sm text-cyan-300">2x High-Definition Scale</div>
            <p className="text-xs text-zinc-400 mt-1">Lanczos high-resolution upscaling for premium digital reading.</p>
          </button>
        </div>
      </div>

      {/* Format Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* PDF Export Card */}
        <div className="glass-panel p-6 rounded-2xl border border-studio-800 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-white">Full Chapter PDF</h3>
            <p className="text-xs text-zinc-400">
              Lossless publication-ready PDF book. Pages are strictly ordered, aspect ratios are 100% preserved with zero margins.
            </p>
          </div>

          <button
            onClick={handleExportPdf}
            disabled={exportingPdf}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-md disabled:opacity-50 transition-all flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4" />
            <span>{exportingPdf ? 'Compiling PDF...' : 'Generate & Download PDF'}</span>
          </button>
        </div>

        {/* ZIP Export Card */}
        <div className="glass-panel p-6 rounded-2xl border border-studio-800 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Archive className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-white">Numbered Image Archive (ZIP)</h3>
            <p className="text-xs text-zinc-400">
              Contains all colored pages cleanly named in natural order (page_0001.png, page_0002.png) ready for e-readers.
            </p>
          </div>

          <button
            onClick={handleExportZip}
            disabled={exportingZip}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-bold shadow-md disabled:opacity-50 transition-all flex items-center justify-center gap-2"
          >
            <Archive className="w-4 h-4" />
            <span>{exportingZip ? 'Packaging ZIP...' : 'Bundle & Download ZIP'}</span>
          </button>
        </div>
      </div>

      {/* Generated Downloads Table */}
      {downloads.length > 0 && (
        <div className="glass-panel p-6 rounded-2xl border border-studio-800 space-y-4">
          <div className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Ready for Download ({downloads.length})</div>
          <div className="divide-y divide-studio-800">
            {downloads.map((d, i) => (
              <div key={i} className="py-3 flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="text-sm font-semibold text-white">{d.name}</div>
                  <div className="text-xs font-mono text-zinc-400">{(d.size / (1024 * 1024)).toFixed(2)} MB</div>
                </div>

                <div className="flex items-center gap-2">
                  <a
                    href={d.url}
                    download={d.name}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-all"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download File</span>
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
