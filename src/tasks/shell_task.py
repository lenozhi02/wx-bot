"""
Shell 命令执行任务处理器
将原有的 ALLOWED_COMMANDS 逻辑抽象为可扩展的任务处理器
"""

import logging
import subprocess
from typing import Dict, Any, List, Optional

from src.tasks.base import TaskHandler, TaskResult

logger = logging.getLogger(__name__)


class ShellTaskHandler(TaskHandler):
    """
    本地 Shell 命令执行任务处理器
    
    支持两种使用方式：
    1. 精确匹配模式：用户输入 "ls" → 执行预设命令
    2. 前缀匹配模式：用户输入 "cmd ls -la" → 执行白名单内的任意命令
    """
    
    def __init__(
        self,
        allowed_commands: Optional[Dict[str, List[str]]] = None,
        prefix: Optional[str] = None,
        timeout: int = 10,
        max_output_len: int = 1800,
        cwd: str = "."
    ):
        """
        Args:
            allowed_commands: 指令名 → 命令参数列表 的映射，如 {"ls": ["ls", "-la"]}
            prefix: 前缀触发词，如 "cmd"，则 "cmd ls" 触发
            timeout: 命令执行超时秒数
            max_output_len: 输出最大字符数，超出截断
            cwd: 命令执行的工作目录
        """
        self._allowed = allowed_commands or {}
        self._prefix = prefix
        self._timeout = timeout
        self._max_output = max_output_len
        self._cwd = cwd
    
    @property
    def name(self) -> str:
        return "shell"
    
    @property
    def priority(self) -> int:
        return 20  # 较高优先级，精确指令优先响应
    
    def can_handle(self, content: str, msg: Dict[str, Any]) -> bool:
        text = content.strip().lower()
        
        # 精确匹配模式
        if text in self._allowed:
            return True
        
        # 前缀匹配模式
        if self._prefix:
            parts = text.split(None, 1)
            if parts and parts[0] == self._prefix.lower():
                return True
        
        return False
    
    def handle(self, content: str, msg: Dict[str, Any]) -> TaskResult:
        text = content.strip().lower()
        
        # 精确匹配
        if text in self._allowed:
            cmd = self._allowed[text]
            return self._run(cmd, text)
        
        # 前缀匹配：提取实际命令
        if self._prefix:
            parts = text.split(None, 1)
            if len(parts) >= 2:
                sub = parts[1]
                # 检查子命令是否在白名单中
                sub_parts = sub.split()
                sub_key = sub_parts[0] if sub_parts else ""
                if sub_key in self._allowed:
                    cmd = self._allowed[sub_key]
                    return self._run(cmd, sub_key)
                else:
                    return TaskResult.fail(
                        f"命令 `{sub_key}` 不在白名单中。"
                        f"可用命令: {', '.join(self._allowed.keys())}"
                    )
        
        return TaskResult.fail("无法解析命令")
    
    def _run(self, cmd: List[str], display_name: str) -> TaskResult:
        """执行命令并包装结果"""
        try:
            logger.info(f"[shell] 执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                cwd=self._cwd
            )
            
            if result.returncode == 0:
                output = result.stdout
                if not output.strip():
                    return TaskResult.success(f"✅ `{display_name}` 执行成功，但无输出")
                if len(output) > self._max_output:
                    output = output[:self._max_output] + "\n... (结果已截断)"
                return TaskResult.success(f"📋 `{display_name}` 结果:\n```\n{output}\n```")
            else:
                error = result.stderr[:500] if result.stderr else "未知错误"
                return TaskResult.fail(f"`{display_name}` 执行失败:\n{error}")
        
        except subprocess.TimeoutExpired:
            return TaskResult.fail(f"`{display_name}` 执行超时（限制{self._timeout}秒）")
        except FileNotFoundError:
            return TaskResult.fail(f"`{display_name}` 命令不存在")
        except Exception as e:
            return TaskResult.fail(f"`{display_name}` 异常: {str(e)}")
