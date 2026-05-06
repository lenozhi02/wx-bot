# WX-BOT 动态插件系统

## 一、概述

WX-BOT 支持**运行时热加载插件**：在 `plugins/` 目录下创建插件目录（含 `manifest.json` + `handler.py`），无需重启服务即可通过 Web UI 或 API 加载、卸载、重载插件。

核心特性：

- **不停止服务** — 通过 API 或文件操作即可加载新插件
- **零代码修改核心** — 新增插件只需在 `plugins/` 目录下放文件
- **安全隔离** — 插件异常不导致主程序崩溃，支持独立卸载
- **向后兼容** — 现有内置 handler 继续正常工作

---

## 二、架构

```
┌────────────────────────────────────────────────────────────────┐
│                        WX-BOT 运行时                             │
│                                                                │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐ │
│  │   Bot    │    │  Plugin  │    │  Plugin  │    │ Plugin  │ │
│  │  核心    │◄──►│  Loader  │◄──►│ Manager  │◄──►│  API    │ │
│  │          │    │          │    │          │    │         │ │
│  │ registry │    │扫描目录  │    │ 加载/卸载 │    │ REST    │ │
│  │ executor │    │动态import│    │ 元数据维护│    │ WebSocket│ │
│  └──────────┘    └──────────┘    └──────────┘    └─────────┘ │
│       ▲                                              ▲        │
│       └──────────────────────────────────────────────┘        │
│                      WebSocket 事件                             │
│              plugin:loaded / plugin:unloaded                   │
└────────────────────────────────────────────────────────────────┘
```

### 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `PluginLoader` | `src/plugins/loader.py` | 扫描 `plugins/` 目录，解析 `manifest.json`，通过 `importlib` 动态导入模块 |
| `PluginManager` | `src/plugins/manager.py` | 桥接 Loader + Registry + EventBus，提供 `load/unload/reload/reload_all` |
| `TaskRegistry` | `src/tasks/registry.py` | 管理所有处理器（内置 + 插件），支持优先级排序和分发 |

---

## 三、插件目录规范

```
plugins/
├── echo/                        # 插件目录名 = 插件ID
│   ├── manifest.json            # 插件元数据
│   └── handler.py               # 处理器实现
│
├── reminder/                    # 另一个插件
│   ├── manifest.json
│   └── handler.py
│
└── README.md
```

### manifest.json

```json
{
  "id": "echo",
  "name": "回声插件",
  "version": "1.0.0",
  "description": "复读用户消息，支持 echo/复读 触发",
  "author": "bot-admin",
  "priority": 90,
  "handler_class": "EchoHandler",
  "handler_file": "handler.py"
}
```

字段说明：

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 插件唯一标识，必须与目录名一致 |
| `name` | 是 | 显示名称 |
| `version` | 否 | 版本号，默认 `0.0.0` |
| `description` | 否 | 功能描述 |
| `author` | 否 | 作者 |
| `priority` | 否 | 处理器优先级，数值小的优先匹配，默认 `50` |
| `handler_class` | 是 | `handler.py` 中的类名 |
| `handler_file` | 否 | 处理器文件名，默认 `handler.py` |

### handler.py

支持两种 Handler 类型：

#### A. 同步 Handler（继承 TaskHandler）

```python
from src.tasks.base import TaskHandler, TaskResult

class EchoHandler(TaskHandler):
    name = "echo"
    priority = 90
    description = "复读用户消息"

    def can_handle(self, content: str, msg: dict) -> bool:
        return "echo" in content.lower() or "复读" in content

    def handle(self, content: str, msg: dict) -> TaskResult:
        return TaskResult(
            success=True,
            content=f"📢 复读: {content}",
            data={"original": content}
        )
```

#### B. 后台 Handler（继承 BackgroundTaskHandler）

