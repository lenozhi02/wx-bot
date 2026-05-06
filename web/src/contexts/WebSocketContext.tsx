import { createContext, useContext, useState, useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { api } from '../services/api';
import type { BusEventData } from '../types';

export type BotActivity =
  | 'idle'
  | 'working'
  | 'writing'
  | 'researching'
  | 'executing'
  | 'syncing'
  | 'error';

export interface ActiveTask {
  taskId: string;
  handlerName: string;
  startedAt: number;
}

export interface FinishingTask extends ActiveTask {
  finishAt: number;
  resultStatus: 'completed' | 'failed' | 'cancelled';
}

export interface WorkerState {
  name: string;
  status: 'idle' | 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  task: {
    taskId: string;
    handlerName: string;
    progress: string;
    startedAt: number;
  } | null;
}

interface WSContextValue {
  connected: boolean;
  events: BusEventData[];
  latency: number;
  lastPing: number;
  activity: BotActivity;
  currentTask: ActiveTask | null;
  activeTasks: ActiveTask[];
  finishingTasks: FinishingTask[];
  taskCount: number;
  workers: WorkerState[];
  connect: () => void;
  disconnect: () => void;
}

const WebSocketContext = createContext<WSContextValue | null>(null);

const IDLE_TIMEOUT = 15000;
const FINISHING_DISPLAY_MS = 5000; // 任务完成后显示"收尾中"5秒

function inferActivity(handlerName: string): BotActivity {
  const h = handlerName.toLowerCase();
  if (h.includes('baidu') || h.includes('search')) return 'researching';
  if (h.includes('long')) return 'executing';
  if (h.includes('sync')) return 'syncing';
  if (h.includes('ai') || h.includes('write')) return 'writing';
  return 'working';
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const ws = useWebSocket(200);
  const [activity, setActivity] = useState<BotActivity>('idle');
  const [activeTasks, setActiveTasks] = useState<ActiveTask[]>([]);
  const [finishingTasks, setFinishingTasks] = useState<FinishingTask[]>([]);
  const [currentTask, setCurrentTask] = useState<ActiveTask | null>(null);
  const [workers, setWorkers] = useState<WorkerState[]>([]);
  const idleTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const prevConnected = useRef<boolean | undefined>(undefined);

  // === 关键修复：用 ref 避免 React 批量更新导致的闭包陷阱 ===
  const processedCount = useRef(0);
  const activeTasksRef = useRef<ActiveTask[]>([]);
  const finishingTasksRef = useRef<FinishingTask[]>([]);
  const workersRef = useRef<WorkerState[]>([]);

  // 同步 ref 与 state（确保 ref 始终最新）
  activeTasksRef.current = activeTasks;
  finishingTasksRef.current = finishingTasks;
  workersRef.current = workers;

  // 定时清理已完成的任务（收尾中 → 彻底移除）
  useEffect(() => {
    const timer = setInterval(() => {
      setFinishingTasks((prev) => {
        const remaining = prev.filter((t) => Date.now() - t.finishAt < FINISHING_DISPLAY_MS);
        finishingTasksRef.current = remaining;
        return remaining;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 监听事件，逐个处理所有未处理的新事件
  useEffect(() => {
    const allEvents = ws.events;
    const startIdx = processedCount.current;
    if (startIdx >= allEvents.length) return;

    const newEvents = allEvents.slice(startIdx);
    processedCount.current = allEvents.length;

    let nextActivity: BotActivity | null = null;
    let nextCurrentTask: ActiveTask | null = currentTask;
    let needsUpdate = false;

    for (const event of newEvents) {
      const handler = String(event.data.handler_name || event.data.handler || '');
      const taskId = String(event.data.task_id || '');

      // ── 任务开始 ──
      if (event.event === 'task:started' || event.event === 'task:submitted') {
        const newTask: ActiveTask = {
          taskId: taskId || `task-${Date.now()}`,
          handlerName: handler || 'UnknownTask',
          startedAt: Date.now(),
        };
        activeTasksRef.current = activeTasksRef.current.filter((t) => t.taskId !== newTask.taskId);
        activeTasksRef.current = [...activeTasksRef.current, newTask];
        nextCurrentTask = newTask;
        nextActivity = inferActivity(newTask.handlerName);
        if (idleTimer.current) clearTimeout(idleTimer.current);
        needsUpdate = true;

        // 更新对应 worker 的任务
        const workerName = String(event.data.worker || '');
        if (workerName) {
          const existingIdx = workersRef.current.findIndex((w) => w.name === workerName);
          const newWorker: WorkerState = {
            name: workerName,
            status: 'running',
            task: {
              taskId: newTask.taskId,
              handlerName: newTask.handlerName,
              progress: '',
              startedAt: newTask.startedAt,
            },
          };
          if (existingIdx >= 0) {
            workersRef.current = workersRef.current.map((w, i) => (i === existingIdx ? newWorker : w));
          } else {
            workersRef.current = [...workersRef.current, newWorker];
          }
        }
      }

      // ── 任务完成/失败/取消 ──
      if (
        event.event === 'task:completed' ||
        event.event === 'task:failed' ||
        event.event === 'task:cancelled'
      ) {
        const resultStatus =
          event.event === 'task:completed'
            ? 'completed'
            : event.event === 'task:failed'
            ? 'failed'
            : 'cancelled';

        const task = activeTasksRef.current.find((t) => t.taskId === taskId);
        activeTasksRef.current = activeTasksRef.current.filter((t) => t.taskId !== taskId);

        // 将完成的任务加入"收尾中"列表
        if (task) {
          finishingTasksRef.current = [
            ...finishingTasksRef.current.filter((t) => t.taskId !== taskId),
            { ...task, finishAt: Date.now(), resultStatus },
          ];
        }

        // 更新当前任务
        if (activeTasksRef.current.length > 0) {
          nextCurrentTask = activeTasksRef.current[activeTasksRef.current.length - 1];
          nextActivity = inferActivity(nextCurrentTask.handlerName);
        } else if (task) {
          nextCurrentTask = {
            taskId: task.taskId,
            handlerName: task.handlerName,
            startedAt: task.startedAt,
          };
          nextActivity = 'working';
        } else {
          nextCurrentTask = null;
          nextActivity = 'idle';
        }
        needsUpdate = true;

        // 清除对应 worker 的任务（保留 worker 条目，状态设为 idle）
        workersRef.current = workersRef.current.map((w) =>
          w.task?.taskId === taskId
            ? { ...w, status: resultStatus === 'completed' ? 'success' : 'failed', task: null }
            : w
        );
      }

      // ── 进度更新 ──
      if (event.event === 'task:progress') {
        const progressTaskId = String(event.data.task_id || '');
        workersRef.current = workersRef.current.map((w) =>
          w.task?.taskId === progressTaskId
            ? { ...w, task: { ...w.task, progress: String(event.data.progress || '') } }
            : w
        );
        needsUpdate = true;
      }

      // ── 消息收到 ──
      if (event.event === 'bot:message_received') {
        if (activeTasksRef.current.length === 0 && finishingTasksRef.current.length === 0) {
          nextActivity = 'working';
          if (idleTimer.current) clearTimeout(idleTimer.current);
          idleTimer.current = setTimeout(() => setActivity('idle'), IDLE_TIMEOUT);
          needsUpdate = true;
        }
      }

      // ── 消息发送 ──
      if (event.event === 'bot:message_sent') {
        if (activeTasksRef.current.length === 0 && finishingTasksRef.current.length === 0) {
          nextActivity = 'idle';
          needsUpdate = true;
        }
      }
    }

    // 批量更新 state（只更新一次）
    if (needsUpdate) {
      setActiveTasks([...activeTasksRef.current]);
      setFinishingTasks([...finishingTasksRef.current]);
      setWorkers([...workersRef.current]);
      if (nextCurrentTask !== undefined) setCurrentTask(nextCurrentTask);
      if (nextActivity !== null) setActivity(nextActivity);
    }
  }, [ws.events, currentTask]);

  // 连接断开检测
  useEffect(() => {
    const wasConnected = prevConnected.current;
    const isConnected = ws.connected;
    if (wasConnected === true && isConnected === false) {
      setActivity('error');
      if (idleTimer.current) clearTimeout(idleTimer.current);
    }
    prevConnected.current = isConnected;
  }, [ws.connected]);

  // 初始化 worker 状态（从 API 获取，弥补 WebSocket 连接前的事件丢失）
  useEffect(() => {
    if (!ws.connected) return;
    const initWorkers = async () => {
      try {
        const status = await api.botStatus();
        if (status.workers && status.workers.length > 0) {
          const mapped = status.workers.map((w) => ({
            name: w.name,
            status: w.status,
            task: w.task
              ? {
                  taskId: w.task.task_id,
                  handlerName: w.task.handler_name,
                  progress: w.task.progress,
                  startedAt: w.task.started_at,
                }
              : null,
          }));
          setWorkers(mapped);
          workersRef.current = mapped;
        }
      } catch (e) {
        // 静默失败，不影响 UI
      }
    };
    initWorkers();
    // 每 10 秒同步一次，确保状态不漂移
    const interval = setInterval(initWorkers, 10000);
    return () => clearInterval(interval);
  }, [ws.connected]);

  const taskCount = activeTasks.length + finishingTasks.length;

  return (
    <WebSocketContext.Provider
      value={{ ...ws, activity, currentTask, activeTasks, finishingTasks, taskCount, workers }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWS() {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error('useWS must be used within WebSocketProvider');
  return ctx;
}
