"""
网络搜索任务处理器（示例扩展）

当前为占位实现，展示如何接入搜索能力。
实际可接入：
- 百度/必应/搜狗等搜索引擎
- 内部知识库检索
- 医院官网新闻检索（利用现有 skills）
"""

import logging
from typing import Dict, Any

from src.tasks.base import TaskHandler, TaskResult

logger = logging.getLogger(__name__)


class SearchTaskHandler(TaskHandler):
    """
    网络搜索任务处理器
    
    触发方式：
    - "搜索 <关键词>"
    - "search <关键词>"
    """
    
    TRIGGERS = ["搜索", "search", "查找", "查"]
    
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
    
    @property
    def name(self) -> str:
        return "search"
    
    @property
    def priority(self) -> int:
        return 30
    
    def can_handle(self, content: str, msg: Dict[str, Any]) -> bool:
        text = content.strip().lower()
        for trigger in self.TRIGGERS:
            if text.startswith(trigger.lower()):
                return True
        return False
    
    def handle(self, content: str, msg: Dict[str, Any]) -> TaskResult:
        text = content.strip()
        
        # 提取关键词
        keyword = self._extract_keyword(text)
        if not keyword:
            return TaskResult.fail("请提供搜索关键词，例如：搜索 人工智能")
        
        logger.info(f"[search] 搜索关键词: {keyword}")
        
        # TODO: 接入实际搜索引擎或内部检索系统
        # 以下为占位实现
        return TaskResult.success(
            f"🔍 搜索「{keyword}」\n\n"
            f"（此为占位回复，请接入实际搜索接口）\n\n"
            f"可接入的搜索源：\n"
            f"• 百度/必应/搜狗等通用搜索\n"
            f"• 医院官网新闻检索（skills）\n"
            f"• 内部知识库/文档检索"
        )
    
    def _extract_keyword(self, text: str) -> str:
        """从触发词后提取关键词"""
        lower = text.lower()
        for trigger in self.TRIGGERS:
            if lower.startswith(trigger.lower()):
                keyword = text[len(trigger):].strip()
                return keyword
        return ""
