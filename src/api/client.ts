const BASE_URL = 'http://localhost:8000/api';

export interface Config {
  monitor_folder: string;
  wecom: {
    corpid: string;
    secret: string;
    agentid: string;
    touser: string;
    toparty: string;
    token?: string;
    aes_key?: string;
  };
  schedule: {
    enabled: boolean;
    time: string;
    frequency: string;
  };
}

export interface Status {
  running: boolean;
  next_run: string | null;
}

export const api = {
  getStatus: async (): Promise<Status> => {
    const res = await fetch(`${BASE_URL}/status`);
    return res.json();
  },

  getConfig: async (): Promise<Config> => {
    const res = await fetch(`${BASE_URL}/config`);
    return res.json();
  },

  updateConfig: async (config: Config): Promise<any> => {
    const res = await fetch(`${BASE_URL}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return res.json();
  },

  runTask: async (): Promise<any> => {
    const res = await fetch(`${BASE_URL}/run`, {
      method: 'POST',
    });
    return res.json();
  },

  getLogs: async (): Promise<{ logs: string[] }> => {
    const res = await fetch(`${BASE_URL}/logs`);
    return res.json();
  },

  uploadFile: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },
};
