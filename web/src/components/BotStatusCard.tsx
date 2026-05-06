import { useEffect, useState } from 'react';
import { Bot, Zap, List, Wifi, Monitor } from 'lucide-react';
import { api } from '../services/api';
import { PixelCard } from './PixelCard';
import { PixelBadge } from './PixelBadge';
import type { BotStatus, WorkerState } from '../types';

interface Props {
  compact?: boolean;
}

export function BotStatusCard({ compact }: Props) {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.botStatus();
        setStatus(data);
        setError('');
      } catch (e) {
        setError(String(e));
      }
    };
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  const inner = (
    <>
      {error && <div className="text-[#e94560] text-sm">{error}</div>}
      {!status && !error && <div className="text-[#64748b] text-sm">加载中...</div>}
      {status && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-[#94a3b8]">
              <Zap className="w-4 h-4 text-[#ffd700]" />
              <span>运行状态</span>
            </div>
            <PixelBadge color={status.running ? 'green' : 'red'}>
              {status.running ? '运行中' : '已停止'}
            </PixelBadge>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-[#94a3b8]">
              <Wifi className="w-4 h-4 text-[#3b82f6]" />
              <span>Webhook</span>
            </div>
            <PixelBadge color={status.webhook_enabled ? 'green' : 'slate'}>
              {status.webhook_enabled ? '已启用' : '已禁用'}
            </PixelBadge>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-[#94a3b8]">
              <Monitor className="w-4 h-4 text-[#a855f7]" />
              <span>Worker 池</span>
            </div>
            <span className="text-sm text-[#e2e8f0] font-bold">{status.executor_workers} 个</span>
          </div>

          {/* Worker 详情 */}
          {status.workers && status.workers.length > 0 && (
            <div className="space-y-1.5 pt-1">
              {status.workers.map((w) => (
                <WorkerRow key={w.name} worker={w} />
              ))}
            </div>
          )}

          <div className="pt-2 border-t-2 border-[#0e1119]">
            <div className="flex items-center gap-2 text-sm text-[#94a3b8] mb-2">
              <List className="w-4 h-4 text-[#a855f7]" />
              <span>已注册处理器 ({status.handlers.length})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {status.handlers.map((h) => (
                <PixelBadge key={h} color="slate">{h}</PixelBadge>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );

  if (compact) {
    return <div className="h-full overflow-auto">{inner}</div>;
  }

  return (
    <PixelCard title="Bot 状态" titleIcon={<Bot className="w-4 h-4" />}>
      {inner}
    </PixelCard>
  );
}

function WorkerRow({ worker }: { worker: WorkerState }) {
  const isIdle = worker.status === 'idle';
  const isRunning = worker.status === 'running';
  const isSuccess = worker.status === 'success';

  const color = isIdle
    ? 'text-[#64748b]'
    : isRunning
    ? 'text-[#3b82f6]'
    : isSuccess
    ? 'text-[#22c55e]'
    : 'text-[#e94560]';

  const dotColor = isIdle
    ? '#64748b'
    : isRunning
    ? '#3b82f6'
    : isSuccess
    ? '#22c55e'
    : '#e94560';

  const shortName = worker.name.replace('worker-', 'W');
  const taskName = worker.task
    ? worker.task.handler_name.replace(/TaskHandler|Handler/g, '')
    : '空闲';

  return (
    <div className="flex items-center gap-2 px-2 py-1 bg-[#0e1119]/50 border border-[#1f2937]">
      <div
        className="w-1.5 h-1.5 shrink-0"
        style={{
          background: dotColor,
          animation: isRunning ? 'pixelPulse 0.8s steps(2) infinite' : undefined,
        }}
      />
      <span className="text-[10px] font-bold text-[#94a3b8] w-8 shrink-0">{shortName}</span>
      <span className={`text-[10px] flex-1 truncate ${color}`}>
        {taskName}
        {worker.task?.progress && (
          <span className="ml-1 opacity-70">{worker.task.progress}</span>
        )}
      </span>
      <PixelBadge color={isIdle ? 'slate' : isRunning ? 'blue' : isSuccess ? 'green' : 'red'}>
        {isIdle ? '空闲' : isRunning ? '执行' : isSuccess ? '完成' : '失败'}
      </PixelBadge>
    </div>
  );
}
