"""
插件管理器 —— 注册表 + 加载器 + 事件通知
"""

import logging
from typing import Dict, List, Optional

from src.plugins.loader import PluginLoader, PluginMeta
from src.tasks.base import TaskHandler
from src.tasks.registry import TaskRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器：桥接 PluginLoader 和 TaskRegistry"""

    def __init__(self, registry: TaskRegistry, loader: PluginLoader, event_bus=None):
        self.registry = registry
        self.loader = loader
        self.event_bus = event_bus
        self._plugins: Dict[str, PluginMeta] = {}  # id -> meta

    # ---- 加载/卸载 ----

    def load(self, plugin_id: str) -> bool:
        """加载并注册插件"""
        try:
            handler = self.loader.load(plugin_id)
            self.registry.register(handler)
            self._plugins[plugin_id] = self.loader.get_meta(plugin_id)
            self._emit("plugin:loaded", plugin_id)
            return True
        except Exception as e:
            logger.error(f"[plugin] 加载 {plugin_id} 失败: {e}")
            self._emit("plugin:error", {"plugin_id": plugin_id, "error": str(e)})
            return False

    def unload(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id not in self._plugins:
            return False

        self.registry.unregister(plugin_id)
        self.loader.unload(plugin_id)
        del self._plugins[plugin_id]
        self._emit("plugin:unloaded", plugin_id)
        return True

    def reload(self, plugin_id: str) -> bool:
        """重载单个插件"""
        if plugin_id in self._plugins:
            self.unload(plugin_id)
        return self.load(plugin_id)

    def reload_all(self) -> Dict[str, bool]:
        """扫描目录并加载所有插件，返回加载结果"""
        # 先卸载已加载的
        for pid in list(self._plugins.keys()):
            self.unload(pid)

        results = {}
        for meta in self.loader.scan():
            pid = meta.id
            results[pid] = self.load(pid)
        return results

    # ---- 查询 ----

    def list_plugins(self) -> List[dict]:
        """返回所有已注册插件信息"""
        return [
            {
                "id": pid,
                "name": meta.name,
                "version": meta.version,
                "description": meta.description,
                "author": meta.author,
                "priority": meta.priority,
                "handler_class": meta.handler_class,
                "status": "loaded",
            }
            for pid, meta in self._plugins.items()
        ]

    def get_plugin(self, plugin_id: str) -> Optional[dict]:
        meta = self._plugins.get(plugin_id)
        if not meta:
            return None
        return {
            "id": plugin_id,
            "name": meta.name,
            "version": meta.version,
            "description": meta.description,
            "author": meta.author,
            "priority": meta.priority,
            "handler_class": meta.handler_class,
            "status": "loaded",
        }

    # ---- 内部 ----

    def _emit(self, event: str, data):
        if self.event_bus:
            try:
                import asyncio
                import inspect
                result = self.event_bus.emit(event, data)
                if inspect.isawaitable(result):
                    asyncio.get_event_loop().call_soon(asyncio.create_task, result)
            except Exception as e:
                logger.error(f"[plugin] 事件发送失败: {e}")
