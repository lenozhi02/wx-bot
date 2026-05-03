"""
任务处理器抽象基类与通用数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class TaskResult:
    """任务执行结果"""
    text: str = ""
    images: list = field(default_factory=list)
    files: list = field(default_factory=list)
    error: Optional[str] = None
    
    def is_empty(self) -> bool:
        return not self.text and not self.images and not self.files
    
    @classmethod
    def success(cls, text: str, **kwargs) -> "TaskResult":
        return cls(text=text, **kwargs)
    
    @classmethod
    def fail(cls, error: str) -> "TaskResult":
        return cls(error=error, text=f"❌ {error}")


class TaskHandler(ABC):
    """任务处理器抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """任务名称，用于日志和调试"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        处理优先级，数值越小优先级越高。
        建议范围：0-100，默认 50。
        高优先级（如精确匹配指令）可设为 10-20，
        低优先级（如 AI 兜底回复）可设为 90-100。
        """
        pass
    
    @abstractmethod
    def can_handle(self, content: str, msg: Dict[str, Any]) -> bool:
        """
        判断是否可处理该消息。
        
        Args:
            content: 提取后的纯文本消息内容（保留原始大小写）
            msg: 原始消息字典
        
        Returns:
            True 表示可以处理，False 表示跳过
        """
        pass
    
    @abstractmethod
    def handle(self, content: str, msg: Dict[str, Any]) -> TaskResult:
        """
        执行任务并返回结果。
        
        Args:
            content: 提取后的纯文本消息内容（保留原始大小写）
            msg: 原始消息字典
        
        Returns:
            TaskResult 包含执行结果
        """
        pass
