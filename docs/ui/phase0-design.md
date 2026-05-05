# Phase 0: 文档规范 + 项目结构

## 设计目标

建立完整的文档体系和项目结构，为后续 Phase 的逐步实施奠定基础。

## 新增目录结构

```
wx-bot/
├── docs/ui/                    # UI 设计文档
│   ├── README.md               # 文档索引
│   ├── phase0-design.md        # 本文件
│   ├── phase0-changelog.md     # 变更记录
│   └── phase0-test-report.md   # 测试报告
├── src/ui/                     # 后端 UI 模块
│   ├── __init__.py
│   ├── bus.py                  # 事件总线（Phase 1）
│   ├── server.py               # FastAPI 服务（Phase 2）
│   ├── hub.py                  # WebSocket Hub（Phase 2）
│   ├── services/               # 服务层
│   │   ├── __init__.py
│   │   ├── bot_svc.py          # Bot 状态服务
│   │   ├── task_svc.py         # 任务监控服务
│   │   ├── sys_svc.py          # 系统采集服务
│   │   └── plugin_svc.py       # 插件管理服务
│   ├── api/                    # REST API
│   │   ├── __init__.py
│   │   ├── bot.py
│   │   ├── tasks.py
│   │   ├── system.py
│   │   └── plugins.py
│   └── plugins/                # 内置插件
│       └── __init__.py
├── web/                        # 前端代码（Phase 3）
│   └── (待创建)
└── tests/ui/                   # UI 测试
    └── (待创建)
```

## 设计原则

1. **低耦合**：`src/ui/` 作为独立模块，不修改现有核心业务逻辑
2. **事件驱动**：通过事件总线与现有代码通信，现有代码通过埋点触发事件
3. **渐进式**：每个 Phase 可独立运行，不阻塞其他功能

## 接口约定

### 事件命名规范

```
{domain}:{action}

# domain: bot | task | sys | webhook
# action: event 类型

bot:message_received    # 收到微信消息
bot:message_sent        # 发送微信消息
bot:connected           # Bot 连接成功
bot:disconnected        # Bot 连接断开

task:submitted          # 任务提交
task:started            # 任务开始执行
task:progress           # 任务进度更新
task:completed          # 任务完成
task:failed             # 任务失败

sys:metrics             # 系统指标更新
sys:alert               # 系统告警

webhook:received        # 收到 Webhook 请求
webhook:delivered       # Webhook 消息已推送
```
