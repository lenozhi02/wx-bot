import { useEffect, useState } from 'react';
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
} from 'lucide-react';
import { api } from '../services/api';
import { PixelCard } from '../components/PixelCard';
import { PixelBadge } from '../components/PixelBadge';

interface HandlerInfo {
  name: string;
  description: string;
  icon: React.ReactNode;
  tags: string[];
}

const handlerMeta: Record<string, Partial<HandlerInfo>> = {
  HelpTaskHandler: {
    description: '帮助指令处理器，响应 "help" / "帮助" 等关键词，列出所有可用命令。',
    icon: <HelpCircle className="w-5 h-5 text-[#f59e0b]" />,
    tags: ['内置', '指令'],
  },
  StatusTaskHandler: {
    description: '服务器状态巡检，响应 "status" 指令，返回 CPU、内存、磁盘等系统信息。',
    icon: <Cpu className="w-5 h-5 text-[#3b82f6]" />,
    tags: ['内置', '系统'],
  },
  LongRunningTaskHandler: {
    description: '后台长时间任务示例，响应 "长任务" / "longtask" 指令，演示异步执行能力。',
    icon: <Zap className="w-5 h-5 text-[#f59e0b]" />,
    tags: ['示例', '后台任务'],
  },
  DataSyncTaskHandler: {
    description: '数据同步任务示例，响应 "同步" / "sync" 指令。',
    icon: <Globe className="w-5 h-5 text-[#a855f7]" />,
    tags: ['示例', '后台任务'],
  },
  BaiduSearchTaskHandler: {
    description: '百度搜索报告生成器，支持按机构名和日期检索新闻并生成 PDF 报告。',
    icon: <Search className="w-5 h-5 text-[#3b82f6]" />,
    tags: ['搜索', '报告'],
  },
  SearchTaskHandler: {
    description: '通用网络搜索处理器，响应 "搜索 <关键词>" 指令。',
    icon: <Search className="w-5 h-5 text-[#22c55e]" />,
    tags: ['搜索'],
  },
  AITaskHandler: {
    description: 'AI 对话兜底处理器，当没有其他处理器匹配时自动调用 AI 回复用户消息。',
    icon: <Bot className="w-5 h-5 text-[#22c55e]" />,
    tags: ['AI', '兜底'],
  },
};

export function PluginHub() {
  const [handlers, setHandlers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api
      .botHandlers()
      .then((res) => {
        setHandlers(res.handlers);
        if (res.handlers.length > 0) {
          setExpanded({ [res.handlers[0]]: true });
        }
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const toggle = (name: string) => {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Puzzle className="w-5 h-5 text-[#a855f7]" />
        <div>
          <h2 className="text-base font-bold text-[#ffd700] pixel-title">插件中心</h2>
          <p className="text-xs text-[#64748b]">已注册的消息处理器与扩展模块</p>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-[#e94560]/10 border-2 border-[#e94560]/20 text-sm text-[#e94560]">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-[#64748b] text-sm">加载中...</div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {handlers.map((name) => {
            const meta = handlerMeta[name] || {};
            const isExpanded = expanded[name];
            return (
              <PixelCard key={name} noCorners className="p-0 overflow-hidden">
                <button
                  onClick={() => toggle(name)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-[#1a1b2f] transition-colors"
                >
                  <div className="w-10 h-10 bg-[#0e1119] border-2 border-[#1f2937] flex items-center justify-center shrink-0">
                    {meta.icon || <MessageSquare className="w-5 h-5 text-[#64748b]" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold text-[#e2e8f0] truncate">{name}</div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {(meta.tags || ['扩展']).map((tag) => (
                        <PixelBadge key={tag} color="slate">{tag}</PixelBadge>
                      ))}
                    </div>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-[#64748b] shrink-0" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-[#64748b] shrink-0" />
                  )}
                </button>
                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 border-t-2 border-[#0e1119]">
                    <p className="text-sm text-[#94a3b8] leading-relaxed">
                      {meta.description || '暂无描述'}
                    </p>
                  </div>
                )}
              </PixelCard>
            );
          })}
        </div>
      )}

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
            desc="注册自定义 Python 脚本作为消息处理器。"
            icon={<Puzzle className="w-5 h-5 text-[#3b82f6]" />}
            status="规划中"
          />
        </div>
      </div>
    </div>
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
