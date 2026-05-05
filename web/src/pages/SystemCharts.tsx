import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Activity, Cpu, MemoryStick } from 'lucide-react';
import { PixelCard } from '../components/PixelCard';
import { useMetricsHistory } from '../hooks/useMetricsHistory';

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export function SystemCharts() {
  const { history, loading, error } = useMetricsHistory(3000);
  const latest = history[history.length - 1];

  return (
    <div className="space-y-6">
      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          icon={<Cpu className="w-5 h-5 text-[#3b82f6]" />}
          label="CPU 使用率"
          value={latest ? `${latest.cpu.toFixed(1)}%` : '--'}
          sub={latest ? `${Math.round(history.reduce((a, b) => a + b.cpu, 0) / history.length || 0)}% 平均` : ''}
          color="blue"
        />
        <StatCard
          icon={<MemoryStick className="w-5 h-5 text-[#a855f7]" />}
          label="内存使用率"
          value={latest ? `${latest.memory.toFixed(1)}%` : '--'}
          sub={latest ? `${formatBytes(latest.memoryUsed)} / ${formatBytes(latest.memoryTotal)}` : ''}
          color="purple"
        />
        <StatCard
          icon={<Activity className="w-5 h-5 text-[#22c55e]" />}
          label="采样点"
          value={`${history.length}`}
          sub="最近 60 个数据点"
          color="green"
        />
      </div>

      {error && (
        <div className="p-4 bg-[#e94560]/10 border-2 border-[#e94560]/20 text-sm text-[#e94560]">
          {error}
        </div>
      )}

      <PixelCard title="CPU & 内存趋势" titleIcon={<Activity className="w-4 h-4" />}>
        {loading && history.length === 0 ? (
          <div className="h-80 flex items-center justify-center text-[#64748b]">加载中...</div>
        ) : history.length < 2 ? (
          <div className="h-80 flex items-center justify-center text-[#64748b]">
            正在收集数据，请稍候...
          </div>
        ) : (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorMem" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="time"
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  tickLine={false}
                  axisLine={{ stroke: '#334155' }}
                  minTickGap={30}
                />
                <YAxis
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  tickLine={false}
                  axisLine={{ stroke: '#334155' }}
                  domain={[0, 100]}
                  unit="%"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#141722',
                    border: '2px solid #0e1119',
                    color: '#e2e8f0',
                  }}
                />
                <Legend wrapperStyle={{ color: '#94a3b8' }} />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  name="CPU %"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorCpu)"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  name="内存 %"
                  stroke="#a855f7"
                  fillOpacity={1}
                  fill="url(#colorMem)"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </PixelCard>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
  color: 'blue' | 'purple' | 'green';
}) {
  const borderColor =
    color === 'blue'
      ? 'border-[#3b82f6]/20'
      : color === 'purple'
      ? 'border-[#a855f7]/20'
      : 'border-[#22c55e]/20';
  return (
    <div className={`bg-[#141722] border-2 ${borderColor} p-4`} style={{ boxShadow: '4px 4px 0 rgba(0,0,0,0.2)' }}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs text-[#94a3b8] font-bold">{label}</span>
      </div>
      <div className="text-2xl font-bold text-[#e2e8f0]">{value}</div>
      <div className="text-xs text-[#64748b] mt-1">{sub}</div>
    </div>
  );
}
