# WX-BOT Web UI 设计文档

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户浏览器                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Dashboard  │  │   Mission   │  │   System    │  │   Plugin    │ │
│  │   像素房间   │  │   Control   │  │   Charts    │  │    Hub      │ │
│  │   (首页)    │  │  (任务中心)  │  │  (系统监控)  │  │  (插件中心)  │ │
│  └──────┬──────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│         │                                                           │
│  ┌──────┴──────────────────────────────────────────────────────────┐│
│  │                     React 18 + React Router                       ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   ││
│  │  │ WebSocket    │  │   REST API   │  │   Zustand (已移除)   │   ││
│  │  │  Hook        │  │   Service    │  │   → Context 替代     │   ││
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘   ││
│  │         │                 │                                      ││
│  │  ┌──────┴─────────────────┴──────────────────────────────────┐  ││
│  │  │              WebSocketContext (全局状态)                    │  ││
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  ││
│  │  │  │ activity │ │currentTask│ │activeTasks│ │finishingTasks│  │  ││
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │  ││
│  │  └───────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                              ┌──────┴──────┐
                              │  Vite Proxy │
                              │  (dev模式)  │
                              └──────┬──────┘
                                     │
┌────────────────────────────────────┴────────────────────────────────┐
│                           FastAPI 后端 (port 3000)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │/api/health│  │/api/tasks│  │/api/system│  │/api/events│  │/ws   ││
│  │ 健康检查  │  │ 任务管理  │  │ 系统指标  │  │  事件历史  │  │WebSocket│
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────────┘│
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                      StaticFiles (web/dist)                     ││
│  │                     生产环境直接提供前端页面                      ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、像素房间 Dashboard 布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  🟢在线                        ◆ WX-BOT 指挥中心 ◆                🔍调研中 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   🌙 窗户      🖼️海报      🖼️海报                                    │
│                                                                     │
│   ┌─────┐                      💬 [BaiduSearch] +2个排队中           │
│   │📚书架│                     👨‍💻 主角色（办公桌前）                 │
│   └─────┘                                                           │
│                              🖥️ ⌨️ 🖱️ 🌵                           │
│                              ┌─────────────┐                        │
│   🐱 小猫                    │  主办公桌   │      🛋️ 沙发            │
│                              └─────────────┘                        │
│                                                                     │
│   ☕ 咖啡机                    👾 [LongRunning]     LOAD 75%         │
│                                          🐱 [DataSync]   🖥️服务器    │
│                                                                     │
│                              ◆ WX-BOT 指挥中心 ◆                   │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  — 实时事件 —  │  │  — Bot状态 —  │  │  — 系统状态 —  │              │
│  │              │  │              │  │              │              │
│  │ [09:50:12]   │  │ 运行状态     │  │ CPU 15% · 4核 │              │
│  │ bot:message  │  │ ✅ 运行中     │  │ ████░░░░░░   │              │
│  │              │  │              │  │              │              │
│  │ [09:50:13]   │  │ Webhook      │  │ 内存 40%     │              │
│  │ task:started │  │ ✅ 已启用     │  │ ████░░░░░░   │              │
│  │              │  │              │  │              │              │
│  │ [09:50:18]   │  │ 处理器(7)    │  │ 磁盘 91%     │              │
│  │ task:completed│  │ Help Status  │  │ █████████░   │              │
│  │              │  │ BaiduSearch  │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
├─────────────────────────────────────────────────────────────────────┤
│  WebSocket 已连接 · 执行中: BaiduSearch, LongRunning · WX-BOT v1.0  │
└─────────────────────────────────────────────────────────────────────┘
```

### 像素房间元素坐标

```
                    [墙壁区域 - 45%高度]
    🌙窗户(8%,8%)  🖼️海报(28%,10%)  🖼️海报(右25%,10%)
    ┌────┐         ┌──┐              ┌──┐
    │🌙  │         │BOT           ⚡│
    └────┘         └──┘              └──┘
    ───────────────────────────────────────────
                    [地板区域 - checkerboard]
    📚书架(3%,42%)        🖥️办公桌(32%,35%)        🖥️服务器(右3%,50%)
    ┌────┐              ┌──────────┐              ┌────┐
    │📚  │    🐱(18%)   │🖥️⌨️🖱️🌵 │   🛋️(78%)    │💡 │
    └────┘              └──────────┘              └────┘
              ☕(72%)                        🛋️沙发(右8%,38%)
