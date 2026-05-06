import { useEffect, useState, useCallback } from 'react';
import {
  Puzzle,
  Zap,
  Search,
  MessageSquare,
  Globe,
  Cpu,
  Bot,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  PowerOff,
  RotateCcw,
  Loader2,
} from 'lucide-react';
import { api, type PluginInfo } from '../services/api';
import { PixelCard } from '../components/PixelCard';
import { PixelBadge } from '../components/PixelBadge';

interface HandlerInfo {
  name: string;
  description: string;
  icon: React.ReactNode;
  tags: string[];
}

const handlerMeta: Record<string, Partial<HandlerInfo>> = {
  help: {
    description: '帮助指令处理器，响应 "help" / "帮助" 等关键词，列出所有可用命令。',
    icon: <HelpCircle className="w-5 h-5 text-[#f59e0b]" />,
    tags: ['内置', '指令'],
  },
  status: {
    description: '服务器状态巡检，响应 "status" 指令，返回 CPU、内存、磁盘等系统信息。',
    icon: <Cpu className="w-5 h-5 text-[#3b82f6]" />,
    tags: ['内置', '系统'],
  },
  longtask: {
    description: '后台长时间任务示例，响应 "长任务" / "longtask" 指令，演示异步执行能力。',
    icon: <Zap className="w-5 h-5 text-[#f59e0b]" />,
    tags: ['示例', '后台任务'],
  },
  sync: {
    description: '数据同步任务示例，响应 "同步" / "sync" 指令。',
    icon: <Globe className="w-5 h-5 text-[#a855f7]" />,
    tags: ['示例', '后台任务'],
  },
  baidu_search: {
    description: '百度搜索报告生成器，支持按机构名和日期检索新闻并生成 PDF 报告。',
    icon: <Search className="w-5 h-5 text-[#3b82f6]" />,
    tags: ['搜索', '报告'],
  },
  search: {
    description: '通用网络搜索处理器，响应 "搜索 <关键词>" 指令。',
    icon: <Search className="w-5 h-5 text-[#22c55e]" />,
    tags: ['搜索'],
  },
  ai: {
    description: 'AI 对话兜底处理器，当没有其他处理器匹配时自动调用 AI 回复用户消息。',
    icon: <Bot className="w-5 h-5 text-[#22c55e]" />,
    tags: ['AI', '兜底'],
  },
  echo: {
    description: '回声插件 — 复读用户消息。',
    icon: <MessageSquare className="w-5 h-5 text-[#e94560]" />,
    tags: ['插件', '示例'],
  },
  reminder: {
    description: '提醒插件 — 异步定时提醒示例。',
    icon: <Zap className="w-5 h-5 text-[#a855f7]" />,
    tags: ['插件', '后台任务'],
  },
};

