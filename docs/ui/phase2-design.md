# Phase 2: FastAPI 服务 + WebSocket Hub

## 设计目标

1. 提供 REST API 供前端查询当前状态（Bot、任务、系统）
2. 提供 WebSocket 连接，实现服务器→前端的实时事件推送
3. 提供 SSE（Server-Sent Events）流，作为 WebSocket 的轻量替代
4. 与 Phase 1 的事件总线对接，自动将事件推送到已连接的客户端

## 架构图

```
前端浏览器
    │
    ├─▶ REST API ──▶ FastAPI ──▶ Service ──▶ 内存状态
    │     GET /api/bot/status
    │     GET /api/tasks
    │     GET /api/system/metrics
    │
    ├─▶ WebSocket ──▶ Hub ──▶ EventBus ──▶ 事件监听
    │     ws://host:port/ws
    │     {"type": "subscribe", "events": ["task:*"]}
    │
    └─▶ SSE ──▶ Stream ──▶ EventBus
          GET /api/events/stream

        EventBus (Phase 1)
            │
            ├── bot:message_received ──▶ 广播到所有 WS 客户端
            ├── task:started ──▶ 广播
            ├── task:progress ──▶ 广播
            └── ...
```

## API 设计

### REST API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 服务健康检查 |
| `/api/bot/status` | GET | Bot 连接状态、在线时长 |
| `/api/bot/handlers` | GET | 已注册的处理器列表 |
| `/api/tasks` | GET | 任务列表（支持过滤） |
| `/api/tasks/{id}` | GET | 单个任务详情 |
| `/api/system/metrics` | GET | 系统指标（CPU/内存/磁盘） |
| `/api/events/history` | GET | 事件历史记录 |
| `/api/webhook/status` | GET | Webhook 状态 |

### WebSocket 协议

```json
// 客户端 → 服务器
{"type": "subscribe", "events": ["task:*", "bot:message_received"]}
{"type": "unsubscribe", "events": ["task:*"]}
{"type": "ping"}

// 服务器 → 客户端
{"type": "event", "event": "task:started", "timestamp": 1234567890, "data": {...}}
{"type": "pong"}
```

### SSE 流

```
GET /api/events/stream?filter=task:*

// 响应
Content-Type: text/event-stream

event: task:started
data: {"task_id": "xxx", ...}

event: task:completed
data: {"task_id": "xxx", ...}
```

## 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| Web 框架 | FastAPI | 异步原生、自动文档、类型提示 |
| WebSocket | FastAPI native | 内置支持，无需额外依赖 |
| SSE | FastAPI Response | StreamingResponse |
| CORS | fastapi.middleware.cors | 前端跨域 |

## 端口设计

UI 服务独立端口，与 Webhook 不冲突：
- Webhook: `--webhook-port` (默认 8080)
- UI API: `--ui-port` (默认 3000)

低耦合：UI 服务可独立启停，不影响 Bot 核心功能。
