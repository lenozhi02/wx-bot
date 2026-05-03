"""
帮助指令任务处理器

响应 "help" / "帮助" / "?" 等指令，列出所有可用功能
"""

from typing import Dict, Any

from src.tasks.base import TaskHandler, TaskResult


class HelpTaskHandler(TaskHandler):
    """
    帮助信息任务处理器
    
    触发方式：help / 帮助 / ? / 菜单
    """
    
    TRIGGERS = ["help", "帮助", "?", "菜单", "menu"]
    
    def __init__(self, bot_name: str = "微信机器人"):
        self.bot_name = bot_name
        self._custom_help: str = ""
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def priority(self) -> int:
        return 5  # 最高优先级，帮助指令优先响应
    
    def set_help_text(self, text: str):
        """动态设置帮助文本，可在注册其他处理器后更新"""
        self._custom_help = text
    
    def can_handle(self, content: str, msg: Dict[str, Any]) -> bool:
        text = content.strip().lower()
        return text in [t.lower() for t in self.TRIGGERS]
    
    def handle(self, content: str, msg: Dict[str, Any]) -> TaskResult:
        help_text = self._build_help_text()
        return TaskResult.success(help_text)
    
    def _build_help_text(self) -> str:
        lines = [
            f"📖 {self.bot_name} 使用指南",
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            "【系统命令】",
            "• help / 帮助 / ?  — 显示本帮助",
            "",
            "【系统巡检】",
            "• status / 状态 / health  — 服务器健康巡检报告",
            "",
            "【搜索功能】",
            "• 搜索 <关键词>  — 网络搜索（示例）",
            "",
            "【AI 对话】",
            "• AI <问题>  — 与 AI 对话（示例）",
            "• 或直接发送任意消息，AI 将兜底回复",
            "",
        ]
        
        if self._custom_help:
            lines.append("【扩展功能】")
            lines.append(self._custom_help)
            lines.append("")
        
        lines.append("━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
