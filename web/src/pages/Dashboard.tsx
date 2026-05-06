import { useWS } from '../contexts/WebSocketContext';
import { PixelRoom } from '../components/pixel-room/PixelRoom';
import { EventStream } from '../components/EventStream';
import { MetricsPanel } from '../components/MetricsPanel';
import { BotStatusCard } from '../components/BotStatusCard';

export function Dashboard() {
  const { connected, events, activity, currentTask, activeTasks, finishingTasks, taskCount, workers } = useWS();

  // 底部显示的任务状态文字
  const statusText = (() => {
    if (activeTasks.length > 0) {
      const names = activeTasks.map((t) => t.handlerName.replace(/TaskHandler|Handler/g, ''));
      return `执行中: ${names.join(', ')}`;
    }
    if (finishingTasks.length > 0) {
      const names = finishingTasks.map((t) => t.handlerName.replace(/TaskHandler|Handler/g, ''));
      return `收尾中: ${names.join(', ')}`;
    }
    return '无任务';
  })();

  return (
    <div className="space-y-4">
      {/* 像素房间场景 */}
      <div
        className="border-[3px] border-[#3d3028] relative"
        style={{ boxShadow: '4px 4px 0 rgba(0,0,0,0.4)' }}
      >
        <PixelRoom
          activity={activity}
          currentTask={currentTask}
          activeTasks={activeTasks}
          finishingTasks={finishingTasks}
          taskCount={taskCount}
          workers={workers}
        />
      </div>

      {/* 底部三栏面板 - 游戏UI风格 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* 左栏 - 实时事件 */}
        <div
          className="bg-[#141722] border-[3px] border-[#0e1119] relative pixel-corners"
          style={{ boxShadow: '4px 4px 0 rgba(0,0,0,0.3)' }}
        >
          <div className="px-4 py-2 border-b-[3px] border-[#0e1119] text-center">
            <h3 className="text-sm font-bold text-[#ffd700] tracking-widest pixel-title">
              — 实时事件 —
            </h3>
          </div>
          <div className="p-3 h-64 overflow-hidden">
            <EventStream events={events} compact />
          </div>
        </div>

        {/* 中栏 - Bot状态 */}
        <div
          className="bg-[#141722] border-[3px] border-[#0e1119] relative pixel-corners"
          style={{ boxShadow: '4px 4px 0 rgba(0,0,0,0.3)' }}
        >
          <div className="px-4 py-2 border-b-[3px] border-[#0e1119] text-center">
            <h3 className="text-sm font-bold text-[#ffd700] tracking-widest pixel-title">
              — Bot 状态 —
            </h3>
          </div>
          <div className="p-3 h-64 overflow-auto">
            <BotStatusCard compact />
          </div>
        </div>

        {/* 右栏 - 系统状态 */}
        <div
          className="bg-[#141722] border-[3px] border-[#0e1119] relative pixel-corners"
          style={{ boxShadow: '4px 4px 0 rgba(0,0,0,0.3)' }}
        >
          <div className="px-4 py-2 border-b-[3px] border-[#0e1119] text-center">
            <h3 className="text-sm font-bold text-[#ffd700] tracking-widest pixel-title">
              — 系统状态 —
            </h3>
          </div>
          <div className="p-3 h-64 overflow-auto">
            <MetricsPanel compact />
          </div>
        </div>
      </div>

      {/* 底部状态栏 */}
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs text-[#64748b]">
        <span className="flex items-center gap-1">
          <span className={`w-2 h-2 ${connected ? 'bg-[#22c55e]' : 'bg-[#e94560]'} pixel-pulse`} />
          WebSocket {connected ? '已连接' : '已断开'}
        </span>
        <span>·</span>
        <span>{statusText}</span>
        <span>·</span>
        <span>活跃 {activeTasks.length} / 收尾 {finishingTasks.length}</span>
        <span>·</span>
        <span>WX-BOT v1.0</span>
      </div>
    </div>
  );
}
