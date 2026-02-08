import { create } from 'zustand';
import { api, Config, Status } from '../api/client';

interface AppState {
  config: Config | null;
  status: Status | null;
  logs: string[];
  isLoading: boolean;
  
  fetchConfig: () => Promise<void>;
  fetchStatus: () => Promise<void>;
  fetchLogs: () => Promise<void>;
  updateConfig: (config: Config) => Promise<void>;
  runTask: () => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  config: null,
  status: null,
  logs: [],
  isLoading: false,

  fetchConfig: async () => {
    try {
      const config = await api.getConfig();
      set({ config });
    } catch (e) {
      console.error(e);
    }
  },

  fetchStatus: async () => {
    try {
      const status = await api.getStatus();
      set({ status });
    } catch (e) {
      console.error(e);
    }
  },

  fetchLogs: async () => {
    try {
      const { logs } = await api.getLogs();
      set({ logs });
    } catch (e) {
      console.error(e);
    }
  },

  updateConfig: async (config) => {
    set({ isLoading: true });
    try {
      await api.updateConfig(config);
      set({ config });
      await get().fetchStatus(); // Status might change (scheduler restart)
    } catch (e) {
      console.error(e);
    } finally {
      set({ isLoading: false });
    }
  },

  runTask: async () => {
    set({ isLoading: true });
    try {
      await api.runTask();
      await get().fetchLogs(); // Logs updated
    } catch (e) {
      console.error(e);
    } finally {
      set({ isLoading: false });
    }
  },

  uploadFile: async (file) => {
    set({ isLoading: true });
    try {
        await api.uploadFile(file);
    } catch (e) {
        console.error(e);
        throw e;
    } finally {
        set({ isLoading: false });
    }
  },
}));
