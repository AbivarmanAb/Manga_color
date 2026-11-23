import React, { useState, useRef, useEffect } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  PaintBucket, 
  Paintbrush, 
  Pipette, 
  MousePointer, 
  SplitSquareVertical, 
  Eye, 
  Sparkles, 
  AlertTriangle,
  RefreshCw,
  Download,
  FileText
} from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api, BASE_ORIGIN } from '../services/api';

export const ColorizationStudio: React.FC = () => {
  const { 
    activeProject, 
    pages, 
    activePageId, 
    setActivePage, 
    characters, 
    refreshPages,
    activeTool,
    setActiveTool,
    brushColor,
    setBrushColor,
    tolerance,
    setTolerance,
    splitPosition,
    setSplitPosition,
    viewMode,
    setViewMode,
    zoom,
    setZoom,
    pan,
    setPan
  } = useStudioStore();

  const [isDraggingSplit, setIsDraggingSplit] = useState(false);
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });
  const [reprocessing, setReprocessing] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [vibrancy, setVibrancy] = useState(125);
  const [contrast, setContrast] = useState(106);
  const [brightness, setBrightness] = useState(100);
  const containerRef = useRef<HTMLDivElement>(null);

  const currentPage = pages.find((p) => p.id === activePageId) || pages[0];

  useEffect(() => {
    refreshPages();
  }, [activeProject]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (activeTool === 'select' || e.button === 1 || e.altKey) {
      setIsPanning(true);
      setStartPan({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDraggingSplit && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const pos = ((e.clientX - rect.left) / rect.width) * 100;
      setSplitPosition(Math.max(5, Math.min(95, pos)));
    } else if (isPanning) {
      setPan({ x: e.clientX - startPan.x, y: e.clientY - startPan.y });
    }
  };

  const handleMouseUp = () => {
    setIsDraggingSplit(false);
    setIsPanning(false);
  };

  const handleCanvasClick = async (e: React.MouseEvent<HTMLImageElement>) => {
    if (activeTool !== 'fill' || !currentPage || !currentPage.processed_path) return;

    // Get click coordinates relative to original image size
    const img = e.currentTarget;
    const rect = img.getBoundingClientRect();
    const scaleX = currentPage.width / rect.width;
    const scaleY = currentPage.height / rect.height;

    const clickX = Math.round((e.clientX - rect.left) * scaleX);
    const clickY = Math.round((e.clientY - rect.top) * scaleY);

    try {
      await api.smartFloodFill(currentPage.id, clickX, clickY, brushColor, tolerance);
      await refreshPages();
    } catch (err) {
      console.error('Fill error:', err);
    }
  };

  const handleReprocess = async () => {
    if (!currentPage) return;
    setReprocessing(true);
    try {
      await api.reprocessPage(currentPage.id);
      await refreshPages();
    } catch (err) {
      console.error(err);
    } finally {
      setReprocessing(false);
    }
  };

  const handleExportPdf = async () => {
    if (!activeProject) return;
    setDownloadingPdf(true);
    try {
      const res = await api.exportPdf(activeProject.id, 'original');
      window.open(`${BASE_ORIGIN}${res.download_url}`, '_blank');
    } catch (err) {
      console.error(err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (!activeProject || pages.length === 0) {
    return (
      <div className="p-12 text-center text-zinc-500">
        <Sparkles className="w-12 h-12 mx-auto text-zinc-600 mb-2" />
        <p className="text-sm">No active project or pages found. Please create a project first.</p>
      </div>
    );
  }

  const originalImgUrl = currentPage ? `${BASE_ORIGIN}${currentPage.original_url}` : '';
  const processedImgUrl = currentPage?.processed_path 
    ? `${BASE_ORIGIN}/api/pages/${currentPage.id}/processed?t=${currentPage.updated_at || Date.now()}`
    : originalImgUrl;

  const qualityReport = currentPage?.quality_report;

  return (
    <div className="h-[calc(100vh-3.5rem)] flex overflow-hidden select-none bg-studio-950">
      {/* LEFT PANEL: Thumbnails & Quick Characters */}
      <div className="w-64 border-r border-studio-800 bg-studio-900/90 flex flex-col justify-between">
        <div className="p-3 border-b border-studio-800 flex items-center justify-between">
          <span className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Pages ({pages.length})</span>
          <button onClick={refreshPages} className="text-zinc-500 hover:text-zinc-300">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Page Thumbnails Vertical Scroll */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
          {pages.map((p) => {
            const isSelected = p.id === activePageId;
            return (
              <div
                key={p.id}
                onClick={() => setActivePage(p.id)}
                className={`p-2 rounded-xl cursor-pointer border transition-all flex items-center gap-3 ${
                  isSelected
                    ? 'bg-purple-600/20 border-purple-500/80 shadow-sm'
                    : 'bg-studio-850/60 border-studio-800 hover:border-studio-700'
                }`}
              >
                <div className="w-12 h-16 rounded overflow-hidden bg-studio-950 flex-shrink-0 relative">
                  <img
                    src={`${BASE_ORIGIN}/api/pages/${p.id}/preview?t=${p.updated_at || Date.now()}`}
                    alt={p.filename}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = `${BASE_ORIGIN}${p.original_url}`;
                    }}
                  />
                  {(p.status === 'completed' || p.status === 'quality_flagged') && (
                    <span className="absolute bottom-1 right-1 w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  )}
                  {p.is_colored_preview && (
                    <span className="absolute top-1 left-1 text-[8px] bg-purple-600 text-white font-bold px-1 rounded">
                      C
                    </span>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-zinc-200 truncate">Page {p.page_number}</div>
                  <div className="text-[10px] text-zinc-400 capitalize truncate">{p.stage || p.status}</div>
                  {p.status === 'quality_flagged' && (
                    <span className="inline-flex items-center gap-1 text-[9px] text-amber-400 mt-1">
                      <AlertTriangle className="w-2.5 h-2.5" /> QA Check
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* CENTER WORKSPACE: Interactive Canvas */}
      <div 
        className="flex-1 flex flex-col relative overflow-hidden bg-transparency-grid"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
      >
        {/* Canvas Toolbar */}
        <div className="h-12 bg-studio-900/90 border-b border-studio-800 px-4 flex items-center justify-between z-20 backdrop-blur-md">
          {/* View Mode Controls */}
          <div className="flex items-center gap-1 bg-studio-800/80 p-0.5 rounded-lg border border-studio-700/60 text-xs">
            <button
              onClick={() => setViewMode('split')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                viewMode === 'split' ? 'bg-purple-600 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <SplitSquareVertical className="w-3.5 h-3.5" />
              <span>Split Slider</span>
            </button>
            <button
              onClick={() => setViewMode('colored-only')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                viewMode === 'colored-only' ? 'bg-purple-600 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Full Color</span>
            </button>
            <button
              onClick={() => setViewMode('original-only')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all flex items-center gap-1.5 ${
                viewMode === 'original-only' ? 'bg-purple-600 text-white shadow-sm' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <span>B&W Manga</span>
            </button>
          </div>

          {/* Zoom & Pan Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setZoom(Math.max(0.2, zoom - 0.15))}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-studio-800 transition-colors"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-xs font-mono text-zinc-300 w-12 text-center">{Math.round(zoom * 100)}%</span>
            <button
              onClick={() => setZoom(Math.min(4.0, zoom + 0.15))}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-studio-800 transition-colors"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={() => { setZoom(1.0); setPan({ x: 0, y: 0 }); }}
              title="Reset View"
              className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-studio-800 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          {/* Direct Action Buttons: Download Page PNG, Export PDF, AI Reprocess */}
          <div className="flex items-center gap-2">
            {currentPage && (
              <a
                href={`${BASE_ORIGIN}/api/pages/${currentPage.id}/download`}
                download
                title="Download this page as PNG"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-studio-800 hover:bg-studio-700 text-zinc-200 text-xs font-semibold border border-studio-700 transition-all"
              >
                <Download className="w-3.5 h-3.5 text-cyan-400" />
                <span>Download PNG</span>
              </a>
            )}

            <button
              onClick={handleExportPdf}
              disabled={downloadingPdf}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 text-xs font-semibold border border-emerald-500/40 disabled:opacity-50 transition-all"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{downloadingPdf ? 'Generating...' : 'Export PDF'}</span>
            </button>

            <button
              onClick={handleReprocess}
              disabled={reprocessing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600/30 hover:bg-purple-600/50 text-purple-300 text-xs font-semibold border border-purple-500/40 disabled:opacity-50 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{reprocessing ? 'Reprocessing...' : 'AI Reprocess'}</span>
            </button>
          </div>
        </div>

        {/* Large Canvas Viewport */}
        <div
          ref={containerRef}
          onMouseDown={handleMouseDown}
          className="flex-1 relative overflow-hidden flex items-center justify-center cursor-default"
        >
          {currentPage && (
            <div
              className="relative transition-transform duration-75 shadow-2xl"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                maxWidth: '90%',
                maxHeight: '90%',
              }}
            >
              {/* Full Color Layer or Base View */}
              {viewMode === 'colored-only' && (
                <img
                  src={processedImgUrl}
                  alt="Colorized Page"
                  onClick={handleCanvasClick}
                  style={{ filter: `saturate(${vibrancy}%) contrast(${contrast}%) brightness(${brightness}%)` }}
                  className="max-h-[82vh] max-w-full object-contain pointer-events-auto rounded shadow-2xl transition-[filter] duration-75"
                />
              )}

              {/* B&W Original Layer */}
              {viewMode === 'original-only' && (
                <img
                  src={originalImgUrl}
                  alt="Original Manga"
                  className="max-h-[82vh] max-w-full object-contain rounded shadow-2xl"
                />
              )}

              {/* Interactive Split-Screen Slider View */}
              {viewMode === 'split' && (
                <div className="relative overflow-hidden select-none max-h-[82vh]">
                  {/* Underneath: Full Color Image */}
                  <img
                    src={processedImgUrl}
                    alt="Colorized"
                    onClick={handleCanvasClick}
                    style={{ filter: `saturate(${vibrancy}%) contrast(${contrast}%) brightness(${brightness}%)` }}
                    className="max-h-[82vh] max-w-full object-contain pointer-events-auto rounded shadow-2xl block transition-[filter] duration-75"
                  />

                  {/* Top Layer: Original B&W Image with CSS Clip-path */}
                  <div
                    className="absolute inset-0 overflow-hidden pointer-events-none"
                    style={{ clipPath: `inset(0 ${100 - splitPosition}% 0 0)` }}
                  >
                    <img
                      src={originalImgUrl}
                      alt="Original B&W"
                      className="max-h-[82vh] max-w-full object-contain block"
                    />
                  </div>

                  {/* Draggable Divider Line & Knob */}
                  <div
                    onMouseDown={(e) => {
                      e.stopPropagation();
                      setIsDraggingSplit(true);
                    }}
                    className="absolute top-0 bottom-0 w-1 bg-gradient-to-b from-purple-500 via-white to-cyan-400 cursor-ew-resize z-30 flex items-center justify-center"
                    style={{ left: `${splitPosition}%` }}
                  >
                    <div className="w-6 h-6 rounded-full bg-studio-900 border-2 border-white shadow-lg flex items-center justify-center text-[10px] text-zinc-300">
                      &harr;
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* RIGHT PANEL: Studio Tools, Palettes & Quality Audit */}
      <div className="w-80 border-l border-studio-800 bg-studio-900/90 flex flex-col justify-between p-4 space-y-6 overflow-y-auto">
        <div className="space-y-6">
          {/* Tools Selector */}
          <div className="space-y-2">
            <span className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Studio Tools</span>
            <div className="grid grid-cols-4 gap-2">
              {[
                { id: 'select', label: 'Pan', icon: <MousePointer className="w-4 h-4" /> },
                { id: 'fill', label: 'Flood Fill', icon: <PaintBucket className="w-4 h-4" /> },
                { id: 'brush', label: 'Brush', icon: <Paintbrush className="w-4 h-4" /> },
                { id: 'eyedropper', label: 'Picker', icon: <Pipette className="w-4 h-4" /> },
              ].map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => setActiveTool(tool.id as any)}
                  className={`flex flex-col items-center justify-center p-2 rounded-xl border text-[11px] font-medium transition-all ${
                    activeTool === tool.id
                      ? 'bg-purple-600 text-white border-purple-400 shadow-glow-purple'
                      : 'bg-studio-850 border-studio-700 text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  {tool.icon}
                  <span className="mt-1">{tool.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Active Color & Swatch Selection */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Active Color</span>
              <div className="flex items-center gap-1.5">
                <input
                  type="color"
                  value={brushColor}
                  onChange={(e) => setBrushColor(e.target.value)}
                  className="w-6 h-6 rounded cursor-pointer border-0 bg-transparent"
                />
                <span className="text-xs font-mono text-zinc-300 uppercase">{brushColor}</span>
              </div>
            </div>

            {/* Tolerance Slider for Flood Fill */}
            {activeTool === 'fill' && (
              <div className="space-y-1.5 p-3 rounded-xl bg-studio-850/80 border border-studio-800">
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-400">Boundary Tolerance</span>
                  <span className="font-mono text-purple-300">{tolerance}</span>
                </div>
                <input
                  type="range"
                  min="8"
                  max="80"
                  value={tolerance}
                  onChange={(e) => setTolerance(Number(e.target.value))}
                  className="w-full accent-purple-500"
                />
                <p className="text-[10px] text-zinc-500">
                  Fill respects manga black line art borders without leaking.
                </p>
              </div>
            )}
          </div>

          {/* Character Quick-Pick Swatches from CCMS */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Character Swatches (CCMS)</span>
            <div className="space-y-2">
              {characters.map((c) => (
                <div key={c.id} className="p-2.5 rounded-xl bg-studio-850/60 border border-studio-800 space-y-1.5">
                  <div className="text-xs font-semibold text-zinc-200">{c.name}</div>
                  <div className="flex items-center gap-1.5">
                    {[
                      { label: 'Hair', color: c.hair_color },
                      { label: 'Skin', color: c.skin_color },
                      { label: 'Eyes', color: c.eye_color },
                      { label: 'Outfit 1', color: c.primary_outfit_color },
                      { label: 'Outfit 2', color: c.secondary_outfit_color },
                      { label: 'Accent', color: c.accent_color },
                    ].map((swatch, idx) => (
                      <button
                        key={idx}
                        onClick={() => setBrushColor(swatch.color)}
                        title={`${c.name} - ${swatch.label} (${swatch.color})`}
                        style={{ backgroundColor: swatch.color }}
                        className={`w-6 h-6 rounded-md border border-white/20 hover:scale-110 transition-transform ${
                          brushColor.toLowerCase() === swatch.color.toLowerCase() ? 'ring-2 ring-white' : ''
                        }`}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Color Grading & Vibrancy Controls */}
          <div className="space-y-3 p-3 rounded-xl bg-studio-850/80 border border-studio-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Color Tuning & Mood</span>
              <button
                onClick={() => { setVibrancy(100); setContrast(100); setBrightness(100); }}
                className="text-[10px] text-zinc-400 hover:text-zinc-200 underline"
              >
                Reset
              </button>
            </div>

            {/* Quick Mood Presets */}
            <div className="grid grid-cols-2 gap-1.5 text-[10px]">
              <button
                onClick={() => { setVibrancy(145); setContrast(112); setBrightness(102); }}
                className="px-2 py-1 rounded-lg bg-studio-800 hover:bg-purple-600/30 text-purple-300 font-medium border border-studio-700 transition-colors"
              >
                Shueisha Digital
              </button>
              <button
                onClick={() => { setVibrancy(165); setContrast(110); setBrightness(104); }}
                className="px-2 py-1 rounded-lg bg-studio-800 hover:bg-emerald-600/30 text-emerald-300 font-medium border border-studio-700 transition-colors"
              >
                Vibrant Anime
              </button>
              <button
                onClick={() => { setVibrancy(90); setContrast(125); setBrightness(96); }}
                className="px-2 py-1 rounded-lg bg-studio-800 hover:bg-cyan-600/30 text-cyan-300 font-medium border border-studio-700 transition-colors"
              >
                Cinematic Drama
              </button>
              <button
                onClick={() => { setVibrancy(85); setContrast(95); setBrightness(105); }}
                className="px-2 py-1 rounded-lg bg-studio-800 hover:bg-amber-600/30 text-amber-300 font-medium border border-studio-700 transition-colors"
              >
                Classic Retro
              </button>
            </div>

            {/* Vibrancy / Saturation */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-zinc-400">Saturation / Vibrancy</span>
                <span className="font-mono text-purple-300">{vibrancy}%</span>
              </div>
              <input
                type="range"
                min="50"
                max="220"
                value={vibrancy}
                onChange={(e) => setVibrancy(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            {/* Contrast */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-zinc-400">Contrast</span>
                <span className="font-mono text-purple-300">{contrast}%</span>
              </div>
              <input
                type="range"
                min="80"
                max="140"
                value={contrast}
                onChange={(e) => setContrast(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            {/* Brightness */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-zinc-400">Brightness</span>
                <span className="font-mono text-purple-300">{brightness}%</span>
              </div>
              <input
                type="range"
                min="85"
                max="125"
                value={brightness}
                onChange={(e) => setBrightness(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>
          </div>

          {/* Automated Quality Audit Report */}
          {qualityReport && (
            <div className="p-4 rounded-xl bg-studio-850 border border-studio-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-zinc-200">Quality Check</span>
                <span className={`text-xs font-bold font-mono ${
                  qualityReport.passed ? 'text-emerald-400' : 'text-amber-400'
                }`}>
                  {Math.round(qualityReport.score * 100)}%
                </span>
              </div>

              <div className="space-y-1 text-[11px] text-zinc-400">
                <div className="flex justify-between">
                  <span>Speech Bubble Contamination:</span>
                  <span className="font-mono text-zinc-300">
                    {(qualityReport.metrics.bubble_leak_ratio * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Line Art Preservation:</span>
                  <span className="font-mono text-zinc-300">
                    {(100 - qualityReport.metrics.wash_ratio * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
