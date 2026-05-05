import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Rocket,
  BarChart3,
  Puzzle,
  Menu,
  X,
  Activity,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useWS } from '../contexts/WebSocketContext';

const NAV = [
  { path: '/', label: '总览', icon: LayoutDashboard },
  { path: '/tasks', label: '任务中心', icon: Rocket },
  { path: '/charts', label: '系统监控', icon: BarChart3 },
  { path: '/plugins', label: '插件中心', icon: Puzzle },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { connected, latency } = useWS();

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-[#1a1a2e] text-[#e2e8f0] flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50 w-56
          bg-[#141722] border-r-[3px] border-[#0e1119]
          transform transition-transform duration-200 ease-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          flex flex-col
        `}
        style={{ boxShadow: '4px 0 0 rgba(0,0,0,0.3)' }}
      >
        <div className="h-14 flex items-center px-4 border-b-[3px] border-[#0e1119]">
          <div className="w-8 h-8 border-2 border-[#ffd700] bg-[#0e1119] flex items-center justify-center mr-3">
            <Activity className="w-4 h-4 text-[#ffd700]" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-[#ffd700] tracking-wider">WX-BOT</h1>
            <p className="text-[10px] text-[#64748b]">指挥中心</p>
          </div>
          <button
            className="ml-auto lg:hidden p-1 text-[#94a3b8] hover:text-[#e2e8f0]"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {NAV.map((item) => {
            const active = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center gap-3 px-3 py-2.5 text-sm transition-colors border-2
                  ${active
                    ? 'bg-[#ffd700]/10 text-[#ffd700] border-[#ffd700]/40'
                    : 'text-[#94a3b8] border-transparent hover:bg-[#1a1b2f] hover:text-[#e2e8f0] hover:border-[#1f2937]'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                <span className="tracking-wide">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t-[3px] border-[#0e1119]">
          <div className="flex items-center gap-2 text-xs">
            {connected ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-[#22c55e]" />
                <span className="text-[#22c55e] font-bold">已连接</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-[#e94560]" />
                <span className="text-[#e94560] font-bold">已断开</span>
              </>
            )}
            {connected && latency > 0 && (
              <span className="ml-auto text-[#64748b]">{latency}ms</span>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header
          className="h-14 border-b-[3px] border-[#0e1119] bg-[#141722] flex items-center px-4 sticky top-0 z-30"
          style={{ boxShadow: '0 4px 0 rgba(0,0,0,0.2)' }}
        >
          <button
            className="lg:hidden p-2 -ml-2 mr-2 text-[#94a3b8] hover:text-[#e2e8f0]"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="text-sm font-bold text-[#ffd700] tracking-wide pixel-title">
            {NAV.find((n) => n.path === location.pathname)?.label || '总览'}
          </div>
          <div className="ml-auto text-xs text-[#64748b]">
            WX-BOT v1.0
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
