# wx-bot
微信机器人设计文档
1. 项目概述
本项目是一个基于微信 iLink Bot API 的本地命令执行机器人。用户通过微信发送文本指令，机器人在本地安全执行预设命令并返回结果。

# 1. 安装依赖
pip install requests qrcode[pil]

# 2. 首次启动（终端显示二维码，微信扫码）
python main.py

# 3. 重新登录
python main.py --logout

# 4. 后台运行
nohup python main.py > bot.log 2>&1 &

# 5.  指定端口
python main.py --webhook-port 3000

# 6. 禁用 Webhook
python main.py --no-webhook

# 7. web接口调用
   curl -X POST http://localhost:18789/webhook/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "xxx@im.wechat",
    "text": "测试消息"
  }'

  

3. 架构设计


┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   main.py   │────▶│  AuthManager│────▶│  WeixinAPI  │────▶│  WeixinBot  │
│  (入口)      │     │  (认证管理)  │     │  (API封装)  │     │  (业务逻辑)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       │                   ▼                   ▼                   ▼
       │            ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
       │            │ 微信扫码登录 │     │ iLink API   │     │ 本地命令执行 │
       │            │ 凭证持久化   │     │ 收发消息    │     │ 消息处理    │
       │            └─────────────┘     └─────────────┘     └─────────────┘
       ▼
┌─────────────┐
│ data/       │
│ credentials │  ← 登录凭证持久化存储
└─────────────┘


3 数据流图

用户微信 ──文本消息──▶ 微信服务器 ──iLink API──▶ WeixinAPI.get_updates()
                                                          │
                                                          ▼
                                              WeixinBot._handle_message()
                                                          │
                                    ┌─────────────────────┼─────────────────────┐
                                    ▼                     ▼                     ▼
                              [ShellTask]           [SearchTask](没实现）    [AIGPTask](没实现)
                                    │                     │                     │
                                    ▼                     ▼                     ▼
                              subprocess.run()       搜索引擎/爬虫          LLM API
                                    │                     │                     │
                                    └─────────────────────┴─────────────────────┘
                                                          │
                                                          ▼
                                              WeixinAPI.send_text_message()
                                                          │
                                    ◀─────────────────────┘

  4 web hook
  增加到web调用接口，推到内部后，异步给消息循环发到微信。

  ┌─────────────────┐      POST /webhook/send       ┌─────────────────┐
│   外部系统       │ ─────────────────────────────▶│  WebhookServer  │
│ (监控/CI/CD等)   │                             │   (aiohttp)     │
└─────────────────┘                             └────────┬────────┘
                                                         │
                                              asyncio.Queue
                                                         │
                              ┌──────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  _webhook_consumer│  ◀── Bot 内部消费者
                    │   (异步循环)      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  WeixinAPI      │
                    │ send_text_message│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   微信用户       │
                    └─────────────────┘

      
