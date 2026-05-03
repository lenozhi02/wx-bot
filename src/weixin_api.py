import requests
import time
import json
import random
import struct
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WeixinMessage:
    """标准化微信消息"""
    seq: int
    message_id: int
    from_user_id: str
    to_user_id: str
    client_id: str
    create_time_ms: int
    session_id: str
    message_type: int
    message_state: int
    item_list: List[Dict[str, Any]]
    context_token: Optional[str]
    raw_data: Dict[str, Any]


class WeixinAPI:
    """
    微信 iLink Bot API（完全参考 co-pine/wx-robot-ilink 的 api.ts）
    """
    
    DEFAULT_API_TIMEOUT_MS = 15000
    DEFAULT_LONG_POLL_TIMEOUT_MS = 35000
    
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
    
    def _random_wechat_uin(self) -> str:
        """生成随机微信 UIN（参考 randomWechatUin）"""
        uint32 = random.randint(0, 0xFFFFFFFF)
        return str(uint32).encode('utf-8').decode('utf-8')  # 简化版，原逻辑是 base64
    
    def _build_headers(self) -> Dict[str, str]:
        """构建请求头（参考 buildHeaders）"""
        headers = {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "X-WECHAT-UIN": self._random_wechat_uin(),
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _api_post(self, endpoint: str, body: Dict[str, Any], timeout_ms: int = None) -> Dict[str, Any]:
        """通用 POST 请求（参考 apiPost）"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout = (timeout_ms or self.DEFAULT_API_TIMEOUT_MS) / 1000
        
        body_str = json.dumps(body)
        headers = self._build_headers()
        headers["Content-Length"] = str(len(body_str.encode('utf-8')))
        
        try:
            resp = self.session.post(
                url,
                headers=headers,
                data=body_str,
                timeout=timeout
            )
            
            text = resp.text
            logger.debug(f"[api] {endpoint} response {resp.status_code}: {text[:500]}")
            
            if not resp.ok:
                raise Exception(f"API {endpoint} HTTP {resp.status_code}: {text}")
            
            data = json.loads(text)
            
            # 检查业务错误码
            if data.get("ret") not in (0, None):
                raise Exception(f"API {endpoint} 业务错误 ret={data.get('ret')}: {data}")
            
            return data
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求 {endpoint} 超时")
        except json.JSONDecodeError:
            raise Exception(f"API {endpoint} 返回非 JSON: {text}")
        except Exception as e:
            raise Exception(f"请求 {endpoint} 失败: {e}")
    
    def get_updates(self, buf: str = "", timeout_ms: int = None) -> Dict[str, Any]:
        """
        获取消息更新（参考 getUpdates）
        长轮询，超时返回空列表
        """
        timeout = timeout_ms or self.DEFAULT_LONG_POLL_TIMEOUT_MS
        
        try:
            return self._api_post(
                "ilink/bot/getupdates",
                {"get_updates_buf": buf},
                timeout_ms=timeout
            )
        except TimeoutError:
            # 长轮询超时是正常情况，返回空结果
            return {"ret": 0, "msgs": [], "get_updates_buf": buf}
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            raise
    
    def send_text_message(self, to: str, text: str, context_token: Optional[str] = None) -> Dict[str, Any]:
        """
        发送文本消息（参考 sendTextMessage）
        
        Returns:
            API 响应数据
        """
        client_id = f"bot-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        
        items = []
        if text:
            items.append({
                "type": 1,  # MessageItemType.TEXT
                "text_item": {"text": text}
            })
        
        msg = {
            "from_user_id": "",
            "to_user_id": to,
            "client_id": client_id,
            "message_type": 2,  # MessageType.BOT
            "message_state": 2,  # MessageState.FINISH
            "item_list": items if items else None,
            "context_token": context_token,
        }
        
        logger.info(f"[api] send_text_message → to={to}, client_id={client_id}, text_len={len(text)}")
        
        resp = self._api_post(
            "ilink/bot/sendmessage",
            {"msg": msg}
        )
        
        logger.info(f"[api] send_text_message 响应: {resp}")
        return resp
    
    @staticmethod
    def extract_text_from_message(msg: Dict[str, Any]) -> str:
        """
        从消息中提取文本（参考 extractTextFromMessage）
        """
        items = msg.get("item_list", [])
        if not items:
            return ""
        
        for item in items:
            if item.get("type") == 1 and item.get("text_item", {}).get("text"):
                ref = item.get("ref_msg")
                text = item["text_item"]["text"]
                if not ref:
                    return text
                parts = []
                if ref.get("title"):
                    parts.append(ref["title"])
                return f"[引用: {' | '.join(parts)}]\n{text}" if parts else text
        
        return ""
