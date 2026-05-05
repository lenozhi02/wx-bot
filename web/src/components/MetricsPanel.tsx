import { useEffect, useState } from 'react';
import { Cpu, HardDrive, MemoryStick, Clock, Activity } from 'lucide-react';
import { api } from '../services/api';
import { PixelCard } from './PixelCard';
import type { SystemMetrics } from '../types';

interface Props {
  compact?: boolean;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

const colorMap: Record<string, string> = {
  blue: 'bg-[#3b82f6]',
  purple: 'bg-[#a855f7]',
  amber: 'bg-[#f59e0b]',
};

function ProgressBar({ percent, color }: { percent: number; color: string }) {
  const base = colorMap[color] || 'bg-[#64748b]';
  const colorClass = percent > 90 ? 'bg-[#e94560]' : percent > 70 ? 'bg-[#f59e0b]' : base;
  return (
    <div className="w-full bg-[#0e1119] h-3 mt-1.5 border border-[#1f2937]">
      <div
        className={`h-full transition-all duration-500 ${colorClass}`}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
  );
}

export function MetricsPanel({ compact }: Props) {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.systemMetrics();
        setMetrics(data);
        setError('');
      } catch (e) {
        setError(String(e));
      }
    };
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const inner = (
    <>
      {error && <div className="text-[#e94560] text-sm">{error}</div>}
      {!metrics && !error && <div className="text-[#64748b] text-sm">加载中...</div>}
      {metrics && (
        <div className="space-y-4">
          {metrics.cpu && (
            <div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 text-[#94a3b8]">
                  <Cpu className="w-4 h-4 text-[#3b82f6]" />
                  <span>CPU</span>
                </div>
                <span className="text-[#e2e8f0] font-bold">{metrics.cpu.percent}% · {metrics.cpu.count}核</span>
              </div>
              <ProgressBar percent={metrics.cpu.percent} color="blue" />
            </div>
          )}

          {metrics.memory && (
            <div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 text-[#94a3b8]">
                  <MemoryStick className="w-4 h-4 text-[#a855f7]" />
                  <span>内存</span>
                </div>
                <span className="text-[#e2e8f0] font-bold">{metrics.memory.percent}% · {formatBytes(metrics.memory.used)}/{formatBytes(metrics.memory.total)}</span>
              </div>
              <ProgressBar percent={metrics.memory.percent} color="purple" />
            </div>
          )}

          {metrics.disk && (
            <div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 text-[#94a3b8]">
                  <HardDrive className="w-4 h-4 text-[#f59e0b]" />
                  <span>磁盘</span>
                </div>
                <span className="text-[#e2e8f0] font-bold">{metrics.disk.percent}% · {formatBytes(metrics.disk.used)}/{formatBytes(metrics.disk.total)}</span>
              </div>
              <ProgressBar percent={metrics.disk.percent} color="amber" />
            </div>
          )}

          {metrics.uptime !== undefined && (
            <div className="flex items-center gap-2 text-sm text-[#94a3b8] pt-2 border-t-2 border-[#0e1119]">
              <Clock className="w-4 h-4 text-[#22c55e]" />
              <span>运行时长: {Math.floor(metrics.uptime / 3600)}h {Math.floor((metrics.uptime % 3600) / 60)}m</span>
            </div>
          )}

          {metrics.processes !== undefined && (
            <div className="text-xs text-[#64748b]">进程数: {metrics.processes}</div>
          )}
        </div>
      )}
    </>
  );

  if (compact) {
    return <div className="h-full overflow-auto">{inner}</div>;
  }

  return (
    <PixelCard title="系统状态" titleIcon={<Activity className="w-4 h-4" />}>
      {inner}
    </PixelCard>
  );
}
