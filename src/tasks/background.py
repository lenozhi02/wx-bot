"""
后台任务支持模块

支持长时间运行的异步任务，执行完成后自动推送结果到微信。

使用方式：
1. 继承 BackgroundTaskHandler，实现 run() 方法
2. 在 run() 中通过 self.report_progress() 上报进度
3. 任务完成后，结果自动推送到微信

架构：
  用户消息 → TaskRegistry.dispatch() → BackgroundTaskHandler
                                          ↓
                                    提交到 TaskExecutor
                                          ↓
                                    后台线程/协程执行
                                          ↓
                                    完成后 → 结果队列 → Bot推送
"""

import asyncio
import logging
import time
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, Coroutine
from enum import Enum

from src.tasks.base import TaskHandler, TaskResult

logger = logging.getLogger(__name__)

# 延迟导入避免循环依赖
def _get_event_bus():
    try:
        from src.ui.bus import EventBus
        return EventBus
    except ImportError:
        return None


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """后台任务数据模型"""
    task_id: str
    user_id: str
    handler_name: str
    content: str
    raw_msg: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None
    progress: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    context_token: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """任务执行时长（秒）"""
        if self.started_at is None:
            return 0
        end = self.finished_at or time.time()
        return end - self.started_at


class TaskExecutor:
    """
    后台任务执行器
    
    管理任务队列和结果队列，支持并发执行多个后台任务。
    """
    
    def __init__(self, max_workers: int = 3, event_bus=None):
        self.max_workers = max_workers
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.result_queue: asyncio.Queue = asyncio.Queue()
        self.tasks: Dict[str, BackgroundTask] = {}
        self._result_callback: Optional[Callable[[BackgroundTask], Coroutine]] = None
        self.event_bus = event_bus
        self.running = False
        self._worker_tasks: Dict[str, Optional[str]] = {}  # worker_name -> task_id
    
    def set_result_callback(self, callback: Callable[[BackgroundTask], Coroutine]):
        """设置任务完成后的回调函数（由 Bot 设置，用于推送结果）"""
        self._result_callback = callback
    
    async def submit(self, task: BackgroundTask, coro: Coroutine):
        """提交任务到执行队列"""
        self.tasks[task.task_id] = task
        await self.task_queue.put((task, coro))
        logger.info(f"[executor] 任务已提交: {task.task_id} ({task.handler_name})")
        
        # 触发任务提交事件
        if self.event_bus:
            await self.event_bus.emit("task:submitted", {
                "task_id": task.task_id,
                "handler_name": task.handler_name,
                "user_id": task.user_id,
                "content": task.content[:100],
            }, source="executor")
    
    async def start(self):
        """启动执行器，创建 worker 协程"""
        self.running = True
        logger.info(f"[executor] 启动，worker 数量: {self.max_workers}")
        
        workers = [
            asyncio.create_task(self._worker_loop(f"worker-{i}"))
            for i in range(self.max_workers)
        ]
        await asyncio.gather(*workers)
    
    async def _worker_loop(self, name: str):
        """Worker 协程：从队列取任务并执行"""
        logger.info(f"[executor] {name} 启动")
        self._worker_tasks[name] = None

        while self.running:
            try:
                task, coro = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            self._worker_tasks[name] = task.task_id
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            logger.info(f"[executor] {name} 开始执行任务: {task.task_id}")

            # 触发任务开始事件
            if self.event_bus:
                await self.event_bus.emit("task:started", {
                    "task_id": task.task_id,
                    "handler_name": task.handler_name,
                    "user_id": task.user_id,
                    "worker": name,
                }, source="executor")
            
            try:
                # 执行异步任务
                result = await coro
                task.result = result
                task.status = TaskStatus.SUCCESS
                logger.info(f"[executor] 任务完成: {task.task_id}, 耗时={task.duration:.1f}s")
                
                # 触发任务完成事件
                if self.event_bus:
                    await self.event_bus.emit("task:completed", {
                        "task_id": task.task_id,
                        "handler_name": task.handler_name,
                        "user_id": task.user_id,
                        "duration": task.duration,
                        "status": task.status.value,
                    }, source="executor")
                
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                logger.warning(f"[executor] 任务取消: {task.task_id}")
                
                if self.event_bus:
                    await self.event_bus.emit("task:cancelled", {
                        "task_id": task.task_id,
                        "handler_name": task.handler_name,
                    }, source="executor")
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.result = TaskResult.fail(f"任务执行异常: {str(e)}")
                logger.exception(f"[executor] 任务失败: {task.task_id}")
                
                if self.event_bus:
                    await self.event_bus.emit("task:failed", {
                        "task_id": task.task_id,
                        "handler_name": task.handler_name,
                        "error": str(e),
                    }, source="executor")
            
            finally:
                task.finished_at = time.time()
                self._worker_tasks[name] = None

                # 放入结果队列，触发回调
                await self.result_queue.put(task)
                if self._result_callback:
                    try:
                        await self._result_callback(task)
                    except Exception:
                        logger.exception(f"[executor] 结果回调失败: {task.task_id}")
    
    def stop(self):
        self.running = False
        logger.info("[executor] 已停止")

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """获取任务状态"""
        return self.tasks.get(task_id)

    def list_tasks(self) -> list:
        """列出所有任务"""
        return list(self.tasks.values())

    def get_worker_states(self) -> list:
        """返回每个 worker 的当前状态"""
        result = []
        for name in sorted(self._worker_tasks.keys(), key=lambda x: int(x.split('-')[-1])):
            task_id = self._worker_tasks[name]
            if task_id and task_id in self.tasks:
                task = self.tasks[task_id]
                result.append({
                    "name": name,
                    "status": task.status.value,
                    "task": {
                        "task_id": task.task_id,
                        "handler_name": task.handler_name,
                        "progress": task.progress,
                        "started_at": task.started_at,
                    }
                })
            else:
                result.append({
                    "name": name,
                    "status": "idle",
                    "task": None,
                })
        return result


