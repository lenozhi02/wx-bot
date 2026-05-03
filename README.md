# wx-bot
微信机器人设计文档
1. 项目概述
本项目是一个基于微信 iLink Bot API 的本地命令执行机器人。用户通过微信发送文本指令，机器人在本地安全执行预设命令并返回结果。
主体参考 https://github.com/co-pine/wx-robot-ilink/
web接口方便外部数据随时推送到微信端，减少bot主体工作量。把wx-bot理解成个壳就好了，想干啥就在外面做，定时也好，一次性也好，结果推给web接口。



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

  例：

  curl -X POST http://localhost:18789/webhook/send   -H "Content-Type: application/json"   -d '{
    "data": {"name": "CPU", "value": "85%"},
    "template": "🔥 {name} 告警: {value}"
  }'

<img width="1264" height="2736" alt="_cgi-bin_mmwebwx-bin_webwxgetmsgimg__ MsgID=5057204888755059850 skey=@crypt_2b89c929_c50451fc47b9fb6c3d0f7a7d0e33dd42 mmweb_appid=wx_webfilehelper" src="https://github.com/user-attachments/assets/8a4b5dc6-9067-490c-9ccd-b17756d7fce5" />

  

3. 架构设计


<img width="1460" height="674" alt="image" src="https://github.com/user-attachments/assets/77313473-95af-4938-a3d3-a3392154c76a" />



3 数据流图

<img width="1664" height="744" alt="image" src="https://github.com/user-attachments/assets/9763378b-d130-4b17-8e06-674c87c455cf" />

  4 web hook
  增加到web调用接口，推到内部后，异步给消息循环发到微信。

<img width="1308" height="998" alt="image" src="https://github.com/user-attachments/assets/2f75c40b-8bd6-4d35-8b3b-4a4b8a9b45d4" />


      