```python
from src.tasks.background import BackgroundTaskHandler
from src.tasks.base import TaskResult

class ReminderHandler(BackgroundTaskHandler):
    name = "reminder"
    priority = 85
    description = "定时提醒（异步任务）"

    def can_handle(self, content: str, msg: dict) -> bool:
        return "remind" in content.lower() or "提醒" in content

    async def run(self, content: str, msg: dict, **kwargs) -> TaskResult:
        self.report_progress(50, "处理中...")
        # 耗时操作...
        return TaskResult(success=True, content="完成！")
```

**关键约定**：
- 插件目录名必须全局唯一，作为插件 ID
- `handler_class` 必须与 `handler.py` 中的类名一致
- `BackgroundTaskHandler` 会自动注入 `executor`
- 插件内部 `import` 使用 `src.xxx` 绝对路径

---

## 四、后端 API

### 端点列表

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/plugins` | 列出所有已加载插件 |
| `GET` | `/api/plugins/{id}` | 获取单个插件详情 |
| `POST` | `/api/plugins/reload` | 扫描目录并重载所有插件 |
| `POST` | `/api/plugins/{id}/load` | 加载指定插件 |
| `POST` | `/api/plugins/{id}/unload` | 卸载指定插件 |
| `POST` | `/api/plugins/{id}/reload` | 重载单个插件 |
| `GET` | `/api/plugins/handlers/all` | 列出全部处理器（内置 + 插件） |

### 响应示例

```bash
# 列出已加载插件
curl http://localhost:3000/api/plugins
# {
#   "plugins": [
#     {
#       "id": "echo",
#       "name": "回声插件",
#       "version": "1.0.0",
#       "description": "复读用户消息",
#       "author": "bot-admin",
#       "priority": 90,
#       "handler_class": "EchoHandler",
#       "status": "loaded"
#     }
#   ],
#   "count": 1
# }

# 加载新插件
curl -X POST http://localhost:3000/api/plugins/my_plugin/load
# {"status": "ok", "plugin_id": "my_plugin", "action": "load"}

# 重载所有插件
curl -X POST http://localhost:3000/api/plugins/reload
# {"reloaded": {"echo": true, "reminder": true}, "count": 2}
```

### WebSocket 事件

| 事件 | 触发时机 | 数据 |
|------|---------|------|
| `plugin:loaded` | 插件加载成功 | `"plugin_id"` |
| `plugin:unloaded` | 插件卸载成功 | `"plugin_id"` |
| `plugin:error` | 加载/卸载失败 | `{"plugin_id": "...", "error": "..."}` |

---

## 五、前端 PluginHub

Web UI 的 **插件中心** 页面提供：

- **已加载插件列表** — 显示版本、优先级、状态标签
- **操作按钮** — 重载 / 卸载单个插件
- **重载全部** — 一键扫描目录并加载所有插件
- **全部处理器** — 查看内置 + 插件的完整处理器列表

---

## 六、启动流程

`main.py` 启动时自动初始化插件系统：

```python
from src.plugins.loader import PluginLoader
from src.plugins.manager import PluginManager

# 1. 创建插件加载器（注入 executor 以支持后台任务）
plugin_loader = PluginLoader(executor=executor)

# 2. 创建插件管理器
plugin_manager = PluginManager(
    registry=registry,
    loader=plugin_loader,
    event_bus=event_bus
)

# 3. 启动时自动加载所有插件
plugin_results = plugin_manager.reload_all()

# 4. 注入 UI Server
ui_server = UIServer(
    ...,
    plugin_manager=plugin_manager
)
```

---

## 七、安全与隔离

### 异常隔离

```python
try:
    handler = self.loader.load(plugin_id)
    self.registry.register(handler)
except Exception as e:
    logger.error(f"[plugin] 加载 {plugin_id} 失败: {e}")
    # 不抛异常，不影响其他插件和主程序
    return False
```

### 模块缓存清理

卸载插件时清理 `sys.modules`，防止内存泄漏和旧代码残留：

```python
module_name = f"__wxbot_plugin_{plugin_id}"
if module_name in sys.modules:
    del sys.modules[module_name]
