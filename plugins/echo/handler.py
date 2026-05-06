"""
Echo Plugin — 复读消息示例
"""

from src.tasks.base import TaskHandler, TaskResult


class EchoHandler(TaskHandler):
    """复读机"""
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
