import { useEffect, useState } from 'react';
import type { BotActivity, ActiveTask } from '../../contexts/WebSocketContext';

interface Props {
  activity: BotActivity;
  currentTask: ActiveTask | null;
  taskCount: number;
  isFinishing?: boolean;
  finishStatus?: 'completed' | 'failed' | 'cancelled';
}

const stateConfig: Record<BotActivity, {
  emoji: string;
  x: string;
  y: string;
  color: string;
}> = {
  idle: { emoji: '🤖', x: '72%', y: '50%', color: '#94a3b8' },
  working: { emoji: '👨‍💻', x: '38%', y: '48%', color: '#ffd700' },
  writing: { emoji: '✍️', x: '38%', y: '48%', color: '#3b82f6' },
  researching: { emoji: '🔍', x: '38%', y: '48%', color: '#a855f7' },
  executing: { emoji: '⚡', x: '38%', y: '48%', color: '#f59e0b' },
  syncing: { emoji: '🔄', x: '85%', y: '52%', color: '#22c55e' },
  error: { emoji: '💀', x: '85%', y: '52%', color: '#e94560' },
};

function formatBubbleText(
  activity: BotActivity,
  task: ActiveTask | null,
  count: number,
  isFinishing?: boolean,
  finishStatus?: string
): string {
  if (activity === 'error') return '连接断开！';
  if (isFinishing) {
    const icon = finishStatus === 'completed' ? '✅' : finishStatus === 'failed' ? '❌' : '⚠️';
    return `${icon} 收尾中...`;
  }
  if (activity === 'idle') return count > 0 ? '处理完毕！' : '待命中...';
  if (!task) return '正在忙碌...';

  const name = task.handlerName
    .replace('TaskHandler', '')
    .replace('Handler', '');

  if (count > 1) {
    return `[${name}] +${count - 1}个排队中`;
  }
  return `[${name}]`;
}

export function PixelCharacter({ activity, currentTask, taskCount, isFinishing, finishStatus }: Props) {
  const config = stateConfig[activity] || stateConfig.idle;
  const [bounce, setBounce] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setBounce((b) => !b), 800);
    return () => clearInterval(timer);
  }, []);

  const bubbleText = formatBubbleText(activity, currentTask, taskCount, isFinishing, finishStatus);

  return (
    <div
      className="absolute transition-all duration-700 ease-in-out"
      style={{ left: config.x, top: config.y, zIndex: 100 }}
    >
      {/* 多任务堆叠标记 */}
      {taskCount > 1 && !isFinishing && activity !== 'idle' && activity !== 'error' && (
        <div
          className="absolute -top-14 left-1/2 -translate-x-1/2 whitespace-nowrap"
          style={{
            background: '#e94560',
            border: '2px solid #ffd700',
            padding: '1px 6px',
            color: '#fff',
            fontSize: '10px',
            fontWeight: 'bold',
          }}
        >
          x{taskCount} 任务
        </div>
      )}

      {/* 收尾标记 */}
      {isFinishing && (
        <div
          className="absolute -top-14 left-1/2 -translate-x-1/2 whitespace-nowrap"
          style={{
            background: finishStatus === 'completed' ? '#22c55e' : '#e94560',
            border: '2px solid #ffd700',
            padding: '1px 6px',
            color: '#fff',
            fontSize: '10px',
            fontWeight: 'bold',
          }}
        >
          {finishStatus === 'completed' ? '✅ 完成' : finishStatus === 'failed' ? '❌ 失败' : '⚠️ 取消'}
        </div>
      )}

      {/* 气泡 */}
      <div
        className="absolute -top-10 left-1/2 -translate-x-1/2 whitespace-nowrap"
        style={{
          background: '#1a1a2e',
          border: '2px solid ' + config.color,
          padding: '2px 8px',
          color: config.color,
          fontSize: '11px',
          fontWeight: 'bold',
          maxWidth: '200px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
      >
        {bubbleText}
        <div
          className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-2 h-2 rotate-45"
          style={{
            background: '#1a1a2e',
            borderRight: '2px solid ' + config.color,
            borderBottom: '2px solid ' + config.color,
          }}
        />
      </div>

      {/* 角色 */}
      <div
        className="text-4xl"
        style={{
          transform: bounce ? 'translateY(-2px)' : 'translateY(0)',
          transition: 'transform 0.4s ease',
          filter: 'drop-shadow(3px 3px 0 rgba(0,0,0,0.4))',
        }}
      >
        {config.emoji}
      </div>
    </div>
  );
}
