export interface HardwareTelemetry {
  cpu: {
    percent: number;
    cores: number;
  };
  ram: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    percent: number;
  };
  disk: {
    total_gb: number;
    free_gb: number;
    percent: number;
  };
  gpu: {
    available: boolean;
    device_name: string;
    total_vram_mb: number;
    used_vram_mb: number;
    free_vram_mb: number;
    utilization_percent: number;
    device_count: number;
  };
}

export interface Project {
  id: string;
  title: string;
  manga_title: string;
  chapter_num: string;
  description: string;
  mode: 'new_manga' | 'preview_reference' | 'character_reference' | 'combined';
  coloring_style: string;
  output_resolution: string;
  status: string;
  created_at: string;
  updated_at: string;
  page_count: number;
  completed_page_count: number;
  character_count: number;
}

export interface MangaPage {
  id: string;
  project_id: string;
  page_number: number;
  filename: string;
  original_url: string;
  preview_url?: string;
  processed_url?: string;
  processed_path?: string;
  updated_at?: string;
  width: number;
  height: number;
  is_colored_preview: boolean;
  status: 'pending' | 'analyzing' | 'colorizing' | 'completed' | 'failed' | 'quality_flagged' | 'retry';
  stage: string;
  progress: number;
  error_message?: string;
  quality_report?: {
    passed: boolean;
    score: number;
    flags: string[];
    metrics: {
      bubble_leak_ratio: number;
      wash_ratio: number;
      coverage_ratio: number;
    };
  };
}

export interface CharacterProfile {
  id: string;
  project_id: string;
  name: string;
  hair_color: string;
  skin_color: string;
  eye_color: string;
  primary_outfit_color: string;
  secondary_outfit_color: string;
  accent_color: string;
  confidence_score: number;
  first_appearance_page: number;
  last_appearance_page: number;
  avatar_url?: string;
  is_locked: boolean;
  appearances_count?: number;
}

export interface AIModelInfo {
  id: string;
  name: string;
  description: string;
  is_available: boolean;
  is_active: boolean;
}

export interface QueueStatus {
  is_running: boolean;
  is_paused: boolean;
  current_project_id: string | null;
  current_page_id: string | null;
}

export const BASE_ORIGIN = typeof window !== 'undefined' && window.location.port !== '8000' 
  ? `${window.location.protocol}//${window.location.hostname || 'localhost'}:8000` 
  : '';

export const API_BASE = `${BASE_ORIGIN}/api`;

export const api = {
  // Hardware
  getHardware: async (): Promise<HardwareTelemetry> => {
    const res = await fetch(`${API_BASE}/hardware/telemetry`);
    return res.json();
  },
  clearVram: async () => {
    const res = await fetch(`${API_BASE}/hardware/clear-vram`, { method: 'POST' });
    return res.json();
  },

  // Projects
  getProjects: async (): Promise<Project[]> => {
    const res = await fetch(`${API_BASE}/projects`);
    return res.json();
  },
  getProject: async (id: string): Promise<{ project: Project; pages: MangaPage[] }> => {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    return res.json();
  },
  createProject: async (data: Partial<Project>): Promise<Project> => {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return res.json();
  },
  deleteProject: async (id: string) => {
    const res = await fetch(`${API_BASE}/projects/${id}`, { method: 'DELETE' });
    return res.json();
  },
  uploadFiles: async (projectId: string, files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const res = await fetch(`${API_BASE}/projects/${projectId}/upload`, {
      method: 'POST',
      body: formData,
    });
    return res.json();
  },
  analyzeChapter: async (projectId: string) => {
    const res = await fetch(`${API_BASE}/projects/${projectId}/analyze`, { method: 'POST' });
    return res.json();
  },

  // Characters (CCMS)
  getCharacters: async (projectId: string): Promise<CharacterProfile[]> => {
    const res = await fetch(`${API_BASE}/characters/project/${projectId}`);
    return res.json();
  },
  updateCharacter: async (charId: string, updates: Partial<CharacterProfile>): Promise<CharacterProfile> => {
    const res = await fetch(`${API_BASE}/characters/${charId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    return res.json();
  },
  propagateCharacter: async (charId: string) => {
    const res = await fetch(`${API_BASE}/characters/${charId}/propagate`, { method: 'POST' });
    return res.json();
  },
  uploadReferenceImage: async (projectId: string, charName: string, file: File) => {
    const formData = new FormData();
    formData.append('character_name', charName);
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/characters/project/${projectId}/reference-upload`, {
      method: 'POST',
      body: formData,
    });
    return res.json();
  },

  // Studio Tools
  smartFloodFill: async (pageId: string, x: number, y: number, colorHex: string, tolerance: number = 32) => {
    const res = await fetch(`${API_BASE}/studio/page/${pageId}/flood-fill`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_type: 'flood_fill', x, y, color_hex: colorHex, tolerance }),
    });
    return res.json();
  },
  saveLayer: async (pageId: string, layerBase64: string) => {
    const res = await fetch(`${API_BASE}/studio/page/${pageId}/save-layer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ layer_base64_png: layerBase64 }),
    });
    return res.json();
  },
  reprocessPage: async (pageId: string) => {
    const res = await fetch(`${API_BASE}/studio/page/${pageId}/reprocess`, { method: 'POST' });
    return res.json();
  },

  // Queue
  getQueueStatus: async (): Promise<QueueStatus> => {
    const res = await fetch(`${API_BASE}/queue/status`);
    return res.json();
  },
  startQueue: async (projectId: string) => {
    const res = await fetch(`${API_BASE}/queue/${projectId}/start`, { method: 'POST' });
    return res.json();
  },
  pauseQueue: async () => {
    const res = await fetch(`${API_BASE}/queue/pause`, { method: 'POST' });
    return res.json();
  },
  resumeQueue: async () => {
    const res = await fetch(`${API_BASE}/queue/resume`, { method: 'POST' });
    return res.json();
  },
  stopQueue: async () => {
    const res = await fetch(`${API_BASE}/queue/stop`, { method: 'POST' });
    return res.json();
  },
  retryPage: async (pageId: string) => {
    const res = await fetch(`${API_BASE}/queue/page/${pageId}/retry`, { method: 'POST' });
    return res.json();
  },

  // Exports
  getExportRecords: async (projectId: string): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/export/${projectId}/records`);
    return res.json();
  },
  exportPdf: async (projectId: string, scale: string = 'original') => {
    const res = await fetch(`${API_BASE}/export/${projectId}/pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ export_type: 'pdf', resolution_scale: scale }),
    });
    return res.json();
  },
  exportZip: async (projectId: string, scale: string = 'original') => {
    const res = await fetch(`${API_BASE}/export/${projectId}/zip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ export_type: 'zip', resolution_scale: scale }),
    });
    return res.json();
  },

  // Models
  getModels: async (): Promise<AIModelInfo[]> => {
    const res = await fetch(`${API_BASE}/models`);
    return res.json();
  },
  selectModel: async (modelId: string) => {
    const res = await fetch(`${API_BASE}/models/select/${modelId}`, { method: 'POST' });
    return res.json();
  },
};