export function PluginHub() {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [handlers, setHandlers] = useState<{ name: string; priority: number; description: string; type: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [reloadAllLoading, setReloadAllLoading] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [pRes, hRes] = await Promise.all([api.plugins(), api.allHandlers()]);
      setPlugins(pRes.plugins);
      setHandlers(hRes.handlers);
      if (pRes.plugins.length > 0 && Object.keys(expanded).length === 0) {
        setExpanded({ [pRes.plugins[0].id]: true });
      }
    } catch (e) {
      setError(String(e));
    }
  }, [expanded]);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  const toggle = (name: string) => {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const withLoading = async (key: string, fn: () => Promise<unknown>) => {
    setActionLoading((prev) => ({ ...prev, [key]: true }));
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setActionLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  const handleUnload = (id: string) => withLoading(`unload-${id}`, () => api.unloadPlugin(id).then(() => {}));
  const handleReload = (id: string) => withLoading(`reload-${id}`, () => api.reloadPlugin(id).then(() => {}));
  const handleReloadAll = async () => {
    setReloadAllLoading(true);
    try {
      await api.reloadPlugins();
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setReloadAllLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Puzzle className="w-5 h-5 text-[#a855f7]" />
          <div>
            <h2 className="text-base font-bold text-[#ffd700] pixel-title">插件中心</h2>
            <p className="text-xs text-[#64748b]">动态加载 / 卸载插件，不重启服务</p>
          </div>
        </div>
        <button
          onClick={handleReloadAll}
          disabled={reloadAllLoading}
          className="flex items-center gap-2 px-3 py-2 text-xs font-bold text-[#22c55e] border-2 border-[#22c55e]/30 hover:bg-[#22c55e]/10 transition-colors disabled:opacity-50"
        >
          {reloadAllLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          重载全部
        </button>
      </div>

      {error && (
        <div className="p-3 bg-[#e94560]/10 border-2 border-[#e94560]/20 text-sm text-[#e94560]">
          {error}
        </div>
      )}

      {/* 插件列表 */}
      <div>
        <h3 className="text-sm font-bold text-[#94a3b8] mb-2 pixel-title">已加载插件</h3>
        {loading ? (
          <div className="text-[#64748b] text-sm">加载中...</div>
        ) : plugins.length === 0 ? (
          <div className="text-[#64748b] text-sm">暂无加载的插件</div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {plugins.map((plugin) => {
              const isExpanded = expanded[plugin.id];
              return (
                <PixelCard key={plugin.id} noCorners className="p-0 overflow-hidden">
                  <button
                    onClick={() => toggle(plugin.id)}
                    className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-[#1a1b2f] transition-colors"
                  >
                    <div className="w-10 h-10 bg-[#0e1119] border-2 border-[#1f2937] flex items-center justify-center shrink-0">
                      <Puzzle className="w-5 h-5 text-[#a855f7]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-bold text-[#e2e8f0] truncate">
                        {plugin.name}
                        <span className="ml-2 text-xs text-[#64748b]">v{plugin.version}</span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        <PixelBadge color="purple">插件</PixelBadge>
                        <PixelBadge color="slate">优先级 {plugin.priority}</PixelBadge>
                        <PixelBadge color="green">{plugin.status}</PixelBadge>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-[#64748b] shrink-0" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-[#64748b] shrink-0" />
                    )}
                  </button>
                  {isExpanded && (
                    <div className="px-4 pb-4 pt-1 border-t-2 border-[#0e1119] space-y-3">
                      <p className="text-sm text-[#94a3b8] leading-relaxed">
                        {plugin.description || '暂无描述'}
                      </p>
                      <div className="text-xs text-[#64748b]">
                        作者: {plugin.author || '未知'} · 类: {plugin.handler_class}
                      </div>
                      <div className="flex gap-2">
                        <ActionBtn
                          icon={<RotateCcw className="w-3.5 h-3.5" />}
                          label="重载"
                          loading={actionLoading[`reload-${plugin.id}`]}
                          onClick={(e) => { e.stopPropagation(); handleReload(plugin.id); }}
                          color="blue"
                        />
                        <ActionBtn
                          icon={<PowerOff className="w-3.5 h-3.5" />}
                          label="卸载"
                          loading={actionLoading[`unload-${plugin.id}`]}
                          onClick={(e) => { e.stopPropagation(); handleUnload(plugin.id); }}
                          color="red"
                        />
                      </div>
                    </div>
                  )}
                </PixelCard>
              );
            })}
          </div>
        )}
      </div>

      {/* 所有处理器 */}
      <div>
        <h3 className="text-sm font-bold text-[#94a3b8] mb-2 pixel-title">全部处理器 ({handlers.length})</h3>
        <div className="grid grid-cols-1 gap-3">
          {handlers.map((h) => {
            const meta = handlerMeta[h.name] || {};
            return (
              <div
                key={h.name}
                className="flex items-center gap-3 px-4 py-3 bg-[#141722]/50 border-2 border-[#0e1119]"
                style={{ boxShadow: '2px 2px 0 rgba(0,0,0,0.2)' }}
              >
                <div className="w-10 h-10 bg-[#0e1119] border-2 border-[#1f2937] flex items-center justify-center shrink-0">
                  {meta.icon || <MessageSquare className="w-5 h-5 text-[#64748b]" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-bold text-[#e2e8f0] truncate">{h.name}</div>
                  <div className="text-xs text-[#64748b] truncate">{h.description || meta.description || '暂无描述'}</div>
                </div>
                <div className="flex flex-wrap gap-1 shrink-0">
                  <PixelBadge color="slate">P{h.priority}</PixelBadge>
                  <PixelBadge color={h.type === 'background' ? 'amber' : 'blue'}>{h.type}</PixelBadge>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 扩展面板 */}
      <div className="pt-4 border-t-2 border-[#0e1119]">
        <h3 className="text-sm font-bold text-[#e2e8f0] mb-3 pixel-title">扩展面板</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <ExtensionCard
            title="Webhook 日志"
            desc="查看最近收到的 Webhook 请求和推送记录。"
            icon={<Globe className="w-5 h-5 text-[#a855f7]" />}
            status="即将推出"
          />
          <ExtensionCard
            title="事件历史"
            desc="浏览和搜索事件总线中的历史事件记录。"
            icon={<Zap className="w-5 h-5 text-[#f59e0b]" />}
            status="即将推出"
          />
          <ExtensionCard
            title="自定义脚本"
            desc="在 plugins/ 目录创建 manifest.json + handler.py 即可自动识别。"
            icon={<Puzzle className="w-5 h-5 text-[#22c55e]" />}
            status="已支持"
          />
        </div>
      </div>
    </div>
  );
}

function ActionBtn({
  icon,
  label,
  loading,
  onClick,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  loading: boolean;
  onClick: (e: React.MouseEvent) => void;
  color: 'blue' | 'red' | 'green';
}) {
  const colorMap = {
    blue: 'text-[#3b82f6] border-[#3b82f6]/30 hover:bg-[#3b82f6]/10',
    red: 'text-[#e94560] border-[#e94560]/30 hover:bg-[#e94560]/10',
    green: 'text-[#22c55e] border-[#22c55e]/30 hover:bg-[#22c55e]/10',
  };
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`flex items-center gap-1 px-2.5 py-1.5 text-xs font-bold border-2 transition-colors disabled:opacity-50 ${colorMap[color]}`}
    >
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : icon}
      {label}
    </button>
  );
}

function ExtensionCard({
  title,
  desc,
  icon,
  status,
}: {
  title: string;
  desc: string;
  icon: React.ReactNode;
  status: string;
}) {
  return (
    <div
      className="bg-[#141722]/50 border-2 border-[#0e1119] p-4 opacity-60 hover:opacity-100 transition-opacity"
      style={{ boxShadow: '2px 2px 0 rgba(0,0,0,0.2)' }}
    >
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm font-bold text-[#94a3b8]">{title}</span>
      </div>
      <p className="text-xs text-[#64748b] mb-3 leading-relaxed">{desc}</p>
      <PixelBadge color="slate">{status}</PixelBadge>
    </div>
  );
}
