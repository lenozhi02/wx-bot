"""
服务器状态巡检任务处理器

微信端发送 "status" 指令，后端汇总返回三大命令的输出：
1. df -h      — 磁盘空间
2. ls -la     — 当前目录文件
3. ps aux     — 进程状态

同时通过 psutil 补充系统概览（CPU、内存、网络、运行时长）。
"""

import logging
import subprocess
import time
import socket
from typing import Dict, Any, List
from datetime import timedelta

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from src.tasks.base import TaskHandler, TaskResult

logger = logging.getLogger(__name__)


class StatusTaskHandler(TaskHandler):
    """
    服务器状态巡检任务处理器

    触发方式：status / 状态 / health / 巡检
    """

    TRIGGERS = ["status", "状态", "health", "巡检"]

    # 三大核心命令
    COMMANDS = {
        "df": ["df", "-h"],
        "ls": ["ls", "-la"],
        "ps": ["ps", "aux"],
    }

    def __init__(self, cmd_timeout: int = 10, max_output_lines: int = 50):
        """
        Args:
            cmd_timeout: 命令执行超时（秒）
            max_output_lines: 单命令输出最大行数，超出截断
        """
        self._cmd_timeout = cmd_timeout
        self._max_lines = max_output_lines

    @property
    def name(self) -> str:
        return "status"

    @property
    def priority(self) -> int:
        return 10

    def can_handle(self, content: str, msg: Dict[str, Any]) -> bool:
        text = content.strip().lower()
        return text in [t.lower() for t in self.TRIGGERS]

    def handle(self, content: str, msg: Dict[str, Any]) -> TaskResult:
        try:
            report = self._build_report()
            return TaskResult.success(report)
        except Exception as e:
            logger.exception("[status] 巡检异常")
            return TaskResult.fail(f"巡检失败: {str(e)}")

    def _build_report(self) -> str:
        """构建完整巡检报告"""
        lines = []
        hostname = socket.gethostname()

        lines.append(f"🖥️ 服务器巡检报告")
        lines.append(f"主机: {hostname}")
        lines.append(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # ── 三大命令输出 ──
        for label, title, emoji in [
            ("df", "💿 磁盘空间 (df -h)", "💿"),
            ("ls", "📁 当前目录 (ls -la)", "📁"),
            ("ps", "⚙️ 进程状态 (ps aux)", "⚙️"),
        ]:
            lines.append(self._run_command_section(label, title))
            lines.append("")

        # ── psutil 系统概览（如有）──
        if PSUTIL_AVAILABLE:
            lines.append(self._system_overview())

        return "\n".join(lines)

    def _run_command_section(self, label: str, title: str) -> str:
        """执行单个命令并格式化输出"""
        cmd = self.COMMANDS[label]
        lines = [title]
        lines.append("─" * 28)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._cmd_timeout,
                cwd=".",
            )

            if result.returncode == 0:
                output = result.stdout.rstrip("\n")
                if not output:
                    lines.append("(无输出)")
                else:
                    # 截断过长输出
                    output_lines = output.split("\n")
                    if len(output_lines) > self._max_lines:
                        output_lines = output_lines[:self._max_lines]
                        output_lines.append(f"... ({len(output_lines)}+ 行，已截断)")
                    lines.extend(output_lines)
            else:
                error = result.stderr[:200] if result.stderr else "未知错误"
                lines.append(f"❌ 执行失败: {error}")

        except subprocess.TimeoutExpired:
            lines.append(f"⏱️ 执行超时（限制 {self._cmd_timeout} 秒）")
        except FileNotFoundError:
            lines.append(f"🔧 命令不存在: {cmd[0]}")
        except Exception as e:
            lines.append(f"💥 异常: {str(e)}")

        return "\n".join(lines)

    def _system_overview(self) -> str:
        """psutil 系统概览（精简版）"""
        lines = ["📊 系统概览"]
        lines.append("─" * 28)

        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count()
            lines.append(f"CPU: {cpu_count} 核 | 使用率 {cpu_percent:.1f}%")

            # Memory
            mem = psutil.virtual_memory()
            lines.append(
                f"内存: {self._bytes_to_human(mem.used)} / "
                f"{self._bytes_to_human(mem.total)} ({mem.percent:.1f}%)"
            )

            # Load
            try:
                load1, _, _ = psutil.getloadavg()
                lines.append(f"负载: {load1:.2f} (1m)")
            except (AttributeError, OSError):
                pass

            # Network
            net = psutil.net_io_counters()
            lines.append(
                f"网络: ↑{self._bytes_to_human(net.bytes_sent)} "
                f"↓{self._bytes_to_human(net.bytes_recv)}"
            )

            # Uptime
            uptime = time.time() - psutil.boot_time()
            uptime_str = str(timedelta(seconds=int(uptime)))
            lines.append(f"运行: {uptime_str}")

            # Processes
            lines.append(f"进程: {len(psutil.pids())}")

        except Exception as e:
            lines.append(f"获取概览失败: {e}")

        return "\n".join(lines)

    @staticmethod
    def _bytes_to_human(n: int) -> str:
        """字节转人类可读"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(n) < 1024.0:
                return f"{n:.1f}{unit}"
            n /= 1024.0
        return f"{n:.1f}PB"
