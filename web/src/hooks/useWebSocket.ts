import { useState, useEffect, useRef, useCallback } from 'react';
import type { BusEventData, WSMessage } from '../types';

const WS_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`;

interface UseWebSocketReturn {
  connected: boolean;
  events: BusEventData[];
  latency: number;
  lastPing: number;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket(maxEvents: number = 200): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState<BusEventData[]>([]);
  const [latency, setLatency] = useState(0);
  const [lastPing, setLastPing] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const pingTimeRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const closedIntentionally = useRef(false);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (closedIntentionally.current) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        console.log('[WS] 已连接');
        ws.send(JSON.stringify({ type: 'subscribe', events: ['*'] }) as string);
      };

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data) as WSMessage;
          handleMessage(msg);
        } catch {
          console.warn('[WS] 收到非 JSON 消息:', e.data);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        if (!closedIntentionally.current) {
          console.log('[WS] 已断开，3秒后重连...');
          reconnectTimerRef.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = (err) => {
        console.error('[WS] 错误:', err);
        ws.close();
      };
    } catch (e) {
      console.error('[WS] 连接失败:', e);
      if (!closedIntentionally.current) {
        reconnectTimerRef.current = setTimeout(connect, 3000);
      }
    }
  }, []);

  const handleMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case 'connected':
        console.log('[WS]', msg.message);
        break;
      case 'event':
        setEvents((prev) => {
          const next = [...prev, {
            event: msg.event,
            timestamp: msg.timestamp,
            data: msg.data,
            source: msg.source,
          }];
          return next.length > maxEvents ? next.slice(-maxEvents) : next;
        });
        break;
      case 'pong':
        setLatency(Date.now() - pingTimeRef.current);
        setLastPing(Date.now());
        break;
    }
  }, [maxEvents]);

  const disconnect = useCallback(() => {
    closedIntentionally.current = true;
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = undefined;
    }
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  // 心跳
  useEffect(() => {
    if (!connected) return;
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        pingTimeRef.current = Date.now();
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 15000);
    return () => clearInterval(interval);
  }, [connected]);

  // 自动连接
  useEffect(() => {
    closedIntentionally.current = false;
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return { connected, events, latency, lastPing, connect, disconnect };
}
