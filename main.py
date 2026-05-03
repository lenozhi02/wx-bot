import sys
import argparse
import logging

from src.auth import AuthManager
from src.weixin_api import WeixinAPI
from src.bot import WeixinBot
from src.tasks.registry import TaskRegistry
from src.tasks.status_task import StatusTaskHandler
from src.tasks.search_task import SearchTaskHandler
from src.tasks.ai_task import AITaskHandler
from src.tasks.help_task import HelpTaskHandler
from src.webhook import WebhookServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def build_registry() -> TaskRegistry:
    """
    构建并配置任务处理器注册表。
    
    新增任务类型时，在此注册即可：
        registry.register(YourTaskHandler())
    """
    registry = TaskRegistry()
    
    # 1. 帮助指令（最高优先级）
    help_handler = HelpTaskHandler(bot_name="微信本地机器人")
    registry.register(help_handler)
    
    # 2. 服务器状态巡检
    registry.register(StatusTaskHandler(cmd_timeout=10, max_output_lines=50))
    
    # 3. 网络搜索（示例扩展）
    registry.register(SearchTaskHandler(max_results=5))
    
    # 4. AI 对话兜底（最低优先级）
    registry.register(AITaskHandler(prefix="AI", fallback=True))
    
    # 动态更新帮助文本
    help_handler.set_help_text(
        "• 输入任意消息 — AI 助手自动回复\n"
        "• 搜索 <关键词> — 网络搜索"
    )
    
    return registry


def main():
    parser = argparse.ArgumentParser(description='微信本地命令机器人')
    parser.add_argument('--logout', action='store_true', help='清除登录凭证并重新扫码')
    parser.add_argument('--webhook-host', default='0.0.0.0', help='Webhook 监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--webhook-port', type=int, default=8080, help='Webhook 监听端口 (默认: 8080)')
    parser.add_argument('--no-webhook', action='store_true', help='禁用 Webhook 服务')
    args = parser.parse_args()
    
    auth = AuthManager()
    
    # 清除凭证
    if args.logout:
        auth.clear_credentials()
        print("✅ 已清除登录凭证，下次启动需重新扫码")
        return
    
    # 登录（扫码或复用凭证）
    try:
        creds = auth.login()
        print(f"登录成功，使用 baseUrl: {creds['baseUrl']}\n")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        sys.exit(1)
    
    # 初始化 API
    api = WeixinAPI(base_url=creds["baseUrl"], token=creds["token"])
    
    # 构建任务注册表
    registry = build_registry()
    
    # 创建 Webhook 服务（可选）
    webhook = None
    if not args.no_webhook:
        webhook = WebhookServer(host=args.webhook_host, port=args.webhook_port)
    
    # 创建机器人
    bot = WeixinBot(api, registry=registry, webhook=webhook)
    
    # 优雅退出
    import signal
    def signal_handler(sig, frame):
        print("\n🛑 正在关闭...")
        bot.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bot.start()


if __name__ == "__main__":
    main()
