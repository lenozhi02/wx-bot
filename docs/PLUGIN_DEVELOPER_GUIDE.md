# WX-BOT 插件开发指南

## 一、快速开始

创建一个最简单的插件只需 2 个文件：

```
plugins/hello/
├── manifest.json
└── handler.py
```

### 1. manifest.json

```json
{
  "id": "hello",
  "name": "Hello 插件",
  "version": "1.0.0",
  "description": "回复 hello 触发",
  "author": "your-name",
  "priority": 50,
  "handler_class": "HelloHandler",
  "handler_file": "handler.py"
}
```

### 2. handler.py

```python
from src.tasks.base import TaskHandler, TaskResult

class HelloHandler(TaskHandler):
    name = "hello"
    priority = 50
    description = "Hello World 示例"

    def can_handle(self, content: str, msg: dict) -> bool:
        return content.strip().lower() == "hello"

    def handle(self, content: str, msg: dict) -> TaskResult:
        return TaskResult(
            success=True,
            content="Hello, World! 🌍",
            data={}
        )
```

### 3. 生效

不需要重启服务：

1. 打开 Web UI → **插件中心**
2. 点击 **"重载全部"** 按钮
3. 插件自动加载，在微信发送 `hello` 即可触发

---

## 二、Handler 类型

### 2.1 同步 Handler（TaskHandler）

适用于**即时响应**的场景，如文本回复、简单计算。

```python
from src.tasks.base import TaskHandler, TaskResult

class MyHandler(TaskHandler):
    name = "my_handler"
    priority = 50
    description = "我的处理器"

    def can_handle(self, content: str, msg: dict) -> bool:
        """判断是否能处理这条消息"""
        return "关键词" in content

    def handle(self, content: str, msg: dict) -> TaskResult:
        """处理消息并返回结果"""
        return TaskResult(
            success=True,
            content="处理结果",
            data={"extra": "附加数据"}
        )
```

### 2.2 后台 Handler（BackgroundTaskHandler）

适用于**耗时操作**，如网络请求、文件生成、数据同步。任务在后台执行，完成后自动推送结果到微信。

```python
import asyncio
from src.tasks.background import BackgroundTaskHandler
from src.tasks.base import TaskResult

class MyAsyncHandler(BackgroundTaskHandler):
    name = "my_async"
    priority = 50
    description = "异步任务示例"

    def can_handle(self, content: str, msg: dict) -> bool:
        return "async" in content.lower()

    async def run(self, content: str, msg: dict, **kwargs) -> TaskResult:
        """异步执行耗时任务"""
        # 上报进度（前端 Dashboard 会实时显示）
        self.report_progress(10, "开始处理...")
        await asyncio.sleep(2)

        self.report_progress(50, "处理中...")
        await asyncio.sleep(2)

        self.report_progress(100, "完成！")
        return TaskResult(
            success=True,
            content="✅ 异步任务完成",
            data={"duration": 4}
        )
```

**进度上报**：`self.report_progress(progress, message)` 会触发 `task:progress` 事件，前端 Dashboard 实时显示进度条。

---

## 三、优先级机制

`priority` 数值**越小**，匹配优先级**越高**。

```
priority=10   → 高优先级（先匹配）
priority=50   → 默认优先级
priority=100  → 低优先级（后匹配，可作兜底）
```

**建议**：
- 指令类插件（如 `status`、`help`）: `priority=10~30`
- 普通功能插件: `priority=40~70`
- 兜底/通用插件（如 AI 对话）: `priority=90~100`

---

## 四、可用 API

### 4.1 消息上下文

`msg` 字典包含完整消息信息：

```python
def handle(self, content: str, msg: dict) -> TaskResult:
    room_id = msg.get("roomId")      # 群聊 ID（私聊为空）
    sender = msg.get("sender")       # 发送者
    user_id = msg.get("userId")      # 用户 ID
    # ...
```

### 4.2 微信 API

如需主动调用微信 API，可在 handler 中注入 `WeixinAPI` 实例（需通过构造函数传入）。

### 4.3 事件总线

```python
from src.ui.bus import get_default_bus

bus = get_default_bus()
bus.emit("custom:event", {"key": "value"})
```

---

## 五、调试技巧

### 5.1 本地测试加载

```python
from src.plugins.loader import PluginLoader
from src.tasks.registry import TaskRegistry

registry = TaskRegistry()
loader = PluginLoader()
handler = loader.load("hello")
registry.register(handler)

# 模拟消息
result = registry.dispatch("hello", {})
print(result)
```

### 5.2 查看日志

插件加载/卸载日志：

```
[plugin] 扫描到 2 个插件
[plugin] 加载插件: echo → handler=echo priority=90
[registry] 注册任务处理器: echo (priority=90)
```

### 5.3 热重载开发

修改 `handler.py` 后，在 Web UI 点击该插件的 **"重载"** 按钮，新代码立即生效，无需重启服务。

---

## 六、最佳实践

1. **目录名 = 插件 ID**：确保全局唯一
2. **handler_class 一致**：`manifest.json` 中的类名必须和 `handler.py` 中的类名一致
3. **异常处理**：`can_handle` 和 `handle` 中应捕获异常，避免影响其他处理器
4. **避免阻塞**：耗时操作务必使用 `BackgroundTaskHandler`
5. **清理资源**：如需释放资源，可在 handler 中实现 `__del__` 或提供 `cleanup()` 方法

---

## 七、示例插件参考

| 插件 | 类型 | 说明 |
|------|------|------|
| `plugins/echo` | 同步 | 复读消息 |
| `plugins/reminder` | 后台 | 异步提醒，演示进度上报 |