```

### 角色状态映射

| 状态 | Emoji | 位置 | 气泡 | 颜色 |
|------|-------|------|------|------|
| idle | 🤖 | 沙发区(72%,50%) | 待命中... | #94a3b8 |
| working | 👨‍💻 | 办公桌(38%,48%) | [HandlerName] | #ffd700 |
| researching | 🔍 | 办公桌(38%,48%) | [BaiduSearch] | #a855f7 |
| executing | ⚡ | 办公桌(38%,48%) | [LongRunning] | #f59e0b |
| syncing | 🔄 | 服务器旁(85%,52%) | [DataSync] | #22c55e |
| writing | ✍️ | 办公桌(38%,48%) | [AITask] | #3b82f6 |
| error | 💀 | 服务器旁(85%,52%) | 连接断开！ | #e94560 |
| 收尾中 | 👨‍💻 | 办公桌(38%,48%) | ✅ 收尾中... | #ffd700 |

---

## 三、组件架构

```
main.tsx
  └── BrowserRouter
        └── WebSocketProvider (全局 WS + 任务状态)
              └── App.tsx (Routes)
                    ├── Layout.tsx (侧边栏 + Header)
                    │     └── useWS() → connected, activity
                    │
                    ├── / → Dashboard.tsx
                    │     └── PixelRoom.tsx
                    │           ├── PixelCharacter.tsx (主角色)
                    │           ├── MiniNPC.tsx (小助手)
                    │           └── PixelFurniture.tsx (家具emoji)
                    │     ├── EventStream.tsx (compact)
                    │     ├── BotStatusCard.tsx (compact)
                    │     └── MetricsPanel.tsx (compact)
                    │
                    ├── /tasks → MissionControl.tsx
                    │     └── PixelCard (表格 + 筛选 + 抽屉)
                    │
                    ├── /charts → SystemCharts.tsx
                    │     └── Recharts AreaChart
                    │
                    └── /plugins → PluginHub.tsx
                          └── PixelCard (插件列表 + 扩展面板)
```

### 核心组件关系

```
WebSocketContext (全局单例)
    │
    ├─ useWebSocket() ──→ WebSocket 连接管理
    │     ├─ ws://${host}/ws 连接
    │     ├─ 心跳 ping/pong
    │     └─ 自动重连 (3s)
    │
    ├─ 事件处理器
    │     ├─ task:started/submitted → activeTasks.push()
    │     ├─ task:completed/failed → activeTasks.remove() + finishingTasks.push()
    │     ├─ task:progress → 更新进度
    │     ├─ bot:message_received → activity = working
    │     └─ bot:message_sent → activity = idle
    │
    └─ 定时器
          ├─ idleTimer (15s无事件→idle)
          └─ finishingTimer (1s轮询清理5s前的收尾任务)
```

---

## 四、状态同步机制

```
微信消息 / 命令
     │
     ▼
┌─────────────┐
│  Bot.core   │
│  消息处理器  │
└──────┬──────┘
       │
       ├─→ BackgroundTaskHandler.handle()
       │       │
       │       ├─→ executor.submit(task, coro) ──→ task:submitted
       │       │
       │       └─→ TaskExecutor._worker_loop()
       │               │
       │               ├─→ task:started (任务开始)
       │               │
       │               ├─→ self.report_progress("xx%")
       │               │       └─→ task:progress
       │               │
       │               └─→ run() 返回 TaskResult
       │                       │
       │                       ├─→ success ──→ task:completed
       │                       └─→ fail ─────→ task:failed
       │
       └─→ EventBus.emit() ──→ WebSocketHub.broadcast()
                                   │
                                   ▼
                              前端 WebSocket.onmessage
                                   │
                                   ▼
                              WebSocketContext
                                   │
                              ┌────┴────┐
                              ▼         ▼
                        PixelRoom   EventStream
                              │
                              ├─→ PixelCharacter (角色移动)
                              ├─→ MiniNPC (小助手)
                              └─→ 服务器指示灯
```

### 事件处理时序（正常任务 vs 极快任务）

```
正常任务（中山一院 - 几十秒）:
t=0ms   task:submitted  → UI: 事件流显示提交
       task:started    → UI: 🤖→👨‍💻 走到办公桌，[BaiduSearch]
t=30s  task:completed  → UI: 👨‍💻 ✅收尾中... (5s) → 🤖 回沙发

极快任务（盛诺一家 - <1ms）:
t=0ms   task:submitted
       task:started    → UI: 🤖→👨‍💻 走到办公桌
       task:completed  → UI: 👨‍💻 ✅收尾中... (5s) → 🤖 回沙发

修复前的问题（极快任务）:
t=0ms   task:submitted
       task:started    → React 批量: setEvents([started, completed])
       task:completed  → useEffect 只取 latest = completed
                       → activeTasks 中找不到 taskId（started 的 setState 未生效）
                       → 直接 fallback idle → UI: 🤖 沙发区（看不到任务）
