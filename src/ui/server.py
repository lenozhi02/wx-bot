"""
FastAPI 服务 —— WX-BOT Web UI 后端

提供：
1. REST API 状态查询
2. WebSocket 实时事件
3. SSE 事件流
"""

import logging
from typing import Optional

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
    from fastapi.responses import StreamingResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from src.ui.bus import EventBus
from src.ui.hub import WebSocketHub, SSEStream

logger = logging.getLogger(__name__)


class UIServer:
    """
    WX-BOT Web UI 服务
    
    独立运行，与 Bot 主循环通过 EventBus 解耦。
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        host: str = "0.0.0.0",
        port: int = 3000,
        bot_instance=None,
        executor=None,
        webhook=None,
    ):
        if not FASTAPI_AVAILABLE:
            raise ImportError("UIServer 需要 FastAPI，请安装: pip install fastapi uvicorn")
        
        self.event_bus = event_bus
        self.host = host
        self.port = port
        self.bot = bot_instance
        self.executor = executor
        self.webhook = webhook
        
        # 创建组件
        self.hub = WebSocketHub(event_bus)
        self.sse = SSEStream(event_bus)
        self.app = self._create_app()
        
        logger.info(f"[ui] UIServer 初始化完成，将监听 {host}:{port}")
    
    def _create_app(self) -> "FastAPI":
        """创建 FastAPI 应用"""
        app = FastAPI(
            title="WX-BOT Web UI",
            description="微信机器人 Web 监控界面 API",
            version="1.0.0",
        )
        
        # CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        self._register_routes(app)
        
        # 静态文件（前端构建产物）—— 必须放在 API 路由之后
        self._mount_static(app)
        
        return app
    
    def _register_routes(self, app: "FastAPI"):
        """注册 API 路由"""
        
        # ========== 健康检查 ==========
        @app.get("/api/health")
        async def health():
            return {
                "status": "ok",
                "version": "1.0.0",
                "event_bus": {
                    "subscribers": self.event_bus.get_subscriber_counts(),
                    "history_size": len(self.event_bus._history),
                },
                "websocket": self.hub.get_stats(),
            }
        
        # ========== Bot 状态 ==========
        @app.get("/api/bot/status")
        async def bot_status():
            if not self.bot:
                return {"status": "unknown", "message": "Bot 实例未绑定"}
            
            return {
                "running": self.bot.running,
                "handlers": self.bot.registry.list_handlers() if self.bot.registry else [],
                "webhook_enabled": self.bot.webhook is not None,
                "executor_workers": self.bot.executor.max_workers if self.bot.executor else 0,
            }
        
        @app.get("/api/bot/handlers")
        async def bot_handlers():
            if not self.bot or not self.bot.registry:
                return {"handlers": []}
            
            handlers = self.bot.registry.list_handlers()
            return {"handlers": handlers, "count": len(handlers)}
        
        # ========== 任务管理 ==========
        @app.get("/api/tasks")
        async def list_tasks(
            status: Optional[str] = Query(None, description="按状态过滤"),
            limit: int = Query(50, ge=1, le=200),
        ):
            if not self.executor:
                return {"tasks": [], "total": 0}
            
            tasks = self.executor.list_tasks()
            
            # 按状态过滤
            if status:
                tasks = [t for t in tasks if t.status.value == status]
            
            # 按时间倒序，限制条数
            tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]
            
            return {
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "handler_name": t.handler_name,
                        "user_id": t.user_id,
                        "status": t.status.value,
                        "progress": t.progress,
                        "created_at": t.created_at,
                        "started_at": t.started_at,
                        "finished_at": t.finished_at,
                        "duration": t.duration,
                    }
                    for t in tasks
                ],
                "total": len(tasks),
            }
        
        @app.get("/api/tasks/{task_id}")
        async def get_task(task_id: str):
            if not self.executor:
                return JSONResponse({"error": "Executor 未初始化"}, status_code=500)
            
            task = self.executor.get_task(task_id)
            if not task:
                return JSONResponse({"error": "任务不存在"}, status_code=404)
            
            return {
                "task_id": task.task_id,
                "handler_name": task.handler_name,
                "user_id": task.user_id,
                "content": task.content,
                "status": task.status.value,
                "progress": task.progress,
                "result": {
                    "text": task.result.text[:500] if task.result else None,
                    "error": task.result.error if task.result else None,
                } if task.result else None,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "finished_at": task.finished_at,
                "duration": task.duration,
            }
        
        # ========== 系统指标 ==========
        @app.get("/api/system/metrics")
        async def system_metrics():
            metrics = {"timestamp": __import__("time").time()}
            
            try:
                import psutil
                metrics["cpu"] = {
                    "percent": psutil.cpu_percent(interval=0.5),
                    "count": psutil.cpu_count(),
                }
                mem = psutil.virtual_memory()
                metrics["memory"] = {
                    "total": mem.total,
                    "available": mem.available,
                    "percent": mem.percent,
                    "used": mem.used,
                }
                disk = psutil.disk_usage("/")
                metrics["disk"] = {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                }
                metrics["uptime"] = __import__("time").time() - psutil.boot_time()
                metrics["processes"] = len(psutil.pids())
            except ImportError:
                metrics["error"] = "psutil 未安装"
            
            return metrics
        
        # ========== 事件历史 ==========
        @app.get("/api/events/history")
        async def events_history(
            event: Optional[str] = Query(None),
            limit: int = Query(100, ge=1, le=1000),
        ):
            history = self.event_bus.get_history(event_filter=event, limit=limit)
            return {
                "events": [
                    {
                        "event": h.event,
                        "timestamp": h.timestamp,
                        "data": h.data,
                        "source": h.source,
                    }
                    for h in history
                ],
                "count": len(history),
            }
        
        # ========== Webhook 状态 ==========
        @app.get("/api/webhook/status")
        async def webhook_status():
            if not self.webhook:
                return {"enabled": False}
            
            return {
                "enabled": True,
                "host": self.webhook.host,
                "port": self.webhook.port,
                "default_user": self.webhook.default_user,
                "recent_users": self.webhook._recent_users,
                "queue_size": self.webhook.queue.qsize(),
            }
        
        # ========== WebSocket ==========
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            client_id = await self.hub.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_json()
                    await self.hub.handle_message(client_id, data)
            except WebSocketDisconnect:
                await self.hub.disconnect(client_id)
            except Exception as e:
                logger.warning(f"[ui] WebSocket 异常: {e}")
                await self.hub.disconnect(client_id)
        
        # ========== SSE ==========
        @app.get("/api/events/stream")
        async def events_stream(
            filter: Optional[str] = Query(None, alias="filter"),
        ):
            return StreamingResponse(
                self.sse.stream(event_filter=filter),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
    
    def _mount_static(self, app: "FastAPI"):
        """挂载前端静态文件"""
        import os
        # 尝试多个可能的路径
        candidates = [
            "web/dist",
            os.path.join(os.path.dirname(__file__), "../../web/dist"),
            os.path.join(os.path.dirname(__file__), "../../../web/dist"),
        ]
        static_dir = None
        for c in candidates:
            if os.path.isdir(c) and os.path.isfile(os.path.join(c, "index.html")):
                static_dir = os.path.abspath(c)
                break
        
        if static_dir:
            app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
            logger.info(f"[ui] 静态文件服务: {static_dir}")
        else:
            logger.warning("[ui] 未找到前端构建产物 web/dist，UI 将无法通过浏览器访问")
    
    async def run(self):
        """启动服务"""
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()
