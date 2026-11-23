import React, { useEffect, useState } from 'react';
import {
  Play,
  Pause,
  Square,
  RotateCcw,
  ListOrdered,
  Eye,
  Download,
  FileText,
  Archive,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api, BASE_ORIGIN } from '../services/api';

export const ProcessingQueuePage: React.FC = () => {
  const { activeProject, pages, queueStatus, refreshQueue, refreshPages, setTab, setActivePage } = useStudioStore();
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingZip, setDownloadingZip] = useState(false);

  useEffect(() => {
    const timer = setInterval(async () => {
      await refreshQueue();
      await refreshPages();
    }, 1500);
    return () => clearInterval(timer);
  }, [activeProject]);

  const handleStart = async () => {
    if (!activeProject) return;
    await api.startQueue(activeProject.id);
    await refreshQueue();
  };

  const handlePause = async () => {
    await api.pauseQueue();
    await refreshQueue();
  };

  const handleResume = async () => {
    await api.resumeQueue();
    await refreshQueue();
  };

  const handleStop = async () => {
    await api.stopQueue();
    await refreshQueue();
  };

  const handleRetry = async (pageId: string) => {
    await api.retryPage(pageId);
    await refreshPages();
    await refreshQueue();
  };

  const handleQuickDownloadPdf = async () => {
    if (!activeProject) return;
    setDownloadingPdf(true);
    try {
      const res = await api.exportPdf(activeProject.id, 'original');
      window.open(`${BASE_ORIGIN}${res.download_url}`, '_blank');
    } catch (e) {
      console.error(e);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleQuickDownloadZip = async () => {
    if (!activeProject) return;
    setDownloadingZip(true);
    try {
      const res = await api.exportZip(activeProject.id, 'original');
      window.open(`${BASE_ORIGIN}${res.download_url}`, '_blank');
    } catch (e) {
      console.error(e);
    } finally {
      setDownloadingZip(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="p-12 text-center text-zinc-500">
        <ListOrdered className="w-12 h-12 mx-auto text-zinc-600 mb-2" />
        <p className="text-sm">Please select or create a manga project first.</p>
      </div>
    );
  }

  const completedCount = pages.filter((p) => p.status === 'completed' || p.status === 'quality_flagged').length;
  const isFinished = pages.length > 0 && completedCount === pages.length && !queueStatus?.is_running;
  const progressPct = pages.length > 0 ? Math.round((completedCount / pages.length) * 100) : 0;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 select-none">
      {/* SUCCESS BANNER WHEN COMPLETED */}
      {isFinished && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950/80 via-studio-900 to-studio-900 border border-emerald-500/50 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg animate-in fade-in duration-300">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                All Pages Colorized Successfully!
                <Sparkles className="w-4 h-4 text-emerald-400" />
              </h2>
              <p className="text-xs text-zinc-300">
                Chapter {activeProject.chapter_num} is complete with full color and preserved line art.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={() => {
                if (pages.length > 0) setActivePage(pages[0].id);
                setTab('studio');
              }}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              <Eye className="w-4 h-4" />
              <span>Open in Studio</span>
            </button>

            <button
              onClick={handleQuickDownloadPdf}
              disabled={downloadingPdf}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
            >
              <FileText className="w-4 h-4" />
              <span>{downloadingPdf ? 'Compiling PDF...' : 'Download Full PDF'}</span>
            </button>

            <button
              onClick={handleQuickDownloadZip}
              disabled={downloadingZip}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-studio-800 hover:bg-studio-700 text-zinc-200 text-xs font-semibold border border-studio-700 transition-all disabled:opacity-50"
            >
              <Archive className="w-4 h-4 text-cyan-400" />
              <span>{downloadingZip ? 'Zipping...' : 'Download ZIP'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Queue Header & Global Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-6 rounded-2xl border border-studio-800">
        <div className="space-y-1">
          <div className="text-xs text-purple-400 font-semibold uppercase tracking-wider">Batch Processing Queue</div>
          <h1 className="text-2xl font-extrabold text-white">
            {activeProject.manga_title} &bull; Chapter {activeProject.chapter_num}
          </h1>
          <p className="text-xs text-zinc-400">
            Sequential single-page AI inference pipeline. Memory-safe for RTX 5060 8GB VRAM.
          </p>
        </div>

        {/* Global Control Buttons */}
        <div className="flex items-center gap-3">
          {!queueStatus?.is_running ? (
            <button
              onClick={handleStart}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-glow-purple transition-all"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>{completedCount > 0 ? 'Resume / Reprocess Chapter' : 'Start Chapter Processing'}</span>
            </button>
          ) : queueStatus.is_paused ? (
            <button
              onClick={handleResume}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>Resume</span>
            </button>
          ) : (
            <button
              onClick={handlePause}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              <Pause className="w-4 h-4" />
              <span>Pause</span>
            </button>
          )}

          {queueStatus?.is_running && (
            <button
              onClick={handleStop}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-studio-800 hover:bg-red-600/30 text-zinc-300 hover:text-red-300 text-xs font-semibold border border-studio-700 transition-colors"
            >
              <Square className="w-4 h-4" />
              <span>Stop</span>
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar Summary */}
      <div className="glass-panel p-5 rounded-xl border border-studio-800 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-zinc-300">Chapter Progress</span>
          <span className="font-mono text-purple-300">{completedCount} of {pages.length} Pages ({progressPct}%)</span>
        </div>
        <div className="w-full h-2.5 rounded-full bg-studio-850 overflow-hidden border border-studio-700/50">
          <div
            className="h-full bg-gradient-to-r from-purple-600 via-indigo-500 to-cyan-400 transition-all duration-300"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Sequential Queue Table */}
      <div className="glass-panel rounded-2xl border border-studio-800 overflow-hidden">
        <div className="p-4 border-b border-studio-800 flex items-center justify-between">
          <span className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Queue Order</span>
          <span className="text-xs text-zinc-500">{pages.length} pages queued</span>
        </div>

        <div className="divide-y divide-studio-800">
          {pages.map((page) => {
            const isCurrent = queueStatus?.current_page_id === page.id;
            const isDone = page.status === 'completed' || page.status === 'quality_flagged';
            return (
              <div
                key={page.id}
                className={`p-4 flex items-center justify-between gap-4 transition-colors ${isCurrent ? 'bg-purple-950/30' : 'hover:bg-studio-850/40'
                  }`}
              >
                {/* Left: Thumbnail & Page Number */}
                <div className="flex items-center gap-4">
                  <div
                    onClick={() => {
                      setActivePage(page.id);
                      setTab('studio');
                    }}
                    className="w-14 h-20 rounded-lg overflow-hidden bg-studio-950 flex-shrink-0 border border-studio-800 cursor-pointer hover:border-purple-500 transition-all relative group"
                  >
                    <img
                      src={`${BASE_ORIGIN}/api/pages/${page.id}/preview?t=${page.updated_at || Date.now()}`}
                      alt={page.filename}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        // Fallback to original if processed preview fails
                        (e.target as HTMLImageElement).src = `${BASE_ORIGIN}${page.original_url}`;
                      }}
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                      <Eye className="w-5 h-5 text-white" />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="text-sm font-bold text-white flex items-center gap-2">
                      <span>Page {page.page_number}</span>
                      {page.is_colored_preview && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-purple-600/30 text-purple-300 font-normal">
                          Colored Preview
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-zinc-400">{page.filename}</div>
                  </div>
                </div>

                {/* Center: Stage & Progress */}
                <div className="flex-1 max-w-md px-6 space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-zinc-300 font-medium">{page.stage || page.status}</span>
                    <span className="font-mono text-zinc-400">{page.progress || 0}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-studio-800 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-200 ${page.status === 'failed'
                          ? 'bg-red-500'
                          : isDone
                            ? 'bg-emerald-400'
                            : 'bg-purple-500 animate-pulse'
                        }`}
                      style={{ width: `${page.progress || 0}%` }}
                    />
                  </div>
                  {page.error_message && (
                    <div className="text-[10px] text-red-400 truncate">{page.error_message}</div>
                  )}
                </div>

                {/* Right: Actions (View in Studio, Download PNG, Retry) */}
                <div className="flex items-center gap-2.5">
                  <span className={`text-[10px] px-2.5 py-1 rounded-full font-mono uppercase border ${isDone
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : page.status === 'colorizing'
                        ? 'bg-purple-500/10 text-purple-400 border-purple-500/30 animate-pulse'
                        : page.status === 'failed'
                          ? 'bg-red-500/10 text-red-400 border-red-500/30'
                          : 'bg-zinc-800 text-zinc-400 border-zinc-700'
                    }`}>
                    {page.status}
                  </span>

                  {isDone && (
                    <>
                      <button
                        onClick={() => {
                          setActivePage(page.id);
                          setTab('studio');
                        }}
                        title="Open in Studio"
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 text-xs font-medium border border-purple-500/30 transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View</span>
                      </button>

                      <a
                        href={`${BASE_ORIGIN}/api/pages/${page.id}/download`}
                        download
                        title="Download Colorized PNG"
                        className="p-1.5 rounded-lg bg-studio-800 hover:bg-studio-700 text-zinc-300 hover:text-white border border-studio-700 transition-colors"
                      >
                        <Download className="w-4 h-4 text-cyan-400" />
                      </a>
                    </>
                  )}

                  {(page.status === 'failed' || isDone) && (
                    <button
                      onClick={() => handleRetry(page.id)}
                      title="Reprocess Page"
                      className="p-1.5 rounded-lg text-zinc-400 hover:text-purple-300 hover:bg-studio-800 transition-colors"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
