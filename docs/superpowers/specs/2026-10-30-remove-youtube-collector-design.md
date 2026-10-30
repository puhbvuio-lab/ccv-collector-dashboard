# 移除内置 YouTube 采集器设计

## 意图

本项目回归 Twitch CCV 采集与报告工具，不再包含或运行任何 YouTube 采集实现。看板只保留一个通往未来独立 YouTube 工具的外部跳转入口，两套工具不交换任务、状态或采集数据。

## 用户可见行为

- 任务创建表单只支持 Twitch 游戏和 Twitch 频道。
- 看板标题与说明不再宣称支持 YouTube 双平台。
- 看板显示“打开 YouTube 采集工具”按钮。
- `config.json.youtube_tool_url` 为有效的 `http://` 或 `https://` 地址时，按钮在新标签页打开该地址。
- 配置为空或不是 HTTP(S) 地址时，按钮显示“待配置”并禁用，不生成可点击跳转。

## 删除范围

- 删除 `server.py` 中的 YouTube URL 解析、oEmbed 查询、Data API 采集器、YouTube 任务创建与运行分支。
- 删除 `yt_web_pilot.js`。
- 删除 `.env.example` 和运行时代码中的 `YOUTUBE_API_KEY`。
- 删除 README、package 描述和工作流文档中的内置 YouTube 采集说明。
- 删除仓库 `examples/` 中明确属于 YouTube 的示例产物；不删除 `data/`、`输出/` 等被忽略的用户运行数据。

## 保留范围

- 保留 Twitch API 采集、Twitch 网页双通道、暂停/恢复/停止、趋势、CSV/Excel 导出与报告能力。
- 报告代码保持对已有通用 CSV/JSON 数据的兼容，不为外部 YouTube 工具增加导入或通信协议。
- 已持久化的历史 YouTube 任务不自动执行；加载时标记为 `unsupported`，避免旧任务在升级后触发异常或被误当成运行中。

## 实现方案

新增一个小型 URL 规范化函数，只接受 HTTP(S) URL。服务启动时读取 `youtube_tool_url` 并安全注入看板按钮；不新增 API 端点。测试覆盖有效链接、空配置、危险协议、YouTube 任务拒绝、历史任务停用以及 Twitch 任务不受影响。

## 非目标

- 不启动、探测或监控外部 YouTube 工具。
- 不定义外部工具的数据格式。
- 不自动迁移或删除用户已有采集数据。
