"""
任务处理器模块

提供可扩展的任务处理框架，支持注册自定义任务处理器。
"""

from src.tasks.base import TaskHandler, TaskResult
from src.tasks.registry import TaskRegistry

__all__ = ["TaskHandler", "TaskResult", "TaskRegistry"]
