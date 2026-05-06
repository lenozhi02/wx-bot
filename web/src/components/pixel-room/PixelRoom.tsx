import { useWS } from '../../contexts/WebSocketContext';
import type { BotActivity, ActiveTask, FinishingTask, WorkerState } from '../../contexts/WebSocketContext';
import { PixelCharacter } from './PixelCharacter';
import { MiniNPC } from './MiniNPC';

interface Props {
  activity: BotActivity;
  currentTask: ActiveTask | null;
  activeTasks: ActiveTask[];
  finishingTasks: FinishingTask[];
  taskCount: number;
  workers: WorkerState[];
}

export function PixelRoom({ activity, currentTask, activeTasks, finishingTasks, taskCount, workers }: Props) {
  const { connected } = useWS();

  // 真正的活跃任务数（不含收尾中）
  const activeCount = activeTasks.length;
  // 是否有收尾中任务
  const hasFinishing = finishingTasks.length > 0;
  // 最上层的收尾任务
  const topFinishing = finishingTasks[finishingTasks.length - 1];

  // 服务器忙碌度：活跃任务越多，闪烁越快
  const pulseSpeed = activeCount > 3 ? '0.3s' : activeCount > 1 ? '0.6s' : '1.5s';

  return (
    <div
      className="relative w-full overflow-hidden select-none"
      style={{ aspectRatio: '16/9', maxHeight: '420px' }}
    >
      {/* 房间整体背景 */}
      <div className="absolute inset-0 bg-[#2d2420]">
        {/* 地板 - checkerboard 像素格子 */}
        <div
          className="absolute bottom-0 left-0 right-0"
          style={{
            height: '55%',
            background: `
              repeating-conic-gradient(#3d3028 0% 25%, #4a3c32 0% 50%) 0 0 / 24px 24px
            `,
            imageRendering: 'pixelated',
          }}
        />
        {/* 墙壁 */}
        <div
          className="absolute top-0 left-0 right-0"
          style={{
            height: '45%',
            background: '#5c4033',
            borderBottom: '4px solid #3d3028',
          }}
        />
        {/* 墙壁砖纹 */}
        <div
          className="absolute top-0 left-0 right-0 opacity-20"
          style={{
            height: '45%',
            background: `
              repeating-linear-gradient(0deg, transparent, transparent 18px, #2d1f1a 18px, #2d1f1a 20px),
              repeating-linear-gradient(90deg, transparent, transparent 38px, #2d1f1a 38px, #2d1f1a 40px)
            `,
          }}
        />
        {/* 地板与墙壁交界线 */}
        <div className="absolute left-0 right-0" style={{ top: '45%', height: '4px', background: '#2d1f1a' }} />
      </div>

      {/* 窗户 */}
      <div
        className="absolute"
        style={{
          top: '8%',
          left: '8%',
          width: '14%',
          height: '22%',
          background: '#87ceeb',
          border: '4px solid #3d3028',
          boxShadow: 'inset 0 0 0 2px #2d1f1a',
        }}
      >
        <div className="absolute top-1/2 left-0 right-0 h-1 bg-[#3d3028] -translate-y-1/2" />
        <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-[#3d3028] -translate-x-1/2" />
        <div className="absolute top-2 right-2 text-lg">🌙</div>
      </div>

      {/* 海报 - 左侧 */}
      <div
        className="absolute"
        style={{ top: '10%', left: '28%', width: '8%', height: '14%', background: '#8b4513', border: '3px solid #3d3028' }}
      >
        <div className="absolute inset-1 bg-[#d4a373] flex items-center justify-center text-xs font-bold text-[#5c4033]">
          BOT
        </div>
      </div>

      {/* 海报 - 右侧 */}
      <div
        className="absolute"
        style={{ top: '10%', right: '25%', width: '8%', height: '14%', background: '#8b4513', border: '3px solid #3d3028' }}
      >
        <div className="absolute inset-1 bg-[#e9c46a] flex items-center justify-center text-lg">⚡</div>
      </div>

      {/* 书架 - 左侧靠墙 */}
      <div
        className="absolute"
        style={{ left: '3%', bottom: '42%', width: '10%', height: '14%', background: '#6b4423', border: '3px solid #3d3028' }}
      >
        <div className="absolute top-1/3 left-0 right-0 h-0.5 bg-[#3d3028]" />
        <div className="absolute top-2/3 left-0 right-0 h-0.5 bg-[#3d3028]" />
      </div>
      <PixelFurniture emoji="📚" x="5%" y="52%" size="2.2rem" z={20} />

      {/* 沙发 - 休息区 */}
      <div
        className="absolute"
        style={{
          right: '8%',
          bottom: '38%',
          width: '16%',
          height: '12%',
          background: '#8b6914',
          border: '3px solid #3d3028',
          borderRadius: '4px 4px 0 0',
        }}
      >
        <div
          className="absolute -top-3 left-1 right-1 h-3 bg-[#a67c00] border-2 border-[#3d3028]"
          style={{ borderRadius: '3px 3px 0 0' }}
        />
      </div>
      <PixelFurniture emoji="🛋️" x="78%" y="58%" size="2rem" z={30} />

      {/* 咖啡机 */}
      <div
        className="absolute"
        style={{ right: '28%', bottom: '42%', width: '8%', height: '10%', background: '#4a4a4a', border: '3px solid #3d3028' }}
      >
        <div className="absolute top-1 left-1 right-1 h-2 bg-[#2d2d2d]" />
        <div className="absolute bottom-1 left-1/2 -translate-x-1/2 w-2 h-3 bg-[#87ceeb]" />
      </div>
      <PixelFurniture emoji="☕" x="72%" y="54%" size="1.5rem" z={35} />

      {/* 服务器机柜 - 右侧（忙碌度可视化） */}
      <div
        className="absolute"
        style={{ right: '3%', bottom: '50%', width: '10%', height: '22%', background: '#2d3748', border: '3px solid #1a202c' }}
      >
        <div className="absolute top-1 left-1 right-1 space-y-1">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex gap-1">
              <div
                className="w-1.5 h-1.5 bg-[#22c55e]"
                style={{ animation: `pixelPulse ${pulseSpeed} steps(2) infinite`, animationDelay: `${i * 0.15}s` }}
              />
              <div
                className="w-1.5 h-1.5 bg-[#3b82f6]"
                style={{ animation: `pixelPulse ${pulseSpeed} steps(2) infinite`, animationDelay: `${i * 0.2 + 0.1}s` }}
              />
              <div
                className="w-1.5 h-1.5 bg-[#a855f7]"
                style={{ animation: `pixelPulse ${pulseSpeed} steps(2) infinite`, animationDelay: `${i * 0.25 + 0.05}s` }}
              />
            </div>
          ))}
        </div>
        {/* 忙碌度指示 */}
        {activeCount > 0 && (
          <div className="absolute -top-5 left-0 right-0 text-center">
            <span
              className="text-[9px] font-bold px-1 py-0.5"
              style={{ background: '#e94560', color: '#fff', border: '1px solid #ffd700' }}
            >
              LOAD {Math.min(activeCount * 25, 100)}%
            </span>
          </div>
        )}
        {/* 收尾中指示 */}
        {hasFinishing && activeCount === 0 && (
          <div className="absolute -top-5 left-0 right-0 text-center">
            <span
              className="text-[9px] font-bold px-1 py-0.5"
              style={{ background: '#22c55e', color: '#fff', border: '1px solid #ffd700' }}
            >
              ✅ 收尾中
            </span>
          </div>
        )}
      </div>

      {/* 主办公桌 */}
      <div
        className="absolute"
        style={{ left: '32%', bottom: '35%', width: '28%', height: '14%', background: '#8b6914', border: '3px solid #3d3028' }}
      >
        <PixelFurniture emoji="🖥️" x="10%" y="-40%" size="2rem" z={40} />
        <PixelFurniture emoji="⌨️" x="40%" y="10%" size="1.2rem" z={45} />
        <PixelFurniture emoji="🖱️" x="65%" y="20%" size="1rem" z={45} />
        <PixelFurniture emoji="🌵" x="80%" y="-30%" size="1.5rem" z={50} />
      </div>

      {/* 椅子 */}
      <div
        className="absolute"
        style={{ left: '42%', bottom: '28%', width: '8%', height: '8%', background: '#4a5568', border: '3px solid #3d3028' }}
      />

      {/* 小猫 */}
      <PixelFurniture emoji="🐱" x="18%" y="75%" size="1.8rem" z={60} />

      {/* Worker 工位栏 */}
      <WorkerStations workers={workers} />

      {/* 小助手 NPC */}
      <MiniNPC activeTasks={activeTasks} finishingTasks={finishingTasks} />

      {/* 主 Bot 角色 */}
      <PixelCharacter
        activity={activity}
        currentTask={currentTask}
        taskCount={taskCount}
        isFinishing={hasFinishing && activeCount === 0}
        finishStatus={topFinishing?.resultStatus}
      />

      {/* 底部牌匾 */}
      <div
        className="absolute bottom-2 left-1/2 -translate-x-1/2"
        style={{ background: '#3d3028', border: '3px solid #5c4033', padding: '4px 24px' }}
      >
        <span className="text-[#ffd700] text-sm font-bold tracking-widest">◆ WX-BOT 指挥中心 ◆</span>
      </div>

      {/* 左上角连接状态 */}
      <div className="absolute top-3 left-3 flex items-center gap-2 bg-[#1a1a2e]/80 px-2 py-1 border-2 border-[#3d3028]">
        <div className={`w-2 h-2 ${connected ? 'bg-[#22c55e]' : 'bg-[#e94560]'} pixel-pulse`} />
        <span className="text-[10px] text-[#e2e8f0] font-bold">{connected ? '在线' : '离线'}</span>
      </div>

      {/* 右上角活动状态 */}
      <div className="absolute top-3 right-3 flex items-center gap-2 bg-[#1a1a2e]/80 px-2 py-1 border-2 border-[#3d3028]">
        <ActivityDot activity={activity} hasFinishing={hasFinishing} />
        <span className="text-[10px] text-[#e2e8f0] font-bold">{activityLabel(activity, hasFinishing)}</span>
      </div>
    </div>
  );
}

