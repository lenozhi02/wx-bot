# Phase 1: 事件总线 + 状态埋点

## 设计目标

1. 实现内存事件总线，支持异步事件发布/订阅
2. 在现有核心模块中埋入事件触发点，将关键状态变更广播到 UI 层
3. 保证低耦合：现有代码不依赖 UI 层，通过事件总线单向通信

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        事件总线 (EventBus)                    │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │  bot:event   │  task:event  │  sys:event   │             │
│  └──────────────┴──────────────┴──────────────┘             │
├─────────────────────────────────────────────────────────────┤
│                      生产者（现有代码埋点）                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ WeixinBot│  │TaskExec  │  │ Webhook  │  │ Status   │   │
│  │ _handle_ │  │ worker   │  │ _handle_ │  │ Task     │   │
│  │ message  │  │ loop     │  │ send     │  │ handler  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼（事件广播）
┌─────────────────────────────────────────────────────────────┐
│                      消费者（UI 层）                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ WebSocket│  │ 日志记录  │  │ 指标统计  │                   │
│  │  Hub     │  │          │  │          │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## 事件总线设计

### 核心类

```python
class EventBus:
    """
    异步内存事件总线
    
    特性：
    - 支持多播：一个事件多个消费者
    - 异步非阻塞：消费者通过 asyncio.create_task 执行
    - 弱引用：可选，防止内存泄漏
    - 类型安全：事件数据使用 TypedDict
    """
```

### 事件类型定义

```python
# Bot 事件
BotMessageEvent = {
    "event": "bot:message_received",
    "timestamp": float,
    "data": {
        "from_user": str,
        "content": str,
        "context_token": Optional[str],
    }
}

# 任务事件
TaskEvent = {
    "event": "task:started",  # | task:progress | task:completed | task:failed
    "timestamp": float,
    "data": {
        "task_id": str,
        "handler_name": str,
        "user_id": str,
        "progress": Optional[str],
        "duration": Optional[float],
        "error": Optional[str],
    }
}

# 系统事件
SysMetricsEvent = {
    "event": "sys:metrics",
    "timestamp": float,
    "data": {
        "cpu_percent": float,
        "memory_percent": float,
        "disk_percent": float,
        "uptime": str,
    }
}
```

## 埋点位置

| 模块 | 方法 | 触发事件 | 时机 |
|------|------|---------|------|
| `bot.py` | `_handle_message` | `bot:message_received` | 收到消息 |
| `bot.py` | `_send_text` | `bot:message_sent` | 发送消息 |
| `bot.py` | `_poll_loop` | `bot:connected`/`disconnected` | 连接状态变更 |
| `background.py` | `submit` | `task:submitted` | 任务提交 |
| `background.py` | `_worker_loop` | `task:started` | 任务开始 |
| `background.py` | `_worker_loop` | `task:completed`/`failed` | 任务结束 |
| `webhook.py` | `_process_send` | `webhook:received` | 收到推送 |
| `bot.py` | `_webhook_consumer` | `webhook:delivered` | 推送成功 |

## 低耦合保证

1. **无侵入**：EventBus 实例通过参数注入，不传则不触发事件
2. **容错**：事件发送失败不影响主业务流程
3. **可选依赖**：现有代码通过 `if self.event_bus:` 判断后触发
