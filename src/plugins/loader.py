"""
插件加载器 —— 运行时动态发现和加载插件

使用 importlib 动态导入，不依赖 sys.path 修改。
"""

import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.tasks.base import TaskHandler
from src.tasks.background import BackgroundTaskHandler

logger = logging.getLogger(__name__)

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "plugins")


@dataclass
class PluginMeta:
    """插件元数据"""
    id: str
    name: str
    version: str
    description: str
    author: str
    priority: int
    handler_class: str
    handler_file: str

    @classmethod
    def from_manifest(cls, manifest: dict) -> "PluginMeta":
        return cls(
            id=manifest.get("id", ""),
            name=manifest.get("name", ""),
            version=manifest.get("version", "0.0.0"),
            description=manifest.get("description", ""),
            author=manifest.get("author", ""),
            priority=manifest.get("priority", 50),
            handler_class=manifest.get("handler_class", ""),
            handler_file=manifest.get("handler_file", "handler.py"),
        )


class PluginLoader:
    """插件加载器"""

    def __init__(self, executor=None):
        self.executor = executor
        self._loaded: Dict[str, PluginMeta] = {}

    def scan(self) -> List[PluginMeta]:
        """扫描插件目录，返回所有可加载的插件元数据（不实际加载）"""
        result = []
        plugin_dir = os.path.abspath(PLUGIN_DIR)

        if not os.path.isdir(plugin_dir):
            logger.warning(f"[plugin] 插件目录不存在: {plugin_dir}")
            return result

        for entry in os.scandir(plugin_dir):
            if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
                continue
            manifest = self._read_manifest(entry.path)
            if manifest:
                result.append(PluginMeta.from_manifest(manifest))
            else:
                logger.debug(f"[plugin] 跳过无 manifest 的目录: {entry.name}")

        logger.info(f"[plugin] 扫描到 {len(result)} 个插件")
        return result

    def load(self, plugin_id: str) -> Optional[TaskHandler]:
        """加载指定插件，返回实例化的 handler"""
        plugin_path = os.path.join(os.path.abspath(PLUGIN_DIR), plugin_id)
        manifest_dict = self._read_manifest(plugin_path)
        if not manifest_dict:
            raise ValueError(f"插件 {plugin_id} 的 manifest.json 不存在或无效")

        manifest = PluginMeta.from_manifest(manifest_dict)

        # 动态导入 handler 模块
        handler_file = manifest.handler_file
        module_path = os.path.join(plugin_path, handler_file)

        if not os.path.exists(module_path):
            raise ValueError(f"插件 {plugin_id} 的 handler 文件不存在: {handler_file}")

        module_name = f"__wxbot_plugin_{plugin_id}"
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if not spec or not spec.loader:
                raise ValueError(f"无法创建模块 spec: {module_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as e:
            # 清理失败的模块缓存
            if module_name in sys.modules:
                del sys.modules[module_name]
            raise ValueError(f"导入插件 {plugin_id} 失败: {e}")

        # 获取 handler 类并实例化
        class_name = manifest.handler_class
        if not hasattr(module, class_name):
            raise ValueError(f"插件 {plugin_id} 中找不到类 {class_name}")

        handler_class = getattr(module, class_name)

        # 后台任务需要注入 executor
        try:
            if issubclass(handler_class, BackgroundTaskHandler):
                if self.executor is None:
                    raise ValueError(f"插件 {plugin_id} 是后台任务，但 executor 未提供")
                instance = handler_class(self.executor)
            else:
                instance = handler_class()
        except Exception as e:
            raise ValueError(f"实例化插件 {plugin_id} 的 handler 失败: {e}")

        if not isinstance(instance, TaskHandler):
            raise TypeError(f"插件 {plugin_id} 的 handler 必须是 TaskHandler 子类")

        self._loaded[plugin_id] = manifest
        logger.info(f"[plugin] 加载插件: {plugin_id} → handler={instance.name} priority={instance.priority}")
        return instance

    def unload(self, plugin_id: str) -> bool:
        """卸载插件，清理 sys.modules 中的缓存"""
        if plugin_id not in self._loaded:
            return False

        module_name = f"__wxbot_plugin_{plugin_id}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        del self._loaded[plugin_id]
        logger.info(f"[plugin] 卸载插件: {plugin_id}")
        return True

    def get_meta(self, plugin_id: str) -> Optional[PluginMeta]:
        """获取已加载插件的元数据"""
        return self._loaded.get(plugin_id)

    def _read_manifest(self, plugin_path: str) -> Optional[dict]:
        """读取插件的 manifest.json"""
        manifest_file = os.path.join(plugin_path, "manifest.json")
        if not os.path.exists(manifest_file):
            return None
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"[plugin] 读取 manifest 失败 {manifest_file}: {e}")
            return None
