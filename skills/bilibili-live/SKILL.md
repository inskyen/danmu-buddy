---
name: "bilibili-live"
description: "B站直播间操作：终端弹幕姬登录、实时看弹幕、发弹幕暖场/水群。触发词：B站直播间、发弹幕、暖场、去直播间看看、水群。"
---

# bilibili-live

## Purpose

通过终端弹幕姬 `bililive` 操作哔哩哔哩直播间：实时看弹幕、发弹幕暖场/水群、陪聊。查在播、看弹幕、发弹幕一律走 CLI。

## 工具

`bin/bililive`（本仓库自带，linux/amd64，已打补丁，开箱即用）。
上游：github.com/Arcadi4/bililive-cli，补丁说明见 `patches/bililive-fixes.md`。
WebSocket 直连弹幕，实时约 1–2 秒延迟。

- 登录：`bililive login`（终端打印二维码，用 B站 App 扫码）；会话存 `~/.cache/bililive-cli/`，一次登录长期有效。
- 查身份：`bililive whoami`；退出：`bililive logout`（仅主人明确说下线/退出时执行）。
- 看弹幕：`bililive watch <room_id> --plain --unicode -q`（`--plain` 纯文本易解析，`-q` 过滤进场/点赞噪音；自带断线重连）。
- 看弹幕（含原始协议）：`bililive watch <room_id> --debug --plain --unicode -q` —— stdout 仍是 plain 文本，stderr 额外输出每条协议事件的原始 JSON（含 `DANMU_MSG` 的完整 info，其 `extra` 里有 `reply_uname` 字段，能识别 B站 App"回复"功能的指向；注意 body 超长会被截断，发送者/正文以 plain 为准）。
- 发弹幕：`bililive send <room_id> "内容"`。
- @/回复侦测器：`scripts/mentions_watcher.py <debug_log> <plain_log> <mentions_log>` —— tail `--debug` 的 stderr 日志，从 `reply_uname` 揪出"回复给目标"的弹幕，再按时间戳到 plain 日志找回发送者与正文，写入 mentions.log（@专线）。文本 @（`@名字`）本来就在 plain 日志里，这个脚本只补"回复"型隐形 @。目标名改脚本内 `TARGETS`。
- 注意：B 站自 2025 年起拒绝匿名弹幕连接，**看和发都必须先登录**。

## Workflow（CLI 折叠方式）

1. `bililive whoami` 确认登录；未登录则 `bililive login` 走扫码。
2. 后台起监听（一路 `--debug` 同时出两种流）：`bililive watch <room_id> --debug --plain --unicode -q >> room-<room_id>.log 2>> room-<room_id>.debug.log`（background 记下 session）。再起 @ 侦测器：`python3 scripts/mentions_watcher.py room-<room_id>.debug.log room-<room_id>.log room-<room_id>.mentions.log`（background）。最终形态：1 个 bililive + 1 个 watcher，勿重复起监听。
3. `tail` 日志看现场：标题、聊天话题和氛围；在播与否以是否有弹幕流为准——连接健康但 1-2 分钟零弹幕，视为未在播或无观众。
4. 发弹幕互动：
   - 风格按话术 skill（如 live-companion-chat），默认像真人水友，一次一条；
   - 回复某条弹幕时称呼发送者 ID：不超过 4 字照念，超过取"前 2 + 后 2"；
   - 读上下文再接话：看日志尾部十几行找钩子，可接梗、押韵、组队玩；
   - 频率：主人指定节奏照办；无人指定时自然（有话接再发）；
   - 禁止"哈哈""666"式凑数，内容贴合当前聊天。
5. 发完后 `grep` 日志确认自己的弹幕回流（`<伴聊昵称>:` 前缀），即广播成功。
6. 主人说"停"/"快跑"/"下线"：立即停发；kill 关掉监听（如下线再 `bililive logout`），交回确认。

## Operating Rules

- 禁止：送礼物、点关注、改账号设置、发重复内容刷屏、透露账号/密码/个人信息。
- 遇到风控提示、禁言、发送失败：立即停手并交回说明，等主人指示。
- 房间未在播（以 watch 日志有无弹幕流为准）：直接交回，不发弹幕（可保持监听等开播，主人要求时）；绝不对着空房间发弹幕试探。
- 切房间：先 kill 旧监听、旧 watcher 和旧 asr_watcher，再起新房间的监听 + watcher（日志分文件：`room-<room_id>.log` / `.debug.log` / `.mentions.log` / `.asr.log`）。

## 主播语音转写（B站原生 AI 字幕）

- B站直播间若主播开了实时字幕，`bililive watch --debug` 的 stderr 日志里自带 `UNIVERSAL_ASR_TEXT` 事件（B站官方语音转写，无需自建 ASR）。
- 抓取脚本：`scripts/asr_watcher.py <debug_log> <asr_log> <streamer_uid>`，输出 `HH:MM:SS [主播/连麦] 昵称: 文字`（北京时间），按 (uid, start_time, text) 去重。
- 伴聊时可 tail `.asr.log` "听见"主播说话，结合弹幕接话；字幕有十几秒延迟，别抢话。

## Output Contract

任务结束交回：房间是否在播、在播什么、发了哪几条弹幕（原文）、聊天区氛围、监听是否已关。
