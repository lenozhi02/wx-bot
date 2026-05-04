"""
百度搜索任务处理器

执行 inseas_search_chrome.py 脚本，支持参数从微信传入。

触发方式：
  百度 机构名 日期范围 邮箱

示例：
  百度 stluciabj 2026-04-29,2026-04-30 9089120@qq.com
  百度 stluciabj 2026-04-29
  百度 stluciabj
"""

import asyncio
import logging
import subprocess
import os
from typing import Dict, Any

from src.tasks.background import BackgroundTaskHandler, TaskExecutor
from src.tasks.base import TaskResult

logger = logging.getLogger(__name__)

# 脚本路径
SCRIPT_PATH = "/root/.hermes/skills/openclaw-imports/keyword-search/scripts/inseas_search_chrome.py"
SCRIPT_CWD = "/root/.hermes/skills/openclaw-imports/keyword-search/scripts"

# 默认参数
DEFAULT_EMAIL = "9089120@qq.com"
DEFAULT_DATE = None  # 脚本会使用默认日期

# 超时控制：40分钟
TASK_TIMEOUT = 40 * 60  # 2400秒


class BaiduSearchTaskHandler(BackgroundTaskHandler):
    """
    百度搜索任务处理器
    
    触发方式：百度 机构名 日期范围 邮箱
    """
    
    TRIGGER = "百度"
    
    def __init__(self, executor: TaskExecutor):
        super().__init__(executor)
    
    @property
    def name(self) -> str:
        return "baidu_search"
    
    @property
    def priority(self) -> int:
        return 22  # 在 status(10) 之后，long_task(25) 之前
    
    def can_handle(self, content: str, msg: Dict[str, Any]) -> bool:
        text = content.strip().lower()
        return text.startswith(self.TRIGGER.lower())
    
    async def run(self, content: str, msg: Dict[str, Any]) -> TaskResult:
        """执行搜索脚本"""
        # 解析参数
        args = self._parse_args(content)
        if isinstance(args, TaskResult):
            return args  # 解析失败，返回错误提示
        
        hospital, date, email = args
        
        logger.info(f"[{self.name}] 开始执行搜索: hospital={hospital}, date={date}, email={email}")
        self.report_progress("正在启动 Chrome 搜索...")
        
        # 构建命令
        cmd = [
            "python3", SCRIPT_PATH,
            "--hospital", hospital,
            "--keep-files",
        ]
        if date:
            cmd.extend(["--date", date])
        if email:
            cmd.extend(["--email", email])
        
        logger.info(f"[{self.name}] 执行命令: {' '.join(cmd)}")
        
        # 执行脚本（40分钟超时）
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=SCRIPT_CWD,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            self.report_progress("Chrome 搜索进行中，请耐心等待...")
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=TASK_TIMEOUT
            )
            
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            if process.returncode == 0:
                logger.info(f"[{self.name}] 搜索完成")
                self.report_progress("搜索完成，正在整理结果...")
                
                # 提取关键输出信息
                summary = self._extract_summary(stdout_text, stderr_text)
                
                return TaskResult.success(
                    f"✅ 百度搜索任务完成\n"
                    f"机构: {hospital}\n"
                    f"日期: {date or '默认'}\n"
                    f"邮箱: {email or '默认'}\n"
                    f"\n{summary}\n"
                    f"报告已发送至邮箱"
                )
            else:
                error = stderr_text[:500] if stderr_text else f"返回码: {process.returncode}"
                logger.error(f"[{self.name}] 搜索失败: {error}")
                return TaskResult.fail(f"搜索脚本执行失败:\n{error}")
        
        except asyncio.TimeoutError:
            logger.error(f"[{self.name}] 搜索超时（{TASK_TIMEOUT}秒）")
            # 尝试终止进程
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass
            return TaskResult.fail(f"⏱️ 搜索任务超时（限制{TASK_TIMEOUT//60}分钟）")
        
        except Exception as e:
            logger.exception(f"[{self.name}] 搜索异常")
            return TaskResult.fail(f"搜索任务异常: {str(e)}")
    
    def _parse_args(self, content: str):
        """
        解析微信消息参数
        
        格式: 百度 机构名 [日期范围] [邮箱]
        
        返回: (hospital, date, email) 或 TaskResult(错误提示)
        """
        parts = content.strip().split()
        
        if len(parts) < 2:
            return TaskResult.success(
                "📖 百度搜索用法:\n"
                "百度 机构名 [日期范围] [邮箱]\n\n"
                "示例:\n"
                "• 百度 stluciabj\n"
                "• 百度 stluciabj 2026-04-29,2026-04-30\n"
                "• 百度 stluciabj 2026-04-29,2026-04-30 9089120@qq.com\n\n"
                "支持的机构: stluciabj, zju4h, huashan, pumch, ..."
            )
        
        hospital = parts[1]
        date = None
        email = None
        
        # 解析可选参数（日期和邮箱）
        for i in range(2, len(parts)):
            part = parts[i]
            # 判断是否是日期格式 (YYYY-MM-DD 或 YYYY-MM-DD,YYYY-MM-DD)
            if self._is_date_format(part):
                date = part
            # 判断是否是邮箱
            elif "@" in part:
                email = part
        
        # 使用默认值
        if not email:
            email = DEFAULT_EMAIL
        
        return hospital, date, email
    
    @staticmethod
    def _is_date_format(s: str) -> bool:
        """判断字符串是否是日期格式"""
        # 支持: 2026-04-29 或 2026-04-29,2026-04-30
        parts = s.split(",")
        for p in parts:
            p = p.strip()
            if len(p) != 10 or p[4] != '-' or p[7] != '-':
                return False
            try:
                int(p[:4])
                int(p[5:7])
                int(p[8:10])
            except ValueError:
                return False
        return True
    
    @staticmethod
    def _extract_summary(stdout: str, stderr: str) -> str:
        """从脚本输出中提取关键信息"""
        lines = []
        
        # 查找关键输出
        for line in stdout.split('\n'):
            line = line.strip()
            if any(kw in line for kw in ['找到', '结果', '完成', '发送', '邮件', '报告']):
                lines.append(line)
        
        if lines:
            return "执行摘要:\n" + '\n'.join(f"  • {l}" for l in lines[-5:])
        
        return "脚本执行完成"
