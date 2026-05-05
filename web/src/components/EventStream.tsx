import { useRef, useEffect } from 'react';
import type { BusEventData } from '../types';
import { MessageSquare, Rocket, CheckCircle, XCircle, AlertTriangle, Globe, Cpu } from 'lucide-react';
import { PixelCard } from './PixelCard';

interface Props {
  events: BusEventData[];
  compact?: boolean;
}

function getEventIcon(event: string) {
  if (event.includes('message')) return <MessageSquare className="w-3.5 h-3.5 text-[#3b82f6]" />;
  if (event.includes('task:started') || event.includes('task:submitted')) return <Rocket className="w-3.5 h-3.5 text-[#f59e0b]" />;
  if (event.includes('task:completed')) return <CheckCircle className="w-3.5 h-3.5 text-[#22c55e]" />;
  if (event.includes('task:failed')) return <XCircle className="w-3.5 h-3.5 text-[#e94560]" />;
  if (event.includes('webhook')) return <Globe className="w-3.5 h-3.5 text-[#a855f7]" />;
  if (event.includes('bot:connected') || event.includes('bot:disconnected')) return <Cpu className="w-3.5 h-3.5 text-[#22c55e]" />;
  return <AlertTriangle className="w-3.5 h-3.5 text-[#64748b]" />;
}

function getEventColor(event: string) {
  if (event.includes('failed')) return 'border-l-[#e94560]';
  if (event.includes('completed')) return 'border-l-[#22c55e]';
  if (event.includes('started')) return 'border-l-[#f59e0b]';
  if (event.includes('message')) return 'border-l-[#3b82f6]';
  return 'border-l-[#64748b]';
}

function formatTime(ts: number) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('zh-CN', { hour12: false });
}

function formatEventSummary(event: string, data: Record<string, unknown>): string {
  if (event === 'bot:message_received') {
    const from = String(data.from_user || '').slice(0, 20);
    const content = String(data.content || '').slice(0, 30);
    return `[${from}] ${content}`;
  }
  if (event === 'bot:message_sent') {
    const to = String(data.to_user || '').slice(0, 20);
    return `→ [${to}]`;
  }
  if (event.startsWith('task:')) {
    const name = String(data.handler_name || '');
    const id = String(data.task_id || '').slice(-6);
    return `[${name}] ${id}`;
  }
  if (event.startsWith('webhook:')) {
    return String(data.text_preview || '').slice(0, 40);
  }
  return JSON.stringify(data).slice(0, 50);
}

export function EventStream({ events, compact }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  const content = (
    <>
      {!compact && (
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-[#64748b]">{events.length} 条</span>
        </div>
      )}
      <div ref={scrollRef} className={`space-y-1 ${compact ? 'h-full overflow-y-auto' : ''}`}>
        {events.length === 0 && (
          <div className="text-center text-[#64748b] py-8 text-sm">等待事件...</div>
        )}
        {events.map((ev, i) => (
          <div
            key={`${ev.timestamp}-${i}`}
            className={`event-item flex items-start gap-2 px-3 py-2 bg-[#0e1119] border-l-2 ${getEventColor(ev.event)} hover:bg-[#1a1b2f] transition-colors`}
          >
            <div className="mt-0.5 shrink-0">{getEventIcon(ev.event)}</div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 text-xs">
                <span className="text-[#64748b] font-mono">{formatTime(ev.timestamp)}</span>
                <span className="text-[#e2e8f0] font-bold">{ev.event}</span>
              </div>
              <div className="text-xs text-[#94a3b8] mt-0.5 truncate">
                {formatEventSummary(ev.event, ev.data)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  );

  if (compact) {
    return content;
  }

  return (
    <PixelCard
      title="实时事件流"
      titleIcon={<span className="w-2 h-2 bg-[#22c55e] pixel-pulse inline-block" />}
      className="h-full flex flex-col"
    >
      {content}
    </PixelCard>
  );
}
