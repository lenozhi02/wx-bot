import { Wifi, WifiOff, Clock } from 'lucide-react';

interface Props {
  connected: boolean;
  latency: number;
  lastPing: number;
}

export function ConnectionStatus({ connected, latency, lastPing }: Props) {
  const timeSincePing = lastPing ? Math.round((Date.now() - lastPing) / 1000) : 0;

  return (
    <div className="flex items-center gap-4 text-sm">
      <div className="flex items-center gap-1.5">
        {connected ? (
          <>
            <Wifi className="w-4 h-4 text-[#22c55e]" />
            <span className="text-[#22c55e] font-bold">已连接</span>
          </>
        ) : (
          <>
            <WifiOff className="w-4 h-4 text-[#e94560]" />
            <span className="text-[#e94560] font-bold">已断开</span>
          </>
        )}
      </div>
      {connected && latency > 0 && (
        <div className="flex items-center gap-1.5 text-[#94a3b8]">
          <Clock className="w-3.5 h-3.5" />
          <span>延迟: {latency}ms</span>
        </div>
      )}
      {connected && lastPing > 0 && (
        <span className="text-[#64748b] text-xs">心跳: {timeSincePing}s前</span>
      )}
    </div>
  );
}
