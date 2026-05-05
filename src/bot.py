import time
import logging
import asyncio
from typing import Dict, Optional

from src.weixin_api import WeixinAPI
from src.tasks.registry import TaskRegistry
from src.tasks.base import TaskResult
from src.tasks.background import TaskExecutor, BackgroundTask
from src.webhook import WebhookServer
from src.ui.bus import EventBus

logger = logging.getLogger(__name__)


class WeixinBot:
    """微信机器人 —— 支持后台任务和 Webhook 推送的可扩展版本"""
    
    def __init__(
        self,
        api: WeixinAPI,
        registry: TaskRegistry = None,
        webhook: Optional[WebhookServer] = None,
        executor: Optional[TaskExecutor] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.api = api
        self.registry = registry or TaskRegistry()
        self.webhook = webhook
        self.executor = executor or TaskExecutor(max_workers=3)
        self.event_bus = event_bus
        self.running = False
        self.get_updates_buf = ""
        
        # 设置任务完成回调
        self.executor.set_result_callback(self._on_task_complete)
        
        # 注册任务事件监听
        if self.event_bus:
            self._register_task_events()
    
    def start(self):
        """启动主循环（同步入口，内部运行事件循环）"""
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            pass
    
    async def _run(self):
        """异步主循环：同时运行消息轮询、Webhook 消费、后台任务执行器"""
        self.running = True
        handlers = self.registry.list_handlers()
        
        logger.info("🤖 机器人启动，监听消息...")
        logger.info(f"已注册处理器 ({len(handlers)}): {', '.join(handlers)}")
        
        # 启动 Webhook 服务（如果配置）
        if self.webhook:
            await self.webhook.setup()
        
        # 并发运行所有任务
        tasks = [
            asyncio.create_task(self._poll_loop()),
            asyncio.create_task(self._result_consumer()),
            asyncio.create_task(self.executor.start()),
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
        connected = False
        while self.running:
            try:
                result = await asyncio.to_thread(
                    self.api.get_updates,
                    buf=self.get_updates_buf,
                    timeout_ms=35000
                )
                
                # 连接状态变更事件
                if not connected and self.event_bus:
                    connected = True
                    await self.event_bus.emit("bot:connected", {
                        "account_id": getattr(self.api, "account_id", ""),
                    }, source="bot")
                
                if "get_updates_buf" in result:
                    self.get_updates_buf = result["get_updates_buf"]
                
                msgs = result.get("msgs", [])
                for msg in msgs:
                    await self._handle_message(msg)
                
            except Exception as e:
                logger.error(f"轮询异常: {e}")
                if connected and self.event_bus:
                    connected = False
                    await self.event_bus.emit("bot:disconnected", {
                        "error": str(e),
                    }, source="bot")
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
                context_token = item.get("context_token")
                
                logger.info(f"[webhook] 从队列取出消息 → {to_user}: {text[:50]}... (context_token={context_token})")
                
                # 触发 Webhook 投递事件
                if self.event_bus:
                    await self.event_bus.emit("webhook:delivered", {
                        "to_user": to_user,
                        "text_preview": text[:100],
                        "context_token": context_token,
                    }, source="webhook")
                
                await self._send_text(to_user, text, context_token=context_token)
                
            except Exception:
                logger.exception("[webhook] 消费异常，1秒后重试")
                await asyncio.sleep(1)
    
    async def _result_consumer(self):
        """后台任务结果消费者（备用，通过回调已处理大部分情况）"""
        logger.info("📬 任务结果消费者启动")
        
        while self.running:
            try:
                task = await asyncio.wait_for(self.executor.result_queue.get(), timeout=2.0)
                # 回调已处理推送，这里仅做日志记录
                logger.info(f"[result] 任务 {task.task_id} 结果已消费 (status={task.status.value})")
                
            except asyncio.TimeoutError:
                continue
            except Exception:
                logger.exception("[result] 结果消费异常")
    
    def _register_task_events(self):
        """注册任务事件监听器"""
        async def on_task_event(event):
            # 将任务事件透传到 UI 层
            pass  # 事件已在 executor 中发布
        
        self.event_bus.on("task:*", on_task_event)
    
    async def _on_task_complete(self, task: BackgroundTask):
        """任务完成回调：自动推送结果到微信"""
        if not task.result:
            return
        
        user_id = task.user_id
        result = task.result
        context_token = task.context_token
        
        logger.info(f"[callback] 任务 {task.task_id} 完成，推送给 {user_id}")
        
        # 触发任务完成事件
        if self.event_bus:
            await self.event_bus.emit("task:completed" if not result.error else "task:failed", {
                "task_id": task.task_id,
                "handler_name": task.handler_name,
                "user_id": user_id,
                "duration": task.duration,
                "status": task.status.value,
                "error": result.error,
                "text_preview": result.text[:200] if result.text else "",
            }, source="bot")
        
        # 构建结果消息
        header = f"📬 后台任务完成\n任务ID: {task.task_id}\n类型: {task.handler_name}\n耗时: {task.duration:.1f}秒\n状态: {task.status.value}\n"
        header += "=" * 20 + "\n"
        
        if result.error:
            text = header + f"❌ {result.text or result.error}"
        else:
            text = header + result.text
        
        await self._send_text(user_id, text, context_token=context_token)
    
    async def _handle_message(self, msg: Dict):
        """处理单条消息：提取文本 → 注册表分发 → 发送回复"""
        content = self.api.extract_text_from_message(msg).strip()
        from_user = msg.get("from_user_id", "")
        context_token = msg.get("context_token")
        session_id = msg.get("session_id")
        
        if not content or not from_user:
            return
        
        # 记录用户到 Webhook
        if self.webhook:
            self.webhook.record_user(from_user, context_token=context_token, session_id=session_id)
        
        logger.info(f"📩 [{from_user}] {content} | context_token={context_token} | session_id={session_id}")
        
        # 触发消息接收事件
        if self.event_bus:
            await self.event_bus.emit("bot:message_received", {
                "from_user": from_user,
                "content": content,
                "context_token": context_token,
                "session_id": session_id,
            }, source="bot")
        
        # 通过注册表分发任务
        task_result = self.registry.dispatch(content, msg)
        
        if task_result is None:
            await self._send_text(from_user, "⚠️ 暂不支持该指令，输入 help 查看可用功能", context_token=context_token)
            return
        
        await self._send_result(from_user, task_result, context_token=context_token)
    
    async def _send_result(self, to: str, result: TaskResult, context_token: Optional[str] = None):
        """发送任务结果到用户"""
        if result.error:
            await self._send_text(to, result.text or f"❌ {result.error}", context_token=context_token)
            return
        
        if result.text:
            await self._send_text(to, result.text, context_token=context_token)
    
    async def _send_text(self, to: str, text: str, context_token: Optional[str] = None):
        """安全发送文本消息（异步包装）"""
        try:
            logger.info(f"[send] 正在发送消息到 {to}, 长度={len(text)}, context_token={context_token}")
            result = await asyncio.to_thread(self.api.send_text_message, to=to, text=text, context_token=context_token)
            logger.info(f"[send] 消息发送成功 → {to}, 响应={result}")
            
            # 触发消息发送事件
            if self.event_bus:
                await self.event_bus.emit("bot:message_sent", {
                    "to_user": to,
                    "text_preview": text[:200],
                    "context_token": context_token,
                    "success": True,
                }, source="bot")
            
            return result
        except Exception as e:
            logger.exception(f"[send] 发送失败 → {to}")
            
            # 触发发送失败事件
            if self.event_bus:
                await self.event_bus.emit("bot:message_sent", {
                    "to_user": to,
                    "text_preview": text[:200],
                    "context_token": context_token,
                    "success": False,
                    "error": str(e),
                }, source="bot")
    
    def stop(self):
        self.running = False
        self.executor.stop()
        logger.info("机器人已停止")
