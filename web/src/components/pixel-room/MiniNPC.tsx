import type { ActiveTask, FinishingTask } from '../../contexts/WebSocketContext';

interface Props {
  activeTasks: ActiveTask[];
  finishingTasks: FinishingTask[];
}

const minions = ['👾', '🐱', '🦎', '👻', '🤖', '🦄', '🐙'];
const positions = [
  { x: '12%', y: '62%' },
  { x: '58%', y: '58%' },
  { x: '88%', y: '68%' },
  { x: '25%', y: '72%' },
  { x: '65%', y: '72%' },
];

export function MiniNPC({ activeTasks, finishingTasks }: Props) {
  // 活跃的排队任务（除当前任务）
  const queueTasks = activeTasks.slice(0, -1);
  // 收尾中的任务
  const finishing = finishingTasks;

  if (queueTasks.length === 0 && finishing.length === 0) return null;

  return (
    <>
      {/* 活跃排队任务 */}
      {queueTasks.map((task, i) => {
        const pos = positions[i % positions.length];
        const emoji = minions[i % minions.length];
        const name = task.handlerName
          .replace('TaskHandler', '')
          .replace('Handler', '');

        return (
          <div
            key={task.taskId}
            className="absolute"
            style={{
              left: pos.x,
              top: pos.y,
              zIndex: 90 + i,
              animation: 'fadeIn 0.3s ease-out',
            }}
          >
            <div
              className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap"
              style={{
                background: '#1a1a2e',
                border: '2px solid #64748b',
                padding: '1px 5px',
                color: '#94a3b8',
                fontSize: '9px',
                fontWeight: 'bold',
              }}
            >
              {name}
              <div
                className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rotate-45"
                style={{
                  background: '#1a1a2e',
                  borderRight: '2px solid #64748b',
                  borderBottom: '2px solid #64748b',
                }}
              />
            </div>
            <div
              className="text-xl"
              style={{
                filter: 'drop-shadow(2px 2px 0 rgba(0,0,0,0.3))',
                animation: `bounceMini ${1 + i * 0.3}s ease-in-out infinite`,
              }}
            >
              {emoji}
            </div>
          </div>
        );
      })}

      {/* 收尾中任务（显示在角落，带淡出动画） */}
      {finishing.map((task, i) => {
        const pos = positions[(queueTasks.length + i) % positions.length];
        const emoji = '✨';
        const name = task.handlerName
          .replace('TaskHandler', '')
          .replace('Handler', '');
        const color = task.resultStatus === 'completed' ? '#22c55e' : '#e94560';

        return (
          <div
            key={`finish-${task.taskId}`}
            className="absolute"
            style={{
              left: pos.x,
              top: pos.y,
              zIndex: 95 + i,
              animation: 'poof 4.5s ease-out forwards',
            }}
          >
            <div
              className="absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap"
              style={{
                background: '#1a1a2e',
                border: `2px solid ${color}`,
                padding: '1px 5px',
                color,
                fontSize: '9px',
                fontWeight: 'bold',
              }}
            >
              {task.resultStatus === 'completed' ? '✅' : '❌'} {name}
              <div
                className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rotate-45"
                style={{
                  background: '#1a1a2e',
                  borderRight: `2px solid ${color}`,
                  borderBottom: `2px solid ${color}`,
                }}
              />
            </div>
            <div
              className="text-xl"
              style={{
                filter: `drop-shadow(2px 2px 0 ${color}80)`,
              }}
            >
              {emoji}
            </div>
          </div>
        );
      })}
    </>
  );
}
