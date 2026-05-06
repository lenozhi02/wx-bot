# WX-BOT 插件目录

本目录存放所有动态插件。插件支持**热加载**，无需重启服务即可增删改。

## 目录结构

```
plugins/
├── echo/                    # 插件 ID = 目录名
│   ├── manifest.json        # 插件元数据
│   └── handler.py           # 处理器实现
│
├── reminder/
│   ├── manifest.json
│   └── handler.py
│
└── README.md                # 本文件
```

## 快速创建插件

1. 创建目录：`mkdir plugins/my_plugin`
2. 编写 `manifest.json` 和 `handler.py`
3. 打开 Web UI → 插件中心 → 点击 **"重载全部"**

详细开发指南请查看：`docs/PLUGIN_DEVELOPER_GUIDE.md`

## 现有插件

| 插件 | 类型 | 触发词 | 说明 |
|------|------|--------|------|
| `echo` | 同步 | `echo`、`复读` | 复读用户消息 |
| `reminder` | 后台 | `remind`、`提醒` | 异步提醒示例，演示进度上报 |

## 注意事项

- 目录名以 `_` 或 `.` 开头的会被忽略
- `manifest.json` 格式错误会导致该插件被跳过
- 卸载插件时会清理 Python 模块缓存，确保下次加载的是最新代码
