"""
Webhook HTTP 服务

提供 Web 接口接收外部推送，将消息转发到微信端。

接口：
  POST /webhook/send
  
  请求体（Content-Type: application/json）：
  {
    "to": "wxid_xxx",           // 可选，目标微信用户ID，不提供则发给默认用户
    "text": "推送消息内容",      // 可选，纯文本内容
    "data": {...},              // 可选，JSON 数据（会被格式化为文本）
    "template": "{name}: {value}" // 可选，自定义模板（使用 data 中的字段）
  }

  响应：
  {
    "success": true,
    "message": "已推送"
  }

启动方式：
  与 Bot 主循环一起启动，通过消息队列解耦。
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class WebhookServer:
    """
    Webhook HTTP 服务器
    
    使用 asyncio.Queue 作为消息队列，与 Bot 主循环解耦。
    支持默认用户（最近交互用户），无需每次指定 to。
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        default_user: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.default_user = default_user
        self.queue: asyncio.Queue = asyncio.Queue()
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        # 记录最近交互过的用户ID列表（按时间倒序）
        self._recent_users: List[str] = []
        self._max_recent = 10
        # 缓存用户上下文信息（context_token, session_id）
        self._user_contexts: Dict[str, Dict[str, Any]] = {}
    
    def set_default_user(self, user_id: str):
        """设置默认推送用户"""
        self.default_user = user_id
        logger.info(f"[webhook] 默认用户已设置: {user_id}")
    
    def record_user(self, user_id: str, context_token: Optional[str] = None, session_id: Optional[str] = None):
        """记录最近交互的用户，同时缓存 context_token 用于后续推送"""
        if not user_id:
            return
        
        # 存储用户上下文信息
        self._user_contexts[user_id] = {
            "context_token": context_token,
            "session_id": session_id,
            "updated_at": datetime.now().isoformat(),
        }
        
        # 去重并置顶
        if user_id in self._recent_users:
            self._recent_users.remove(user_id)
        self._recent_users.insert(0, user_id)
        self._recent_users = self._recent_users[:self._max_recent]
        
        # 首次交互自动设为默认用户
        if not self.default_user:
            self.default_user = user_id
            logger.info(f"[webhook] 自动设置默认用户: {user_id} (context_token={context_token})")
    
    @property
    def target_user(self) -> Optional[str]:
        """获取当前目标用户（默认用户 > 最近用户）"""
        return self.default_user or (self._recent_users[0] if self._recent_users else None)
    
    async def setup(self):
        """初始化 aiohttp 应用"""
        if not AIOHTTP_AVAILABLE:
            raise ImportError("Webhook 服务需要 aiohttp，请安装: pip install aiohttp")
        
        self.app = web.Application()
        self.app.router.add_post("/webhook/send", self._handle_send)
        self.app.router.add_get("/webhook/send", self._handle_send_get)
        self.app.router.add_get("/webhook/health", self._handle_health)
        self.app.router.add_get("/", self._handle_index)
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f"🌐 Webhook 服务已启动: http://{self.host}:{self.port}")
        logger.info(f"   推送接口: POST http://{self.host}:{self.port}/webhook/send")
        if self.default_user:
            logger.info(f"   默认用户: {self.default_user}")
    
    async def teardown(self):
        """清理资源"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("🌐 Webhook 服务已停止")
    
    async def _handle_send(self, request: web.Request) -> web.Response:
        """处理 POST 推送请求"""
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"success": False, "error": "请求体必须是合法的 JSON"},
                status=400
            )
        
        return await self._process_send(body)
    
    async def _handle_send_get(self, request: web.Request) -> web.Response:
        """处理 GET 推送请求（简易模式，通过 query 参数）"""
        text = request.query.get("text", "")
        data_str = request.query.get("data", "")
        to = request.query.get("to", "")
        
        body: Dict[str, Any] = {}
        if to:
            body["to"] = to
        if text:
            body["text"] = text
        if data_str:
            try:
                body["data"] = json.loads(data_str)
            except json.JSONDecodeError:
                body["data"] = data_str
        
        return await self._process_send(body)
    
    async def _process_send(self, body: Dict[str, Any]) -> web.Response:
        """统一的推送处理逻辑"""
        # 确定目标用户
        to_user = body.get("to") or self.target_user
        if not to_user:
            return web.json_response(
                {
                    "success": False,
                    "error": "未指定目标用户 (to)，且没有默认用户。"
                             "请先通过微信与机器人交互，或显式指定 to 字段。",
                    "recent_users": self._recent_users,
                },
                status=400
            )
        
        # 构建消息内容
        message_text = self._build_message(body)
        if not message_text:
            return web.json_response(
                {"success": False, "error": "缺少内容字段: text 或 data 至少提供一个"},
                status=400
            )
        
        # 放入队列，等待 Bot 消费
        # 获取用户的 context_token（如果有缓存）
        user_context = self._user_contexts.get(to_user, {})
        context_token = user_context.get("context_token")
        
        await self.queue.put({
            "to": to_user,
            "text": message_text,
            "context_token": context_token,
            "timestamp": datetime.now().isoformat(),
            "raw": body,
        })
        
        logger.info(f"[webhook] 收到推送 → {to_user}: {message_text[:50]}...")
        
        return web.json_response({
            "success": True,
            "message": "已加入推送队列",
            "to": to_user,
        })
    
    async def _handle_health(self, request: web.Request) -> web.Response:
        """健康检查接口"""
        return web.json_response({
            "status": "ok",
            "queue_size": self.queue.qsize(),
            "default_user": self.default_user,
            "recent_users": self._recent_users,
            "timestamp": datetime.now().isoformat(),
        })
    
    async def _handle_index(self, request: web.Request) -> web.Response:
        """首页说明"""
        default_info = f"默认用户: {self.default_user}" if self.default_user else "默认用户: 未设置（等待首次微信交互）"
        html = f"""<!DOCTYPE html>