```

### 命名空间隔离

- 插件模块名格式：`__wxbot_plugin_{plugin_id}`
- 使用 `importlib.util.spec_from_file_location` 动态导入，不污染 `sys.path`

---

## 八、Worker 可视化同步

Dashboard 像素房间中的 **Worker 工位栏** 与后端 `TaskExecutor` 的 worker 数量、任务名称、状态实时同步。

### 8.1 后端状态追踪

`TaskExecutor` 维护 `_worker_tasks: Dict[str, Optional[str]]`，记录每个 worker 当前执行的任务 ID：

```python
class TaskExecutor:
    def __init__(self, max_workers=3, ...):
        self._worker_tasks: Dict[str, Optional[str]] = {}

    async def _worker_loop(self, name: str):
        self._worker_tasks[name] = None
        while self.running:
            task, coro = await self.task_queue.get()
            self._worker_tasks[name] = task.task_id  # 开始执行
            # ... 执行任务 ...
            self._worker_tasks[name] = None           # 执行完毕

    def get_worker_states(self) -> List[dict]:
        """返回每个 worker 的状态列表"""
```

### 8.2 API 暴露

`GET /api/bot/status` 返回 `workers` 数组：

```json
{
  "executor_workers": 3,
  "workers": [
    { "name": "worker-0", "status": "running", "task": { "task_id": "...", "handler_name": "baidu_search", "progress": "搜索中...", "started_at": 1234567890 } },
    { "name": "worker-1", "status": "idle", "task": null },
    { "name": "worker-2", "status": "idle", "task": null }
  ]
}
```

### 8.3 WebSocket 实时同步

| 事件 | worker 字段 | 前端行为 |
|------|------------|---------|
| `task:started` | `worker: "worker-0"` | 设置对应 worker 为 `running`，记录任务名 |
| `task:progress` | 无（通过 `task_id` 关联） | 更新对应 worker 的进度文本 |
| `task:completed` | 无（通过 `task_id` 关联） | 设置对应 worker 为 `success`，清空任务 |
| `task:failed` | 无（通过 `task_id` 关联） | 设置对应 worker 为 `failed`，清空任务 |
| `task:cancelled` | 无（通过 `task_id` 关联） | 设置对应 worker 为 `failed`，清空任务 |

### 8.4 前端双通道同步

1. **API 初始化**：WebSocket 连接成功后，调用 `GET /api/bot/status` 获取初始 worker 列表，后续每 10 秒同步一次防漂移
2. **WebSocket 实时更新**：事件驱动，毫秒级响应

### 8.5 UI 展示

**PixelRoom — Worker 工位栏**：
- 底部显示一排 worker 机器人，数量 = `executor_workers`
- 每个 worker 显示：编号（W0/W1/W2）、任务名、进度、状态灯
- 状态：😴 空闲 / 💻 执行中 / ✅ 完成 / ❌ 失败

**BotStatusCard — Worker 详情**：
- 显示每个 worker 的当前任务和状态标签
- 状态灯实时闪烁（执行中时）

---

## 九、文件清单

### 新增文件

```
src/plugins/
├── __init__.py          # 包初始化
├── loader.py            # PluginLoader
└── manager.py           # PluginManager

plugins/
├── echo/
│   ├── manifest.json
│   └── handler.py
├── reminder/
│   ├── manifest.json
│   └── handler.py
└── README.md

docs/PLUGIN_SYSTEM_DESIGN.md   # 本文档
docs/PLUGIN_DEVELOPER_GUIDE.md # 插件开发指南
```

### 修改文件

```
src/tasks/registry.py         # 新增 get_handler_info() / get_handler()
src/ui/server.py              # 新增 7 个插件管理 API 端点
web/src/services/api.ts       # 新增插件管理 API 调用
web/src/pages/PluginHub.tsx   # 支持动态加载/卸载/重载交互
main.py                       # 启动时自动初始化插件系统
```

---

*设计目标：不停止服务，新增插件并注册可用*
