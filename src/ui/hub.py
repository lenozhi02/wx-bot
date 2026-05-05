"""
WebSocket Hub —— 实时事件推送中心

职责：
1. 管理 WebSocket 客户端连接
2. 订阅 EventBus 事件，转发到匹配的客户端
3. 支持客户端订阅/取消订阅特定事件
4. 提供 SSE (Server-Sent Events) 流接口
"""

import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional, List
from dataclasses import dataclass, field

try:
    from fastapi import WebSocket, WebSocketDisconnect
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from src.ui.bus import EventBus, BusEvent

logger = logging.getLogger(__name__)


@dataclass
class WSClient:
    """WebSocket 客户端封装"""
    id: str
    websocket: Optional["WebSocket"]
    subscribed_events: Set[str] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)


class WebSocketHub:
    """
    WebSocket 事件推送中心
    
    与 EventBus 对接，将事件实时推送到前端。
    """
    
    def __init__(self, event_bus: EventBus):
        if not FASTAPI_AVAILABLE:
            raise ImportError("WebSocketHub 需要 FastAPI，请安装: pip install fastapi")
        
        self.event_bus = event_bus
        self.clients: Dict[str, WSClient] = {}
        self._client_counter = 0
        self._lock = asyncio.Lock()
        
        # 订阅所有事件（通过通配符）
        self.event_bus.on("*", self._on_bus_event)
        logger.info("[hub] WebSocket Hub 初始化完成")
    
    def _next_client_id(self) -> str:
        self._client_counter += 1
        return f"ws-{int(time.time())}-{self._client_counter}"
    
    async def connect(self, websocket: "WebSocket"):
        """处理新 WebSocket 连接"""
        await websocket.accept()
        
        client_id = self._next_client_id()
        client = WSClient(id=client_id, websocket=websocket)
        
        async with self._lock:
            self.clients[client_id] = client
        
        logger.info(f"[hub] 客户端连接: {client_id}, 当前连接数: {len(self.clients)}")
        
        # 发送欢迎消息
        await self._send_to_client(client, {
            "type": "connected",
            "client_id": client_id,
            "message": "已连接到 WX-BOT 事件中心",
        })
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """处理客户端断开"""
        async with self._lock:
            if client_id in self.clients:
                del self.clients[client_id]
        
        logger.info(f"[hub] 客户端断开: {client_id}, 当前连接数: {len(self.clients)}")
    
    async def handle_message(self, client_id: str, data: dict):
        """处理客户端发送的消息"""
        client = self.clients.get(client_id)
        if not client:
            return
        
        msg_type = data.get("type", "")
        
        if msg_type == "subscribe":
            events = data.get("events", [])
            client.subscribed_events.update(events)
            await self._send_to_client(client, {
                "type": "subscribed",
                "events": list(client.subscribed_events),
            })
            logger.debug(f"[hub] {client_id} 订阅事件: {events}")
        
        elif msg_type == "unsubscribe":
            events = data.get("events", [])
            client.subscribed_events.difference_update(events)
            await self._send_to_client(client, {
                "type": "unsubscribed",
                "events": list(client.subscribed_events),
            })
            logger.debug(f"[hub] {client_id} 取消订阅: {events}")
        
        elif msg_type == "ping":
            client.last_ping = time.time()
            await self._send_to_client(client, {"type": "pong", "time": time.time()})
        
        else:
            await self._send_to_client(client, {
                "type": "error",
                "message": f"未知消息类型: {msg_type}",
            })
    
    async def _on_bus_event(self, event: BusEvent):
        """EventBus 事件回调：将事件推送到匹配的客户端"""
        if not self.clients:
            return
        
        message = {
            "type": "event",
            "event": event.event,
            "timestamp": event.timestamp,
            "data": event.data,
            "source": event.source,
        }
        
        # 推送到所有订阅了该事件的客户端
        tasks = []
        for client in list(self.clients.values()):
            if self._client_matches(client, event.event):
                tasks.append(self._send_to_client(client, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _client_matches(self, client: WSClient, event_name: str) -> bool:
        """检查客户端是否订阅了该事件"""
        if not client.subscribed_events:
            return True  # 未指定则接收所有
        
        for pattern in client.subscribed_events:
            if pattern == "*":
                return True
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if event_name.startswith(prefix):
                    return True
            if pattern == event_name:
                return True
        
        return False
    
    async def _send_to_client(self, client: WSClient, message: dict):
        """发送消息到单个客户端"""
        try:
            if client.websocket:
                await client.websocket.send_json(message)
        except Exception as e:
            logger.warning(f"[hub] 发送消息到 {client.id} 失败: {e}")
            # 标记为待清理
            asyncio.create_task(self.disconnect(client.id))
    
    async def broadcast(self, message: dict, event_filter: Optional[str] = None):
        """广播消息到所有匹配的客户端"""
        if not self.clients:
            return
        
        tasks = []
        for client in list(self.clients.values()):
            if event_filter and not self._client_matches(client, event_filter):
                continue
            tasks.append(self._send_to_client(client, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_stats(self) -> dict:
        """获取 Hub 统计信息"""
        return {
            "connected_clients": len(self.clients),
            "clients": [
                {
                    "id": c.id,
                    "subscribed_events": list(c.subscribed_events),
                    "connected_at": c.connected_at,
                    "duration": time.time() - c.connected_at,
                }
                for c in self.clients.values()
            ],
        }


class SSEStream:
    """
    Server-Sent Events 流
    
    作为 WebSocket 的轻量替代，适合单向推送场景。
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._queues: List[asyncio.Queue] = []
        self.event_bus.on("*", self._on_event)
        logger.info("[sse] SSE Stream 初始化完成")
    
    async def _on_event(self, event: BusEvent):
        """将事件放入所有队列"""
        message = {
            "event": event.event,
            "timestamp": event.timestamp,
            "data": event.data,
        }
        
        for queue in list(self._queues):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                pass
    
    async def stream(self, event_filter: Optional[str] = None):
        """
        生成 SSE 流
        
        使用方式（FastAPI）:
            @app.get("/api/events/stream")
            async def events_stream():
                return StreamingResponse(sse.stream(), media_type="text/event-stream")
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.append(queue)
        
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    
                    # 过滤
                    if event_filter and not self._matches_filter(message["event"], event_filter):
                        continue
                    
                    # SSE 格式
                    yield f"event: {message['event']}\n"
                    yield f"data: {json.dumps(message['data'], ensure_ascii=False)}\n\n"
                
                except asyncio.TimeoutError:
                    # 发送心跳注释保持连接
                    yield ":heartbeat\n\n"
        
        finally:
            if queue in self._queues:
                self._queues.remove(queue)
    
    def _matches_filter(self, event_name: str, filter_pattern: str) -> bool:
        """匹配事件过滤规则"""
        if filter_pattern == "*":
            return True
        if filter_pattern.endswith("*"):
            return event_name.startswith(filter_pattern[:-1])
        return event_name == filter_pattern