<html>
<head><title>微信机器人 Webhook</title></head>
<body>
<h1>🤖 微信机器人 Webhook 服务</h1>
<p>服务运行中，队列长度: {self.queue.qsize()}</p>
<p>{default_info}</p>

<h2>简易接口（无需用户ID）</h2>
<pre>
# 方式1: POST JSON（推荐）
curl -X POST http://{self.host}:{self.port}/webhook/send \\
  -H "Content-Type: application/json" \\
  -d '{{"text": "服务器告警：CPU 90%"}}'

# 方式2: GET 请求（快速测试）
curl "http://{self.host}:{self.port}/webhook/send?text=hello"

# 方式3: 指定用户（覆盖默认）
curl -X POST http://{self.host}:{self.port}/webhook/send \\
  -H "Content-Type: application/json" \\
  -d '{{"to": "wxid_xxx@im.wechat", "text": "指定用户消息"}}'
</pre>

<h2>完整字段说明</h2>
<pre>
{{
  "to":       "wxid_xxx@im.wechat",  // 可选，默认发给最近交互用户
  "text":     "纯文本消息",           // 可选
  "data":     {{"key": "value"}},    // 可选，JSON 数据
  "template": "{{key}}"               // 可选，格式化模板
}}
</pre>

<p><a href="/webhook/health">健康检查</a></p>
</body>
</html>"""
        return web.Response(text=html, content_type="text/html")
    
    def _build_message(self, body: Dict[str, Any]) -> str:
        """
        根据请求体构建微信消息文本
        
        优先级:
        1. template + data → 格式化输出
        2. text → 纯文本
        3. data → JSON 格式化输出
        """
        text = body.get("text", "")
        data = body.get("data")
        template = body.get("template", "")
        
        # 模板模式
        if template and data and isinstance(data, dict):
            try:
                return template.format(**data)
            except KeyError as e:
                return f"[模板错误] 字段 {e} 不存在\n数据: {json.dumps(data, ensure_ascii=False, indent=2)}"
        
        # 纯文本模式
        if text:
            return text
        
        # JSON 数据模式
        if data is not None:
            return self._format_json(data)
        
        return ""
    
    @staticmethod
    def _format_json(data: Any) -> str:
        """将 JSON 数据格式化为易读的文本"""
        if isinstance(data, dict):
            lines = ["📦 数据推送"]
            for key, value in data.items():
                lines.append(f"  {key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            return "\n".join([f"  • {item}" for item in data])
        else:
            return str(data)
    
    async def get_next(self) -> Optional[Dict[str, Any]]:
        """
        从队列中获取下一条待推送消息（阻塞等待）
        
        由 Bot 主循环调用。
        """
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
