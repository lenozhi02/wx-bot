# Phase 2 变更记录

## 新增文件

| 文件 | 说明 |
|------|------|
| `src/ui/hub.py` | WebSocket Hub + SSE Stream（244行） |
| `src/ui/server.py` | FastAPI 服务 + REST API（263行） |
| `tests/ui/test_server.py` | FastAPI 服务端点测试 |

## 修改文件

| 文件 | 变更 |
|------|------|
| `main.py` | 添加 `--ui-port`/`--no-ui` 参数；创建 UIServer；支持并发运行 Bot + UI |

## API 端点清单

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/bot/status` | GET | Bot 运行状态 |
| `/api/bot/handlers` | GET | 已注册处理器列表 |
| `/api/tasks` | GET | 任务列表（支持 status/limit 过滤） |
| `/api/tasks/{id}` | GET | 单个任务详情 |
| `/api/system/metrics` | GET | 系统指标（CPU/内存/磁盘） |
| `/api/events/history` | GET | 事件历史记录 |
| `/api/webhook/status` | GET | Webhook 状态 |
| `/api/events/stream` | GET | SSE 事件流 |
| `/ws` | WS | WebSocket 实时事件 |
