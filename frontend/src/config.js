export const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = API_URL.replace('http', 'ws');
