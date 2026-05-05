import type { BotStatus, HealthStatus, SystemMetrics, TaskInfo, WebhookStatus } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || '';

async function fetchJSON<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
  }
  return resp.json() as T;
}

export const api = {
  health: () => fetchJSON<HealthStatus>('/api/health'),
  botStatus: () => fetchJSON<BotStatus>('/api/bot/status'),
  botHandlers: () => fetchJSON<{ handlers: string[]; count: number }>('/api/bot/handlers'),
  tasks: (params?: { status?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.limit) qs.set('limit', String(params.limit));
    return fetchJSON<{ tasks: TaskInfo[]; total: number }>(`/api/tasks?${qs}`);
  },
  taskDetail: (id: string) => fetchJSON<TaskInfo>(`/api/tasks/${id}`),
  systemMetrics: () => fetchJSON<SystemMetrics>('/api/system/metrics'),
  eventsHistory: (params?: { event?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.event) qs.set('event', params.event);
    if (params?.limit) qs.set('limit', String(params.limit));
    return fetchJSON<{ events: Array<{ event: string; timestamp: number; data: unknown; source: string }>; count: number }>(`/api/events/history?${qs}`);
  },
  webhookStatus: () => fetchJSON<WebhookStatus>('/api/webhook/status'),
};
