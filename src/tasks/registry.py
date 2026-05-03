"""
任务注册表 —— 管理所有任务处理器
"""

import logging
from typing import List, Dict, Any, Optional

from src.tasks.base import TaskHandler, TaskResult

logger = logging.getLogger(__name__)


class TaskRegistry:
    """任务处理器注册表，支持优先级排序和自动分发"""
    
    def __init__(self):
        self._handlers: List[TaskHandler] = []
    
    def register(self, handler: TaskHandler) -> "TaskRegistry":
        """
        注册一个任务处理器。
        自动按优先级排序（数值小的在前）。
        """
        if not isinstance(handler, TaskHandler):
            raise TypeError(f"handler must be instance of TaskHandler, got {type(handler)}")
        
        self._handlers.append(handler)
        self._handlers.sort(key=lambda h: h.priority)
        logger.info(f"[registry] 注册任务处理器: {handler.name} (priority={handler.priority})")
        return self
    
    def register_many(self, *handlers: TaskHandler) -> "TaskRegistry":
        """批量注册多个处理器"""
        for handler in handlers:
            self.register(handler)
        return self
    
    def unregister(self, name: str) -> bool:
        """按名称注销处理器，返回是否成功"""
        for i, h in enumerate(self._handlers):
            if h.name == name:
                self._handlers.pop(i)
                logger.info(f"[registry] 注销任务处理器: {name}")
                return True
        return False
    
    def dispatch(self, content: str, msg: Dict[str, Any]) -> Optional[TaskResult]:
        """
        按优先级遍历处理器，找到第一个能处理的并执行。
        
        Args:
            content: 消息纯文本内容
            msg: 原始消息字典
        
        Returns:
            如果找到匹配的处理器，返回 TaskResult；否则返回 None
        """
        for handler in self._handlers:
            try:
                if handler.can_handle(content, msg):
                    logger.info(f"[registry] 分发到处理器: {handler.name}")
                    return handler.handle(content, msg)
            except Exception as e:
                logger.error(f"[registry] 处理器 {handler.name} 判断/执行异常: {e}")
                continue
        
        return None
    
    def list_handlers(self) -> List[str]:
        """返回所有已注册处理器的名称列表（按优先级排序）"""
        return [h.name for h in self._handlers]
