import { useEffect, useState } from 'react';
import { Bot, Zap, MessageCircle, List, Wifi } from 'lucide-react';
import { api } from '../services/api';
import { PixelCard } from './PixelCard';
import { PixelBadge } from './PixelBadge';
import type { BotStatus } from '../types';

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
              <MessageCircle className="w-4 h-4 text-[#f59e0b]" />
              <span>任务 Worker</span>
            </div>
            <span className="text-sm text-[#e2e8f0] font-bold">{status.executor_workers} 个</span>
          </div>

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
