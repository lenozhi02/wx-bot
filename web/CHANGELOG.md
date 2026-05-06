# WX-BOT Web UI 变更记录

## [1.1.0] 2026-05-05 — 像素风 UI + 任务状态同步修复

### 新增

- **像素风 Dashboard 首页**
  - 像素房间场景（checkerboard 地板、砖墙、家具）
  - Bot 角色根据状态在不同区域移动（办公桌/沙发/服务器区）
  - 状态气泡实时显示当前活动
  - 服务器机柜忙碌度可视化（LOAD % + 闪烁频率）

- **多任务协作可视化**
  - 主角色处理当前任务，小助手 NPC（👾🐱🦎）显示排队任务
  - 任务完成后小助手淡入淡出动画
  - 多任务时角色头顶显示 "xN 任务" 堆叠标记

- **任务"收尾中"状态**
  - 任务完成后保留 5 秒"收尾中"显示
  - 角色气泡变为 `✅ 收尾中...`
  - 服务器机柜显示 `✅ 收尾中` 指示

- **React Router 多页面**
  - Dashboard（像素房间 + 三栏面板）
  - Mission Control（任务列表 + 筛选 + 详情抽屉）
  - System Charts（Recharts CPU/内存趋势图）
  - Plugin Hub（插件中心 + 扩展面板）

### 修复

#### P0 — 极快任务 UI 不更新（React 批量更新导致事件丢失）

**问题描述：**
执行 `百度 盛诺一家 ...`（脚本有缓存，几毫秒内完成）时，UI 不显示任务状态；
执行 `百度 中山一院 ...`（无缓存，几十秒搜索）时，UI 正常更新。

**根因分析：**
React 18 的自动批量更新机制，当 `task:started` 和 `task:completed` 在 <1ms 内连续到达时：
1. 两次 `setEvents()` 被批量为一次渲染
2. `useEffect` 只执行一次，只取 `events[events.length-1]`（即 completed）
3. 处理 completed 时，`activeTasks` 中找不到 taskId（因为 started 的 `setActiveTasks` 尚未生效）
4. 结果直接 fallback 到 idle，UI 无变化

**修复方案：**
- `processedCount` ref 记录已处理的事件索引
- `activeTasksRef` / `finishingTasksRef` ref 实时维护任务列表（避免 setState 闭包延迟）
- `useEffect` 中遍历 `ws.events.slice(processedCount)` 逐个处理所有新事件
- 所有事件处理完成后，统一批量更新 state

**影响文件：** `web/src/contexts/WebSocketContext.tsx`

#### P1 — 初始加载显示骷髅头（错误状态）

**问题描述：**
页面刚打开时 `ws.connected` 初始为 `false`，`useEffect` 立即把 `activity` 设成 `error`（骷髅头）。

**修复方案：**
使用 `prevConnected` ref 记录上一次的连接状态，只在"从连接变为断开"时才设为 error，初始加载保持 idle。

### 技术栈

- React 19 + TypeScript
- React Router 7
- Tailwind CSS v4（像素风配色系统）
- Recharts（系统监控图表）
- WebSocket 实时事件流
- FastAPI 静态文件服务
