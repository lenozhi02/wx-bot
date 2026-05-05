import { useEffect, useState, useMemo } from 'react';
import {
  CheckCircle,
  XCircle,
  Loader2,
  Clock,
  Search,
  Filter,
  X,
  ChevronRight,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { PixelCard } from '../components/PixelCard';
import { PixelBadge } from '../components/PixelBadge';
import type { TaskInfo } from '../types';

type StatusFilter = 'all' | 'running' | 'completed' | 'failed' | 'pending';

const statusMeta: Record<string, { label: string; color: 'green' | 'red' | 'amber' | 'slate'; icon: React.ReactNode }> = {
  running: { label: '运行中', color: 'amber', icon: <Loader2 className="w-3.5 h-3.5 animate-spin" /> },
  completed: { label: '已完成', color: 'green', icon: <CheckCircle className="w-3.5 h-3.5" /> },
  failed: { label: '失败', color: 'red', icon: <XCircle className="w-3.5 h-3.5" /> },
  pending: { label: '等待中', color: 'slate', icon: <Clock className="w-3.5 h-3.5" /> },
};

export function MissionControl() {
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [search, setSearch] = useState('');
  const [selectedTask, setSelectedTask] = useState<TaskInfo | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      const res = await api.tasks({ limit: 100 });
      setTasks(res.tasks);
      setError('');
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, []);

  const filtered = useMemo(() => {
    let list = tasks;
    if (filter !== 'all') {
      list = list.filter((t) => t.status === filter);
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (t) =>
          t.handler_name.toLowerCase().includes(q) ||
          t.task_id.toLowerCase().includes(q) ||
          t.user_id.toLowerCase().includes(q)
      );
    }
    return list;
  }, [tasks, filter, search]);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: tasks.length };
    tasks.forEach((t) => {
      c[t.status] = (c[t.status] || 0) + 1;
    });
    return c;
  }, [tasks]);

  const filters: { key: StatusFilter; label: string }[] = [
    { key: 'all', label: `全部 (${counts.all || 0})` },
    { key: 'running', label: `运行中 (${counts.running || 0})` },
    { key: 'pending', label: `等待中 (${counts.pending || 0})` },
    { key: 'completed', label: `已完成 (${counts.completed || 0})` },
    { key: 'failed', label: `失败 (${counts.failed || 0})` },
  ];

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#64748b]" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索任务 ID、处理器、用户..."
            className="w-full pl-9 pr-4 py-2 bg-[#141722] border-2 border-[#0e1119] text-sm text-[#e2e8f0] placeholder:text-[#475569] focus:outline-none focus:border-[#ffd700]/40"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#64748b] hover:text-[#e2e8f0]"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        <button
          onClick={load}
          className="px-4 py-2 bg-[#141722] border-2 border-[#0e1119] text-sm text-[#94a3b8] hover:text-[#ffd700] hover:border-[#ffd700]/40 transition-colors font-bold tracking-wide"
          style={{ boxShadow: '2px 2px 0 rgba(0,0,0,0.3)' }}
        >
          刷新
        </button>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2">
        <Filter className="w-4 h-4 text-[#64748b] mt-1" />
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`
              px-3 py-1 text-xs border-2 transition-colors font-bold tracking-wide
              ${filter === f.key
                ? 'bg-[#ffd700]/10 text-[#ffd700] border-[#ffd700]/40'
                : 'bg-[#141722] border-[#0e1119] text-[#94a3b8] hover:border-[#1f2937]'
              }
            `}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-[#e94560]/10 border-2 border-[#e94560]/20 text-sm text-[#e94560]">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* Task list */}
      <PixelCard noCorners className="overflow-hidden">
        <div className="overflow-x-auto -mx-4 -mt-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-[#0e1119] text-[#64748b]">
                <th className="text-left px-4 py-3 font-bold">状态</th>
                <th className="text-left px-4 py-3 font-bold">处理器</th>
                <th className="text-left px-4 py-3 font-bold hidden md:table-cell">任务 ID</th>
                <th className="text-left px-4 py-3 font-bold hidden lg:table-cell">用户</th>
                <th className="text-left px-4 py-3 font-bold hidden sm:table-cell">进度</th>
                <th className="text-left px-4 py-3 font-bold">创建时间</th>
                <th className="px-4 py-3 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {loading && tasks.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-[#64748b]">
                    加载中...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-[#64748b]">
                    没有匹配的任务
                  </td>
                </tr>
              ) : (
                filtered.map((task) => {
                  const meta = statusMeta[task.status] || statusMeta.pending;
                  return (
                    <tr
                      key={task.task_id}
                      className="border-b border-[#0e1119] hover:bg-[#1a1b2f] transition-colors cursor-pointer"
                      onClick={() => setSelectedTask(task)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          {meta.icon}
                          <PixelBadge color={meta.color}>{meta.label}</PixelBadge>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-[#e2e8f0] font-bold">{task.handler_name}</td>
                      <td className="px-4 py-3 text-[#64748b] font-mono hidden md:table-cell">
                        {task.task_id.slice(-8)}
                      </td>
                      <td className="px-4 py-3 text-[#64748b] hidden lg:table-cell">{task.user_id}</td>
                      <td className="px-4 py-3 hidden sm:table-cell">
                        {task.progress ? (
                          <div className="w-24 bg-[#0e1119] h-2 border border-[#1f2937]">
                            <div
                              className="h-full bg-[#3b82f6]"
                              style={{ width: `${Math.min(parseFloat(task.progress) || 0, 100)}%` }}
                            />
                          </div>
                        ) : (
                          <span className="text-[#475569]">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-[#64748b] whitespace-nowrap font-mono text-xs">
                        {new Date(task.created_at * 1000).toLocaleString('zh-CN')}
                      </td>
                      <td className="px-4 py-3">
                        <ChevronRight className="w-4 h-4 text-[#475569]" />
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </PixelCard>

      {/* Task detail drawer */}
      {selectedTask && (
        <div
          className="fixed inset-0 bg-black/60 z-50 flex justify-end"
          onClick={() => setSelectedTask(null)}
        >
          <div
            className="w-full max-w-md bg-[#141722] border-l-[3px] border-[#0e1119] h-full overflow-y-auto p-6 space-y-4 animate-slideInRight"
            style={{ boxShadow: '-4px 0 0 rgba(0,0,0,0.3)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b-2 border-[#0e1119] pb-3">
              <h2 className="text-lg font-bold text-[#ffd700] pixel-title">任务详情</h2>
              <button
                onClick={() => setSelectedTask(null)}
                className="p-1 text-[#94a3b8] hover:text-[#e2e8f0]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <DetailRow label="任务 ID" value={selectedTask.task_id} mono />
            <DetailRow label="处理器" value={selectedTask.handler_name} />
            <DetailRow label="用户" value={selectedTask.user_id} />
            <DetailRow label="状态" value={selectedTask.status} />
            <DetailRow label="进度" value={selectedTask.progress || '-'} />
            <DetailRow
              label="创建时间"
              value={new Date(selectedTask.created_at * 1000).toLocaleString('zh-CN')}
            />
            {selectedTask.started_at && (
              <DetailRow
                label="开始时间"
                value={new Date(selectedTask.started_at * 1000).toLocaleString('zh-CN')}
              />
            )}
            {selectedTask.finished_at && (
              <DetailRow
                label="结束时间"
                value={new Date(selectedTask.finished_at * 1000).toLocaleString('zh-CN')}
              />
            )}
            {selectedTask.duration !== undefined && selectedTask.duration > 0 && (
              <DetailRow label="耗时" value={`${selectedTask.duration.toFixed(2)}s`} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function DetailRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="py-2 border-b border-[#0e1119]">
      <div className="text-xs text-[#64748b] mb-1 font-bold">{label}</div>
      <div className={`text-sm text-[#e2e8f0] ${mono ? 'font-mono' : ''}`}>{value}</div>
    </div>
  );
}
