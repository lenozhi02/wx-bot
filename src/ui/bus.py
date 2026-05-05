"""
事件总线 —— UI 层与核心层的通信桥梁

支持异步事件发布/订阅，低耦合设计。
现有代码通过注入 event_bus 实例触发事件，不传则不触发。
"""

import asyncio
import logging
import time
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BusEvent:
    """标准化事件对象"""
    event: str           # 事件名称，如 "bot:message_received"
    timestamp: float     # 事件时间戳
    data: Dict[str, Any] # 事件数据
    source: str = ""     # 事件来源模块


class EventBus:
    """
    异步内存事件总线
    
    使用方式：
        bus = EventBus()
        
        # 订阅事件
        bus.on("task:completed", lambda e: print(e.data))
        
        # 发布事件
        await bus.emit("task:completed", {"task_id": "xxx", "status": "ok"})
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[BusEvent], Any]]] = {}
        self._history: List[BusEvent] = []
        self._max_history = 1000
        self._lock = asyncio.Lock()
    
    def on(self, event: str, callback: Callable[[BusEvent], Any]):
        """
        订阅事件
        
        Args:
            event: 事件名称，支持通配符 "*" 订阅所有事件
            callback: 回调函数，接收 BusEvent 对象
        """
        self._subscribers.setdefault(event, []).append(callback)
        logger.debug(f"[bus] 订阅事件: {event}, 当前订阅数: {len(self._subscribers[event])}")
    
    def off(self, event: str, callback: Callable[[BusEvent], Any]):
        """取消订阅"""
        if event in self._subscribers:
            try:
                self._subscribers[event].remove(callback)
            except ValueError:
                pass
    
    async def emit(self, event: str, data: Dict[str, Any], source: str = ""):
        """
        发布事件（异步，不阻塞调用方）
        
        所有回调通过 asyncio.create_task 并发执行，
        单个回调失败不影响其他回调。
        """
        bus_event = BusEvent(
            event=event,
            timestamp=time.time(),
            data=data,
            source=source,
        )
        
        # 保存到历史
        self._history.append(bus_event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        # 收集匹配的回调
        callbacks = []
        
        # 精确匹配
        if event in self._subscribers:
            callbacks.extend(self._subscribers[event])
        
        # 通配符匹配
        if "*" in self._subscribers:
            callbacks.extend(self._subscribers["*"])
        
        if not callbacks:
            return
        
        # 并发执行所有回调，容错处理
        tasks = []
        for cb in callbacks:
            tasks.append(asyncio.create_task(
                self._safe_callback(cb, bus_event),
                name=f"bus_cb_{event}_{id(cb)}"
            ))
        
        # 不等待回调完成（fire-and-forget）
        # 但需要捕获异常防止未处理的 Task 异常
        for task in tasks:
            task.add_done_callback(self._on_task_done)
    
    async def _safe_callback(self, callback: Callable, event: BusEvent):
        """安全执行回调，捕获异常"""
        try:
            result = callback(event)
            # 支持异步回调
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            logger.exception(f"[bus] 事件回调异常: {event.event}")
    
    def _on_task_done(self, task: asyncio.Task):
        """Task 完成回调，捕获未处理异常"""
        try:
            task.result()
        except Exception:
            pass  # 异常已在 _safe_callback 中记录
    
    def get_history(self, event_filter: Optional[str] = None, limit: int = 100) -> List[BusEvent]:
        """
        获取事件历史
        
        Args:
            event_filter: 事件名称过滤，None 返回所有
            limit: 返回条数
        """
        events = self._history
        if event_filter:
            events = [e for e in events if e.event == event_filter]
        return events[-limit:]
    
    def get_subscriber_counts(self) -> Dict[str, int]:
        """获取各事件的订阅数"""
        return {k: len(v) for k, v in self._subscribers.items()}
    
    def clear_history(self):
        """清空历史记录"""
        self._history.clear()


# 全局默认事件总线实例（可选使用）
_default_bus: Optional[EventBus] = None


def get_default_bus() -> EventBus:
    """获取全局默认事件总线（懒加载）"""
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus
