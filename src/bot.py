import time
import logging
import asyncio
from typing import Dict, Optional

from src.weixin_api import WeixinAPI
from src.tasks.registry import TaskRegistry
from src.tasks.base import TaskResult
from src.webhook import WebhookServer

logger = logging.getLogger(__name__)


class WeixinBot:
    """微信机器人 —— 支持 Webhook 推送的可扩展版本"""
    
    def __init__(
        self,
        api: WeixinAPI,
        registry: TaskRegistry = None,
        webhook: Optional[WebhookServer] = None
    ):
        self.api = api
        self.registry = registry or TaskRegistry()
        self.webhook = webhook
        self.running = False
        self.get_updates_buf = ""
    
    def start(self):
        """启动主循环（同步入口，内部运行事件循环）"""
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            pass
    
    async def _run(self):
        """异步主循环：同时运行消息轮询和 Webhook 消费"""
        self.running = True
        handlers = self.registry.list_handlers()
        
        logger.info("🤖 机器人启动，监听消息...")
        logger.info(f"已注册处理器 ({len(handlers)}): {', '.join(handlers)}")
        
        # 启动 Webhook 服务（如果配置）
        if self.webhook:
            await self.webhook.setup()
        
        # 并发运行两个任务
        tasks = [
            asyncio.create_task(self._poll_loop()),
        ]
        if self.webhook:
            tasks.append(asyncio.create_task(self._webhook_consumer()))
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            if self.webhook:
                await self.webhook.teardown()
    
    async def _poll_loop(self):
        """微信消息长轮询循环"""
        while self.running:
            try:
                # 长轮询获取消息（35秒超时）
                # WeixinAPI.get_updates 是同步方法，在线程池中执行
                result = await asyncio.to_thread(
                    self.api.get_updates,
                    buf=self.get_updates_buf,
                    timeout_ms=35000
                )
                
                # 更新 buf
                if "get_updates_buf" in result:
                    self.get_updates_buf = result["get_updates_buf"]
                
                # 处理消息
                msgs = result.get("msgs", [])
                for msg in msgs:
                    await self._handle_message(msg)
                
            except Exception as e:
                logger.error(f"轮询异常: {e}")
                await asyncio.sleep(5)
    
    async def _webhook_consumer(self):
        """Webhook 消息队列消费者"""
        if not self.webhook:
            return
        
        logger.info("🌐 Webhook 消费者启动")
        
        while self.running:
            try:
                item = await self.webhook.get_next()
                if item is None:
                    continue
                
                to_user = item["to"]
                text = item["text"]
                
                logger.info(f"[webhook] 推送消息 → {to_user}")
                await self._send_text(to_user, text)
                
            except Exception as e:
                logger.error(f"Webhook 消费异常: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, msg: Dict):
        """处理单条消息：提取文本 → 注册表分发 → 发送回复"""
        content = self.api.extract_text_from_message(msg).strip()
        from_user = msg.get("from_user_id", "")
        
        if not content or not from_user:
            return
        
        # 记录用户到 Webhook（用于默认推送目标）
        if self.webhook:
            self.webhook.record_user(from_user)
        
        logger.info(f"📩 [{from_user}] {content}")
        
        # 通过注册表分发任务
        task_result = self.registry.dispatch(content, msg)
        
        if task_result is None:
            await self._send_text(from_user, "⚠️ 暂不支持该指令，输入 help 查看可用功能")
            return
        
        await self._send_result(from_user, task_result)
    
    async def _send_result(self, to: str, result: TaskResult):
        """发送任务结果到用户"""
        if result.error:
            await self._send_text(to, result.text or f"❌ {result.error}")
            return
        
        if result.text:
            await self._send_text(to, result.text)
        
        # TODO: 支持发送图片/文件
    
    async def _send_text(self, to: str, text: str):
        """安全发送文本消息（异步包装）"""
        try:
            logger.info(f"[send] 正在发送消息到 {to}, 长度={len(text)}")
            result = await asyncio.to_thread(self.api.send_text_message, to=to, text=text)
            logger.info(f"[send] 消息发送成功 → {to}")
            return result
        except Exception as e:
            logger.exception(f"[send] 发送失败 → {to}: {e}")
            raise
    
    def stop(self):
        self.running = False
        logger.info("机器人已停止")