class BackgroundTaskHandler(TaskHandler):
    """
    后台任务处理器基类
    
    子类需要实现：
    1. name / priority 属性
    2. can_handle() 方法
    3. run() 方法（异步，返回 TaskResult）
    
    示例：
        class LongRunningTask(BackgroundTaskHandler):
            @property
            def name(self): return "long_task"
            
            @property
            def priority(self): return 30
            
            def can_handle(self, content, msg):
                return content == "长任务"
            
            async def run(self, content, msg):
                for i in range(10):
                    await asyncio.sleep(1)  # 模拟耗时操作
                    self.report_progress(f"进度: {i+1}/10")
                return TaskResult.success("任务完成！")
    """
    
    def __init__(self, executor: TaskExecutor):
        self.executor = executor
        self._current_task: Optional[BackgroundTask] = None
    
    def handle(self, content: str, msg: Dict[str, Any]) -> TaskResult:
        """
        提交后台任务，立即返回"任务已启动"提示
        
        实际执行在 executor 的 worker 协程中进行。
        """
        task_id = f"task-{int(time.time()*1000)}-{id(msg)}"
        user_id = msg.get("from_user_id", "")
        context_token = msg.get("context_token")
        
        task = BackgroundTask(
            task_id=task_id,
            user_id=user_id,
            handler_name=self.name,
            content=content,
            raw_msg=msg,
            context_token=context_token,
        )
        
        # 创建异步任务协程
        coro = self._run_task(task, content, msg)
        
        # 提交到执行器（不等待完成）
        asyncio.create_task(self.executor.submit(task, coro))
        
        # 立即返回提示
        return TaskResult.success(
            f"⏳ 后台任务已启动\n"
            f"任务ID: {task_id}\n"
            f"类型: {self.name}\n"
            f"执行完成后会自动推送结果"
        )
    
    async def _run_task(self, task: BackgroundTask, content: str, msg: Dict[str, Any]):
        """包装 run() 方法，绑定当前任务上下文"""
        self._current_task = task
        try:
            return await self.run(content, msg)
        finally:
            self._current_task = None
    
    @abstractmethod
    async def run(self, content: str, msg: Dict[str, Any]) -> TaskResult:
        """
        子类实现的具体任务逻辑
        
        这是一个异步方法，可以使用 await 执行耗时操作。
        通过 self.report_progress() 上报进度。
        """
        pass
    
    def report_progress(self, progress_or_message, message: str = None):
        """上报任务进度（子类在 run() 中调用）

        支持两种调用方式:
            report_progress("解析中...")
            report_progress(50, "解析中...")
        """
        if message is not None:
            # 双参数: (progress, message)
            progress = progress_or_message
            msg = message
        else:
            # 单参数: (message)
            progress = None
            msg = progress_or_message

        if self._current_task:
            display = f"{progress}% {msg}" if progress is not None else msg
            self._current_task.progress = display
            logger.info(f"[task] {self._current_task.task_id} 进度: {display}")

            # 触发进度事件（通过 executor 的 event_bus）
            if self.executor and self.executor.event_bus:
                asyncio.create_task(self.executor.event_bus.emit("task:progress", {
                    "task_id": self._current_task.task_id,
                    "handler_name": self._current_task.handler_name,
                    "progress": message,
                }, source="task"))
    
    def get_progress(self) -> str:
        """获取当前任务进度"""
        if self._current_task:
            return self._current_task.progress
        return ""
