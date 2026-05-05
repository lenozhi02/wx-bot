import { useState, useEffect, useRef } from 'react';

export interface MetricsPoint {
  time: string;
  timestamp: number;
  cpu: number;
  memory: number;
  memoryUsed: number;
  memoryTotal: number;
}

const MAX_POINTS = 60;

export function useMetricsHistory(intervalMs: number = 3000) {
  const [history, setHistory] = useState<MetricsPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;

    const fetchMetrics = async () => {
      try {
        const resp = await fetch('/api/system/metrics');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        const now = Date.now();
        const timeStr = new Date(now).toLocaleTimeString('zh-CN', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });

        const point: MetricsPoint = {
          time: timeStr,
          timestamp: now,
          cpu: data.cpu?.percent ?? 0,
          memory: data.memory?.percent ?? 0,
          memoryUsed: data.memory?.used ?? 0,
          memoryTotal: data.memory?.total ?? 1,
        };

        if (mounted.current) {
          setHistory((prev) => {
            const next = [...prev, point];
            return next.length > MAX_POINTS ? next.slice(-MAX_POINTS) : next;
          });
          setError('');
          setLoading(false);
        }
      } catch (e) {
        if (mounted.current) {
          setError(String(e));
          setLoading(false);
        }
      }
    };

    fetchMetrics();
    const timer = setInterval(fetchMetrics, intervalMs);
    return () => {
      mounted.current = false;
      clearInterval(timer);
    };
  }, [intervalMs]);

  return { history, loading, error };
}
