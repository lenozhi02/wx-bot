import os
import json
import time
import requests
import qrcode
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

BASE_URL = "https://ilinkai.weixin.qq.com"
BOT_TYPE = "3"
QR_POLL_TIMEOUT_MS = 35000
MAX_QR_REFRESH = 3

CREDENTIALS_PATH = "data/credentials.json"


class AuthManager:
    """扫码登录认证（完全参考 auth.ts）"""
    
    def __init__(self):
        self.base_url = BASE_URL
    
    def _fetch_qrcode(self) -> Dict[str, Any]:
        """获取二维码（参考 fetchQRCode）"""
        url = f"{self.base_url}/ilink/bot/get_bot_qrcode?bot_type={BOT_TYPE}"
        logger.info(f"请求二维码: {url}")
        
        resp = requests.get(url, timeout=15)
        if not resp.ok:
            raise Exception(f"获取二维码失败: HTTP {resp.status_code}")
        
        data = resp.json()
        logger.info(f"二维码响应: {data}")
        return data
    
    def _poll_qr_status(self, qrcode_str: str) -> Dict[str, Any]:
        """轮询二维码状态（参考 pollQRStatus）"""
        url = f"{self.base_url}/ilink/bot/get_qrcode_status"
        params = {"qrcode": qrcode_str}
        headers = {"iLink-App-ClientVersion": "1"}
        
        try:
            resp = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=QR_POLL_TIMEOUT_MS / 1000
            )
            
            if not resp.ok:
                raise Exception(f"轮询失败: HTTP {resp.status_code}")
            
            return resp.json()
            
        except requests.exceptions.Timeout:
            # 超时视为等待状态
            return {"status": "wait"}
        except Exception as e:
            raise Exception(f"轮询状态失败: {e}")
    
    def _display_qrcode(self, qrcode_url: str):
        """终端显示二维码（参考 displayQRCode）"""
        try:
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(qrcode_url)
            qr.make(fit=True)
            qr.print_ascii(invert=True)
        except Exception:
            pass
        print(f"\n如果二维码无法显示，请在浏览器打开:\n{qrcode_url}\n")
    
    def login(self) -> Dict[str, Any]:
        """
        完整登录流程（参考 login）
        返回: {"token": str, "baseUrl": str, "accountId": str, "userId": str}
        """
        # 尝试加载已保存凭证
        saved = self._load_credentials()
        if saved:
            logger.info(f"[auth] 使用已保存的凭证 (accountId={saved['accountId']})")
            return saved
        
        logger.info("[auth] 正在获取登录二维码...")
        qr = self._fetch_qrcode()
        self._display_qrcode(qr["qrcode_img_content"])
        
        refresh_count = 0
        deadline = time.time() + 8 * 60  # 8 分钟超时
        
        while time.time() < deadline:
            status = self._poll_qr_status(qr["qrcode"])
            status_code = status.get("status")
            
            if status_code == "wait":
                pass
            elif status_code == "scaned":
                logger.info("[auth] 已扫码，请在手机上确认...")
            elif status_code == "expired":
                refresh_count += 1
                if refresh_count >= MAX_QR_REFRESH:
                    raise Exception("二维码多次过期，请重试")
                logger.info(f"[auth] 二维码已过期，正在刷新... ({refresh_count}/{MAX_QR_REFRESH})")
                qr = self._fetch_qrcode()
                self._display_qrcode(qr["qrcode_img_content"])
            elif status_code == "confirmed":
                if not status.get("bot_token") or not status.get("ilink_bot_id"):
                    raise Exception("登录确认但未返回 token 或 bot_id")
                
                creds = {
                    "token": status["bot_token"],
                    "baseUrl": status.get("baseurl") or self.base_url,
                    "accountId": status["ilink_bot_id"],
                    "userId": status.get("ilink_user_id"),
                }
                self._save_credentials(creds)
                logger.info(f"[auth] ✅ 登录成功! accountId={creds['accountId']}")
                return creds
            
            time.sleep(1)
        
        raise Exception("登录超时（8分钟）")
    
    def _save_credentials(self, creds: Dict[str, Any]):
        """保存凭证（参考 saveCredentials）"""
        os.makedirs(os.path.dirname(CREDENTIALS_PATH) or ".", exist_ok=True)
        with open(CREDENTIALS_PATH, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(CREDENTIALS_PATH, 0o600)
        except:
            pass
    
    def _load_credentials(self) -> Optional[Dict[str, Any]]:
        """加载凭证（参考 loadCredentials）"""
        try:
            if not os.path.exists(CREDENTIALS_PATH):
                return None
            with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("token") and data.get("baseUrl") and data.get("accountId"):
                return data
            return None
        except Exception:
            return None
    
    def clear_credentials(self):
        """清除凭证（参考 clearCredentials）"""
        try:
            if os.path.exists(CREDENTIALS_PATH):
                os.remove(CREDENTIALS_PATH)
                logger.info("凭证已清除")
        except Exception:
            pass
