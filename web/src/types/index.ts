// WX-BOT Web UI 类型定义

export interface WorkerState {
  name: string;
  status: 'idle' | 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  task: {
    task_id: string;
    handler_name: string;
    progress: string;
    started_at: number;
  } | null;
}

export interface BotStatus {
  running: boolean;
  handlers: string[];
  webhook_enabled: boolean;
  executor_workers: number;
  workers: WorkerState[];
}

export interface TaskInfo {
  task_id: string;
  handler_name: string;
  user_id: string;
  status: string;
  progress: string;
  created_at: number;
  started_at: number | null;
  finished_at: number | null;
  duration: number;
}

export interface SystemMetrics {
  timestamp: number;
  cpu?: {
    percent: number;
    count: number;
  };
  memory?: {
    total: number;
    available: number;
    percent: number;
    used: number;
  };
  disk?: {
    total: number;
    used: number;
    free: number;
    percent: number;
  };
  uptime?: number;
  processes?: number;
  error?: string;
}

export interface BusEventData {
  event: string;
  timestamp: number;
  data: Record<string, unknown>;
  source: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  event_bus: {
    subscribers: Record<string, number>;
    history_size: number;
  };
  websocket: {
    connected_clients: number;
    clients: Array<{
      id: string;
      subscribed_events: string[];
      connected_at: number;
      duration: number;
    }>;
  };
}

export interface WebhookStatus {
  enabled: boolean;
  host?: string;
  port?: number;
  default_user?: string | null;
  recent_users?: string[];
  queue_size?: number;
}

export type WSMessage =
  | { type: 'connected'; client_id: string; message: string }
  | { type: 'subscribed'; events: string[] }
  | { type: 'event'; event: string; timestamp: number; data: Record<string, unknown>; source: string }
  | { type: 'pong'; time: number }
  | { type: 'error'; message: string };
