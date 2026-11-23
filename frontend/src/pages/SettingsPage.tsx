import React, { useEffect, useState } from 'react';
import { Settings, Cpu, Sparkles, RefreshCw, CheckCircle2, ShieldCheck } from 'lucide-react';
import { useStudioStore } from '../stores/useStudioStore';
import { api } from '../services/api';
import type { AIModelInfo } from '../services/api';

export const SettingsPage: React.FC = () => {
  const { hardware, refreshHardware } = useStudioStore();
  const [models, setModels] = useState<AIModelInfo[]>([]);
  const [activeModel, setActiveModel] = useState<string>('palette_propagator');
  const [flushing, setFlushing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchModels = async () => {
    try {
      const list = await api.getModels();
      setModels(list);
      const active = list.find((m) => m.is_active);
      if (active) setActiveModel(active.id);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchModels();
    refreshHardware();
  }, []);

  const handleSelectModel = async (modelId: string) => {
    await api.selectModel(modelId);
    setActiveModel(modelId);
    await fetchModels();
    setMessage(`Switched active colorization engine to ${modelId}`);
    setTimeout(() => setMessage(null), 3000);
  };

  const handleClearVram = async () => {
    setFlushing(true);
    await api.clearVram();
    await refreshHardware();
    setFlushing(false);
    setMessage('GPU VRAM cache flushed successfully.');
    setTimeout(() => setMessage(null), 3000);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 select-none">
      <div>
        <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-purple-400" />
          Hardware & AI Model Configuration
        </h1>
        <p className="text-xs text-zinc-400">
          Hardware telemetry, VRAM memory controls, and modular AI colorization adapters.
        </p>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{message}</span>
        </div>
      )}

      {/* Hardware Inspector */}
      <div className="glass-panel p-6 rounded-2xl border border-studio-800 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Active Hardware Environment
          </h2>
          <button
            onClick={handleClearVram}
            disabled={flushing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-studio-800 hover:bg-studio-700 text-zinc-300 text-xs font-mono border border-studio-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${flushing ? 'animate-spin' : ''}`} />
            <span>Flush VRAM Cache</span>
          </button>
        </div>

        {hardware && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-studio-800/60 border border-studio-700/60 space-y-1">
              <div className="text-[11px] text-zinc-400 font-medium">GPU Acceleration</div>
              <div className="text-sm font-bold text-emerald-400">{hardware.gpu.device_name}</div>
              <div className="text-xs font-mono text-zinc-300 mt-1">
                {Math.round(hardware.gpu.used_vram_mb)} / {Math.round(hardware.gpu.total_vram_mb)} MB VRAM
              </div>
            </div>

            <div className="p-4 rounded-xl bg-studio-800/60 border border-studio-700/60 space-y-1">
              <div className="text-[11px] text-zinc-400 font-medium">Processor & RAM</div>
              <div className="text-sm font-bold text-white">{hardware.cpu.cores} Cores &bull; {hardware.ram.total_gb} GB RAM</div>
              <div className="text-xs font-mono text-zinc-300 mt-1">
                RAM Used: {hardware.ram.used_gb} GB ({hardware.ram.percent}%)
              </div>
            </div>

            <div className="p-4 rounded-xl bg-studio-800/60 border border-studio-700/60 space-y-1">
              <div className="text-[11px] text-zinc-400 font-medium">Local Storage</div>
              <div className="text-sm font-bold text-white">{hardware.disk.total_gb} GB SSD</div>
              <div className="text-xs font-mono text-zinc-300 mt-1">
                Free: {hardware.disk.free_gb} GB ({100 - hardware.disk.percent}% available)
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modular AI Model Adapters */}
      <div className="glass-panel p-6 rounded-2xl border border-studio-800 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          Modular AI Colorization Engines
        </h2>
        <p className="text-xs text-zinc-400">
          The studio supports hot-swappable colorization engines. You can switch between the native edge-preserving palette propagation engine and custom deep checkpoints.
        </p>

        <div className="space-y-3">
          {models.map((m) => (
            <div
              key={m.id}
              onClick={() => handleSelectModel(m.id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                activeModel === m.id
                  ? 'bg-purple-600/20 border-purple-500/80 ring-1 ring-purple-500 text-white'
                  : 'bg-studio-800/60 border-studio-700 text-zinc-300 hover:bg-studio-750'
              }`}
            >
              <div className="space-y-1">
                <div className="font-bold text-sm flex items-center gap-2">
                  <span>{m.name}</span>
                  {activeModel === m.id && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/30 text-purple-300 font-mono">
                      ACTIVE
                    </span>
                  )}
                </div>
                <p className="text-xs text-zinc-400">{m.description}</p>
              </div>

              <span className={`text-xs font-mono ${m.is_available ? 'text-emerald-400' : 'text-zinc-500'}`}>
                {m.is_available ? 'Ready' : 'No Checkpoint'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Local-First & Zero Paid API Guarantee */}
      <div className="glass-panel p-6 rounded-2xl border border-studio-800 flex items-start gap-4">
        <ShieldCheck className="w-8 h-8 text-emerald-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h3 className="font-bold text-sm text-white">100% Local-First & Completely Free</h3>
          <p className="text-xs text-zinc-400">
            This application operates entirely on your local machine using your NVIDIA RTX 5060 GPU.
            No paid AI APIs, no cloud subscriptions, and no hidden third-party dependencies are used.
          </p>
        </div>
      </div>
    </div>
  );
};
