const runtimeApiUrl = typeof window !== 'undefined' && window._env_?.VITE_API_URL && !window._env_.VITE_API_URL.includes('${')
  ? window._env_.VITE_API_URL
  : null;

export const API_URL = runtimeApiUrl || import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = API_URL.replace('http', 'ws');