function WorkerStations({ workers }: { workers: WorkerState[] }) {
  if (workers.length === 0) return null;

  // 均匀分布在底部
  const slotWidth = Math.min(18, 90 / workers.length);
  const startX = (100 - slotWidth * workers.length) / 2;

  return (
    <>
      {/* 工位区底板 */}
      <div
        className="absolute"
        style={{
          left: `${startX - 2}%`,
          bottom: '12%',
          width: `${slotWidth * workers.length + 4}%`,
          height: '22%',
          background: '#1a1a2e',
          border: '3px solid #3d3028',
          opacity: 0.85,
          zIndex: 25,
        }}
      />
      {/* Worker 工位标签 */}
      <div
        className="absolute"
        style={{
          left: `${startX - 2}%`,
          bottom: '35%',
          zIndex: 26,
          background: '#3d3028',
          padding: '1px 6px',
        }}
      >
        <span className="text-[8px] font-bold text-[#ffd700]">WORKERS</span>
      </div>
      {workers.map((worker, i) => {
        const x = startX + i * slotWidth + slotWidth / 2;
        const isIdle = worker.status === 'idle';
        const isRunning = worker.status === 'running';
        const isSuccess = worker.status === 'success';

        const statusColor = isIdle
          ? '#64748b'
          : isRunning
          ? '#3b82f6'
          : isSuccess
          ? '#22c55e'
          : '#e94560';

        const emoji = isIdle ? '😴' : isRunning ? '💻' : isSuccess ? '✅' : '❌';
        const taskName = worker.task
          ? worker.task.handlerName.replace(/TaskHandler|Handler/g, '')
          : '空闲';

        return (
          <div
            key={worker.name}
            className="absolute"
            style={{
              left: `${x}%`,
              bottom: '14%',
              transform: 'translateX(-50%)',
              zIndex: 30 + i,
            }}
          >
            {/* 任务名气泡 */}
            <div
              className="absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap"
              style={{
                background: '#0e1119',
                border: `2px solid ${statusColor}`,
                padding: '1px 5px',
                color: statusColor,
                fontSize: '8px',
                fontWeight: 'bold',
              }}
            >
              {worker.name.replace('worker-', 'W')}: {taskName}
              {worker.task?.progress && (
                <span className="ml-1 opacity-70">{worker.task.progress}</span>
              )}
              <div
                className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rotate-45"
                style={{
                  background: '#0e1119',
                  borderRight: `2px solid ${statusColor}`,
                  borderBottom: `2px solid ${statusColor}`,
                }}
              />
            </div>
            {/* Worker 表情 */}
            <div
              className="text-xl"
              style={{
                filter: `drop-shadow(2px 2px 0 ${statusColor}40)`,
                animation: isRunning ? `bounceMini ${1 + i * 0.2}s ease-in-out infinite` : undefined,
              }}
            >
              {emoji}
            </div>
            {/* 状态灯 */}
            <div className="flex justify-center mt-0.5">
              <div
                className="w-1.5 h-1.5 rounded-full"
                style={{
                  background: statusColor,
                  animation: isRunning ? `pixelPulse 0.8s steps(2) infinite` : undefined,
                }}
              />
            </div>
          </div>
        );
      })}
    </>
  );
}

