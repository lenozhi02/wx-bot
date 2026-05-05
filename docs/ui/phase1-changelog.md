# Phase 1 变更记录

## 新增文件

| 文件 | 说明 |
|------|------|
| `src/ui/bus.py` | 事件总线实现（EventBus + BusEvent） |
| `tests/ui/test_bus.py` | 事件总线单元测试 |

## 修改文件

| 文件 | 变更 |
|------|------|
| `src/bot.py` | 注入 event_bus，埋点 6 个事件：`bot:message_received`, `bot:message_sent`, `bot:connected`, `bot:disconnected`, `webhook:delivered`, `task:completed`/`failed` |
| `src/tasks/background.py` | Executor 注入 event_bus，埋点 5 个事件：`task:submitted`, `task:started`, `task:progress`, `task:completed`, `task:failed`, `task:cancelled` |
| `src/webhook.py` | 埋点 1 个事件：`webhook:received` |
| `main.py` | 创建 EventBus，注入到 Executor 和 Bot |

## 事件清单

| 事件名 | 来源 | 触发时机 |
|--------|------|---------|
| `bot:connected` | bot.py | 长轮询连接成功 |
| `bot:disconnected` | bot.py | 长轮询异常断开 |
| `bot:message_received` | bot.py | 收到微信消息 |
| `bot:message_sent` | bot.py | 发送微信消息（成功/失败） |
| `task:submitted` | background.py | 任务提交到队列 |
| `task:started` | background.py | Worker 开始执行 |
| `task:progress` | background.py | 任务进度更新 |
| `task:completed` | background.py | 任务成功完成 |
| `task:failed` | background.py | 任务执行失败 |
| `task:cancelled` | background.py | 任务被取消 |
| `webhook:received` | webhook.py | 收到外部推送 |
| `webhook:delivered` | bot.py | Webhook 消息推送给微信 |
