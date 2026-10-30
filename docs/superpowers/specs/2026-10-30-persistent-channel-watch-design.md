# Twitch 直播间持续守望设计

## 意图

一个频道任务从创建开始持续存在，在“等待开播”和“直播采集”之间自动切换。未开播时只查询直播状态；开播后记录 CCV；下播后回到等待状态。任务只因用户暂停、停止或删除而中断，不因单场直播结束而自动结束。

## 适用范围

- 持续守望仅适用于 Twitch `channel` 任务。
- Twitch `game` 分类任务继续使用现有持续轮询方式，但使用新的直播采样间隔字段。
- API + Twitch 网页双通道暂不支持双速率切换；双通道任务继续使用直播采样间隔，避免 API 与网页进程节拍失配。

## 配置与兼容

- `watch_interval_seconds`：等待开播时的查询间隔，默认 30 秒，最低 5 秒。
- `live_interval_seconds`：直播期间的 CCV 采样间隔，默认 30 秒，最低 5 秒。
- 看板提供两个独立数字输入框，用户可分别调整。
- 旧任务只有 `poll_interval_seconds` 时，该值同时作为两个新间隔的回退值。
- 新任务仍写入 `poll_interval_seconds = live_interval_seconds`，供现有报告、网页双通道和旧读取逻辑兼容。
- `monitor_duration_minutes` 对频道持续守望任务不再作为自动终止条件；频道任务只由用户控制结束。游戏分类任务维持原有时长行为。

## 状态机

```text
waiting（等待开播）
  └─ 每 watch_interval_seconds 查询频道
       └─ 发现直播 → live

live（直播采集）
  └─ 每 live_interval_seconds 查询并写入 CCV
       └─ 连续 2 次查询为空 → waiting

任意状态
  ├─ pause → paused（不查询、不采集）
  ├─ resume → 回到原循环
  └─ stop/delete → 结束任务
```

第一次空查询只作为下播候选，第二次连续为空才确认下播并切回等待。若中间重新读到直播，计数清零。

## 数据行为

- 等待状态不追加 raw JSONL 或直播 CSV，只更新 heartbeat，明确写入 `phase: waiting`、两个间隔与下一轮使用的间隔。
- 直播状态继续按现有格式写入 raw、单场 CSV、汇总与状态文件。
- 每次新开播使用 Twitch 返回的新 `stream_id`，形成独立场次；旧场次保留为 `ended`。
- 下播确认后不结束 session 或任务线程。

## 看板行为

- “开播守望”不再是可选复选框；频道任务默认始终持续守望。
- 表单显示“未开播检查间隔”和“开播采样间隔”，默认均为 30 秒。
- 任务卡片在 `heartbeat.phase == waiting` 时显示“守望中 · 等待开播”，直播时显示正常 CCV。
- 文案不再出现“下播后自动停止”。

## 非目标

- 不增加 Twitch EventSub、Webhook 或 WebSocket；仍使用现有 Helix API 轮询。
- 不改变 CSV/JSON 的已有字段格式。
- 不让外部 YouTube 工具参与该状态机。
