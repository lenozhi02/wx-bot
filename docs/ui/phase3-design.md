# Phase 3: 前端仪表盘框架

## 设计目标

1. 使用 React + Vite 构建现代化前端
2. 暗色主题 UI，类似斯坦福小镇的可视化风格
3. WebSocket 实时连接后端事件总线
4. 仪表盘首页：系统状态概览 + 实时事件流

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18 | UI 框架 |
| Vite | 6 | 构建工具 |
| TypeScript | 5 | 类型安全 |
| Tailwind CSS | 4 | 样式系统 |
| WebSocket API | native | 实时通信 |
| Lucide React | latest | 图标库 |

## 页面设计

### 仪表盘首页 (/)

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 WX-BOT 指挥中心                    [暗色/亮色切换] [刷新]  │
├────────────────────────┬───────────────────────────────────┤
│                        │                                   │
│   ┌─────────────────┐  │   📡 实时事件流                    │
│   │   系统状态       │  │   ────────────────────────────   │
│   │                 │  │   🟢 Bot 在线                     │
│   │  CPU  ████░░░░   │  │   📩 新消息 [用户A]               │
│   │  45%            │  │   🚀 任务启动 [baidu_search]      │
│   │                 │  │   ✅ 任务完成                     │
│   │  内存 ██████░░   │  │   ...                            │
│   │  80%            │  │                                   │
│   │                 │  │                                   │
│   │  磁盘 ████████   │  │                                   │
│   │  90%            │  │                                   │
│   └─────────────────┘  │                                   │
│                        │                                   │
│   ┌─────────────────┐  │   🎯 活跃任务                      │
│   │   连接状态       │  │   ────────────────────────────   │
│   │                 │  │   • baidu_search 运行中  [15m]    │
│   │  🟢 微信已连接   │  │   • long_task 已完成    [2m]     │
│   │  🟢 Webhook     │  │                                   │
│   │  📊 今日 128 条 │  │                                   │
│   └─────────────────┘  │                                   │
│                        │                                   │
├────────────────────────┴───────────────────────────────────┤
│  WebSocket: 🟢 已连接 | 延迟: 12ms | 最后心跳: 2s前           │
└─────────────────────────────────────────────────────────────┘
```

## 组件结构

```
web/src/
├── main.tsx              # 入口
├── App.tsx               # 根组件
├── index.css             # 全局样式
├── components/           # 通用组件
│   ├── Layout.tsx        # 布局框架
│   ├── Header.tsx        # 顶部导航
│   ├── Sidebar.tsx       # 侧边栏
│   ├── StatusCard.tsx    # 状态卡片
│   ├── EventStream.tsx   # 事件流
│   ├── TaskList.tsx      # 任务列表
│   ├── MetricsPanel.tsx  # 指标面板
│   └── ConnectionStatus.tsx  # 连接状态
├── hooks/                # 自定义 Hooks
│   ├── useWebSocket.ts   # WebSocket 管理
│   └── useAPI.ts         # REST API 调用
├── types/                # TypeScript 类型
│   └── index.ts
└── services/             # API 服务
    ├── api.ts            # REST API
    └── websocket.ts      # WebSocket 封装
```

## WebSocket 前端协议

```typescript
// 连接后自动订阅所有事件
{ type: "subscribe", events: ["*"] }

// 接收事件
{ type: "event", event: "bot:message_received", timestamp: 123, data: {...} }

// 心跳
{ type: "ping" }  →  { type: "pong", time: 123 }
```

## 暗色主题

使用 Tailwind CSS 的 dark 模式，配色方案：
- 背景: slate-900 / slate-950
- 卡片: slate-800
- 边框: slate-700
- 文字: slate-100 / slate-300
- 强调色: emerald-500 (成功), amber-500 (警告), rose-500 (错误)
