"""
长时间后台任务示例

模拟耗时操作，展示后台任务的使用方式。
"""

import asyncio
import logging

from src.tasks.background import BackgroundTaskHandler, TaskExecutor
from src.tasks.base import TaskResult

logger = logging.getLogger(__name__)


class LongRunningTaskHandler(BackgroundTaskHandler):
    """
    长时间运行任务示例
    
    触发方式：长任务 / longtask / 后台任务
    
    模拟一个耗时 10 秒的任务，每 2 秒上报一次进度。
    """
    
    TRIGGERS = ["长任务", "longtask", "后台任务"]
    
    def __init__(self, executor: TaskExecutor):
        super().__init__(executor)
    
    @property
    def name(self) -> str:
        return "long_task"
    
    @property
    def priority(self) -> int:
        return 25  # 在 status(10) 之后，search(30) 之前
    
    def can_handle(self, content: str, msg: dict) -> bool:
        return content.strip().lower() in [t.lower() for t in self.TRIGGERS]
    
    async def run(self, content: str, msg: dict) -> TaskResult:
        """执行耗时任务"""
        logger.info(f"[{self.name}] 开始执行任务...")
        
        # 模拟分阶段耗时操作
        stages = [
            ("正在初始化...", 2),
            ("正在处理数据（1/3）...", 2),
            ("正在处理数据（2/3）...", 2),
            ("正在处理数据（3/3）...", 2),
            ("正在生成报告...", 2),
        ]
        
        results = []
        for stage_name, delay in stages:
            self.report_progress(stage_name)
            await asyncio.sleep(delay)  # 模拟耗时操作
            results.append(f"✅ {stage_name} 完成")
        
        # 汇总结果
        report = "📋 后台任务执行报告\n"
        report += "=" * 20 + "\n"
        report += "\n".join(results)
        report += f"\n\n总计耗时: {len(stages) * delay} 秒"
        
        return TaskResult.success(report)


class DataSyncTaskHandler(BackgroundTaskHandler):
    """
    数据同步任务示例
    
    触发方式：同步 / sync / 数据同步
    
    模拟从多个数据源拉取数据并汇总。
    """
    
    TRIGGERS = ["同步", "sync", "数据同步"]
    
    def __init__(self, executor: TaskExecutor):
        super().__init__(executor)
    
    @property
    def name(self) -> str:
        return "data_sync"
    
    @property
    def priority(self) -> int:
        return 25
    
    def can_handle(self, content: str, msg: dict) -> bool:
        return content.strip().lower() in [t.lower() for t in self.TRIGGERS]
    
    async def run(self, content: str, msg: dict) -> TaskResult:
        """模拟数据同步"""
        sources = ["数据库A", "数据库B", "API接口C", "文件服务器D"]
        synced = []
        failed = []
        
        for source in sources:
            self.report_progress(f"正在同步 {source}...")
            await asyncio.sleep(1.5)  # 模拟网络请求
            
            # 模拟随机失败
            import random
            if random.random() > 0.2:
                synced.append(source)
            else:
                failed.append(source)
        
        lines = ["🔄 数据同步完成"]
        lines.append(f"成功: {len(synced)}/{len(sources)}")
        if synced:
            lines.append(f"✅ {', '.join(synced)}")
        if failed:
            lines.append(f"❌ 失败: {', '.join(failed)}")
        
        return TaskResult.success("\n".join(lines))
