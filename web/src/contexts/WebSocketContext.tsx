import { createContext, useContext, useState, useEffect, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
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
  const idleTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const prevConnected = useRef<boolean | undefined>(undefined);

  // 定时清理已完成的任务（收尾中 → 彻底移除）
  useEffect(() => {
    const timer = setInterval(() => {
      setFinishingTasks((prev) =>
        prev.filter((t) => Date.now() - t.finishAt < FINISHING_DISPLAY_MS)
      );
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 监听事件，更新任务状态
  useEffect(() => {
    const latest = ws.events[ws.events.length - 1];
    if (!latest) return;

    const handler = String(latest.data.handler_name || latest.data.handler || '');
    const taskId = String(latest.data.task_id || '');

    // 任务开始
    if (latest.event === 'task:started' || latest.event === 'task:submitted') {
      const newTask: ActiveTask = {
        taskId: taskId || `task-${Date.now()}`,
        handlerName: handler || 'UnknownTask',
        startedAt: Date.now(),
      };
      setActiveTasks((prev) => {
        const filtered = prev.filter((t) => t.taskId !== newTask.taskId);
        return [...filtered, newTask];
      });
      setCurrentTask(newTask);
      setActivity(inferActivity(newTask.handlerName));
      if (idleTimer.current) clearTimeout(idleTimer.current);
    }

    // 任务完成/失败/取消 → 移到"收尾中"列表，5秒后消失
    if (
      latest.event === 'task:completed' ||
      latest.event === 'task:failed' ||
      latest.event === 'task:cancelled'
    ) {
      const resultStatus = latest.event === 'task:completed'
        ? 'completed'
        : latest.event === 'task:failed'
        ? 'failed'
        : 'cancelled';

      setActiveTasks((prev) => {
        const task = prev.find((t) => t.taskId === taskId);
        const remaining = prev.filter((t) => t.taskId !== taskId);

        // 将完成的任务加入"收尾中"列表
        if (task) {
          setFinishingTasks((ft) => [
            ...ft.filter((t) => t.taskId !== taskId),
            { ...task, finishAt: Date.now(), resultStatus },
          ]);
        }

        // 更新当前任务为最新的活跃任务
        if (remaining.length > 0) {
          setCurrentTask(remaining[remaining.length - 1]);
          setActivity(inferActivity(remaining[remaining.length - 1].handlerName));
        } else if (task) {
          // 没有活跃任务了，但还有收尾中任务，显示收尾状态
          setCurrentTask({
            taskId: task.taskId,
            handlerName: task.handlerName,
            startedAt: task.startedAt,
          });
          setActivity('working'); // 收尾中也算working
        } else {
          setCurrentTask(null);
          setActivity('idle');
        }

        return remaining;
      });
    }

    // 消息收到
    if (latest.event === 'bot:message_received') {
      if (activeTasks.length === 0 && finishingTasks.length === 0) {
        setActivity('working');
        if (idleTimer.current) clearTimeout(idleTimer.current);
        idleTimer.current = setTimeout(() => setActivity('idle'), IDLE_TIMEOUT);
      }
    }

    // 消息发送
    if (latest.event === 'bot:message_sent') {
      if (activeTasks.length === 0 && finishingTasks.length === 0) {
        setActivity('idle');
      }
    }
  }, [ws.events, activeTasks.length, finishingTasks.length]);

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

  const taskCount = activeTasks.length + finishingTasks.length;

  return (
    <WebSocketContext.Provider
      value={{ ...ws, activity, currentTask, activeTasks, finishingTasks, taskCount }}
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
