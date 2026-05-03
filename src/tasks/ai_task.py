"""
AI 对话任务处理器（示例扩展 / 兜底回复）

当前为占位实现，展示如何接入 AI 能力。
实际可接入：
- OpenAI / Claude / Kimi 等大模型 API
- 本地部署的 LLM
"""

import logging
from typing import Dict, Any

from src.tasks.base import TaskHandler, TaskResult

logger = logging.getLogger(__name__)


class AITaskHandler(TaskHandler):
    """
    AI 对话任务处理器
    
    触发方式：
    - "AI <问题>" / "ai <问题>"
    - 作为兜底处理器，任何未被其他处理器处理的消息都会进入 AI
    
    使用建议：
    - 如果希望 AI 作为兜底，priority 设为 100（最低）
    - 如果希望 AI 仅在特定前缀时触发，priority 可设为 40，can_handle 检查前缀
    """
    
    def __init__(self, prefix: str = "AI", fallback: bool = True):
        """
        Args:
            prefix: 触发前缀，如 "AI"
            fallback: 是否作为兜底处理器（任何消息都处理）
        """
        self._prefix = prefix
        self._fallback = fallback
    
    @property
    def name(self) -> str:
        return "ai"
    
    @property
    def priority(self) -> int:
        return 100  # 最低优先级，作为兜底
    
    def can_handle(self, content: str, msg: Dict[str, Any]) -> bool:
        # 如果启用兜底模式，接收所有消息
        if self._fallback:
            return True
        
        # 否则仅在前缀匹配时处理
        text = content.strip().lower()
        return text.startswith(self._prefix.lower())
    
    def handle(self, content: str, msg: Dict[str, Any]) -> TaskResult:
        # 去除前缀（如果有的话）
        question = content.strip()
        lower = question.lower()
        if lower.startswith(self._prefix.lower()):
            question = question[len(self._prefix):].strip()
        
        logger.info(f"[ai] 处理问题: {question[:50]}...")
        
        # TODO: 接入实际大模型 API
        # 以下为占位实现
        return TaskResult.success(
            f"🤖 AI 助手（占位模式）\n\n"
            f"您的问题：{question}\n\n"
            f"（请接入实际大模型 API 以获取真实回复）\n\n"
            f"可接入的模型：\n"
            f"• OpenAI GPT-4 / GPT-3.5\n"
            f"• Anthropic Claude\n"
            f"• 月之暗面 Kimi\n"
            f"• 本地部署的 LLM"
        )
