import { create } from 'zustand';
import { api } from '../services/api';
import type { Project, MangaPage, CharacterProfile, HardwareTelemetry, AIModelInfo, QueueStatus } from '../services/api';

export type NavigationTab = 
  | 'dashboard'
  | 'new-project'
  | 'projects'
  | 'studio'
  | 'characters'
  | 'references'
  | 'queue'
  | 'exports'
  | 'settings';

interface StudioState {
  currentTab: NavigationTab;
  activeProjectId: string | null;
  activeProject: Project | null;
  pages: MangaPage[];
  activePageId: string | null;
  characters: CharacterProfile[];
  hardware: HardwareTelemetry | null;
  models: AIModelInfo[];
  queueStatus: QueueStatus | null;
  
  // Studio Interactive Editor State
  activeTool: 'select' | 'brush' | 'fill' | 'eyedropper' | 'eraser';
  brushColor: string;
  brushSize: number;
  brushOpacity: number;
  tolerance: number;
  zoom: number;
  pan: { x: number; y: number };
  splitPosition: number; // 0 to 100
  viewMode: 'split' | 'side-by-side' | 'colored-only' | 'original-only';
  selectedCharacterId: string | null;
  
  // Actions
  setTab: (tab: NavigationTab) => void;
  setActiveProject: (projectId: string) => Promise<void>;
  setActivePage: (pageId: string) => void;
  refreshHardware: () => Promise<void>;
  refreshQueue: () => Promise<void>;
  refreshPages: () => Promise<void>;
  refreshCharacters: () => Promise<void>;
  setActiveTool: (tool: 'select' | 'brush' | 'fill' | 'eyedropper' | 'eraser') => void;
  setBrushColor: (color: string) => void;
  setBrushSize: (size: number) => void;
  setTolerance: (tol: number) => void;
  setZoom: (zoom: number) => void;
  setPan: (pan: { x: number; y: number }) => void;
  setSplitPosition: (pos: number) => void;
  setViewMode: (mode: 'split' | 'side-by-side' | 'colored-only' | 'original-only') => void;
  setSelectedCharacterId: (id: string | null) => void;
}

export const useStudioStore = create<StudioState>((set, get) => ({
  currentTab: 'dashboard',
  activeProjectId: null,
  activeProject: null,
  pages: [],
  activePageId: null,
  characters: [],
  hardware: null,
  models: [],
  queueStatus: null,
  
  // Studio default tools
  activeTool: 'select',
  brushColor: '#2563EB',
  brushSize: 18,
  brushOpacity: 1.0,
  tolerance: 32,
  zoom: 1.0,
  pan: { x: 0, y: 0 },
  splitPosition: 50,
  viewMode: 'split',
  selectedCharacterId: null,

  setTab: (tab) => set({ currentTab: tab }),

  setActiveProject: async (projectId: string) => {
    try {
      const data = await api.getProject(projectId);
      const chars = await api.getCharacters(projectId);
      const firstPageId = data.pages.length > 0 ? data.pages[0].id : null;
      set({
        activeProjectId: projectId,
        activeProject: data.project,
        pages: data.pages,
        activePageId: firstPageId,
        characters: chars,
      });
    } catch (e) {
      console.error('Failed to set active project', e);
    }
  },

  setActivePage: (pageId: string) => set({ activePageId: pageId }),

  refreshHardware: async () => {
    try {
      const hw = await api.getHardware();
      set({ hardware: hw });
    } catch (e) {
      console.error('Failed to fetch hardware', e);
    }
  },

  refreshQueue: async () => {
    try {
      const qs = await api.getQueueStatus();
      set({ queueStatus: qs });
    } catch (e) {
      console.error('Failed to fetch queue', e);
    }
  },

  refreshPages: async () => {
    const { activeProjectId } = get();
    if (!activeProjectId) return;
    try {
      const data = await api.getProject(activeProjectId);
      set({ pages: data.pages, activeProject: data.project });
    } catch (e) {
      console.error('Failed to refresh pages', e);
    }
  },

  refreshCharacters: async () => {
    const { activeProjectId } = get();
    if (!activeProjectId) return;
    try {
      const chars = await api.getCharacters(activeProjectId);
      set({ characters: chars });
    } catch (e) {
      console.error('Failed to refresh characters', e);
    }
  },

  setActiveTool: (tool) => set({ activeTool: tool }),
  setBrushColor: (color) => set({ brushColor: color }),
  setBrushSize: (size) => set({ brushSize: size }),
  setTolerance: (tol) => set({ tolerance: tol }),
  setZoom: (zoom) => set({ zoom }),
  setPan: (pan) => set({ pan }),
  setSplitPosition: (pos) => set({ splitPosition: pos }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setSelectedCharacterId: (id) => set({ selectedCharacterId: id }),
}));