function PixelFurniture({ emoji, x, y, size = '1.5rem', z = 10 }: { emoji: string; x: string; y: string; size?: string; z?: number }) {
  return (
    <div
      className="absolute"
      style={{ left: x, top: y, fontSize: size, zIndex: z, filter: 'drop-shadow(2px 2px 0 rgba(0,0,0,0.3))' }}
    >
      {emoji}
    </div>
  );
}

function ActivityDot({ activity, hasFinishing }: { activity: BotActivity; hasFinishing?: boolean }) {
  if (hasFinishing && activity === 'idle') {
    return <div className="w-2 h-2 pixel-pulse" style={{ backgroundColor: '#22c55e' }} />;
  }
  const color =
    activity === 'idle' ? '#94a3b8' :
    activity === 'error' ? '#e94560' :
    activity === 'syncing' ? '#22c55e' :
    activity === 'researching' ? '#a855f7' :
    activity === 'executing' ? '#f59e0b' :
    '#3b82f6';
  return <div className="w-2 h-2 pixel-pulse" style={{ backgroundColor: color }} />;
}

function activityLabel(a: BotActivity, hasFinishing?: boolean) {
  if (hasFinishing && a === 'idle') return '收尾中';
  const map: Record<string, string> = {
    idle: '待命', working: '工作中', writing: '撰写中',
    researching: '调研中', executing: '执行中', syncing: '同步中', error: '离线',
  };
  return map[a] || a;
}