```

---

## 五、路由与页面

| 路由 | 页面 | 功能 |
|------|------|------|
| `/` | Dashboard | 像素房间 + 实时事件 + Bot状态 + 系统状态 |
| `/tasks` | MissionControl | 任务列表（状态筛选/搜索/详情抽屉） |
| `/charts` | SystemCharts | Recharts CPU/内存趋势图 + 统计卡片 |
| `/plugins` | PluginHub | 已注册处理器列表 + 扩展面板占位 |

---

## 六、配色系统

```
@theme {
  --color-so-bg:        #1a1a2e    (页面背景 - 深蓝紫)
  --color-so-card:      #141722    (卡片背景 - 深色面板)
  --color-so-border:    #0e1119    (边框 - 粗实线)
  --color-so-gold:      #ffd700    (标题/强调 - 金色)
  --color-so-red:       #e94560    (失败/断开 - 红色)
  --color-so-green:     #22c55e    (成功/在线 - 绿色)
  --color-so-blue:      #3b82f6    (工作中 - 蓝色)
  --color-so-purple:    #a855f7    (调研中 - 紫色)
  --color-so-amber:     #f59e0b    (执行中 - 琥珀色)
  --color-so-text:      #e2e8f0    (主文字 - 浅灰)
  --color-so-text-dim:  #94a3b8    (次要文字)
}
```

### 像素风设计特征

| 元素 | 风格 |
|------|------|
| 边框 | 3px 粗实线 #0e1119，无圆角或极小圆角 |
| 阴影 | `box-shadow: 4px 4px 0 rgba(0,0,0,0.3)`（硬阴影） |
| 字体 | `'Courier New', monospace`（等宽像素感） |
| 角标 | 四角金色 L 形装饰线（`.pixel-corners`） |
| 标题 | `◆ 标题 ◆` 居中，金色，带装饰符号 |
| 按钮 | 粗边框 + 硬阴影，hover 变色 |
| 进度条 | 直角，无圆角，方块填充 |
| 动画 | `steps(2)` 步进动画（模拟像素闪烁） |

---

## 七、文件结构

```
web/
├── package.json
├── vite.config.ts              # Vite + TailwindCSS v4 + Proxy
├── index.html
├── CHANGELOG.md                # 变更记录
├── DESIGN.md                   # 本文档
├── src/
│   ├── main.tsx                # React 入口 (BrowserRouter + WebSocketProvider)
│   ├── App.tsx                 # 路由配置
│   ├── index.css               # 全局像素风样式 + 动画
│   ├── types/
│   │   └── index.ts            # TypeScript 类型定义
│   ├── lib/
│   │   └── utils.ts            # cn() 工具函数
│   ├── services/
│   │   └── api.ts              # REST API 封装
│   ├── hooks/
│   │   ├── useWebSocket.ts     # WebSocket 连接管理
│   │   └── useMetricsHistory.ts # 系统指标历史采集
│   ├── contexts/
│   │   └── WebSocketContext.tsx # 全局状态 (活动/任务/事件)
│   ├── components/
│   │   ├── Layout.tsx          # 侧边栏 + Header 布局
│   │   ├── ConnectionStatus.tsx # WS 连接状态
│   │   ├── EventStream.tsx     # 实时事件流
│   │   ├── BotStatusCard.tsx   # Bot 状态卡片
│   │   ├── MetricsPanel.tsx    # 系统指标面板
│   │   ├── PixelCard.tsx       # 像素风卡片容器
│   │   ├── PixelBadge.tsx      # 像素风标签
│   │   └── pixel-room/
│   │       ├── PixelRoom.tsx   # 像素房间主场景
│   │       ├── PixelCharacter.tsx # 主角色 (Emoji + 气泡)
│   │       └── MiniNPC.tsx     # 小助手 NPC
│   └── pages/
│       ├── Dashboard.tsx       # 首页 (像素房间 + 三栏)
│       ├── MissionControl.tsx  # 任务中心
│       ├── SystemCharts.tsx    # 系统监控图表
│       └── PluginHub.tsx       # 插件中心
└── dist/                       # 构建产物 (FastAPI 静态服务)
```

---

## 八、后端交互

```
浏览器 ←─────────────────────────────→ FastAPI (port 3000)
         GET  /api/health              → {status, version, subscribers}
         GET  /api/bot/status          → {running, handlers, webhook, workers}
         GET  /api/tasks?status=&limit → {tasks[], total}
         GET  /api/system/metrics      → {cpu, memory, disk, uptime}
         GET  /api/events/history      → {events[], count}
         WS   /ws                      → 实时事件流
         GET  /                        → 静态文件 (web/dist/index.html)
```

### WebSocket 消息协议

```typescript
type WSMessage =
  | { type: 'connected'; client_id: string; message: string }
  | { type: 'subscribed'; events: string[] }
  | { type: 'event'; event: string; timestamp: number; data: Record<string, unknown>; source: string }
  | { type: 'pong'; time: number }
  | { type: 'error'; message: string };
```

---

*设计参考: [Star Office UI](https://github.com/ringhyacinth/Star-Office-UI) 像素风 AI 办公室*
