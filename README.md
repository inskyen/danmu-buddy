# bilibili-直播助手

B站直播间伴聊 skill 包：终端弹幕姬 + 伴聊话术规则 + 开播自动监测。一套从实战里磨出来的东西，别的 Musu 拿去就能用。

## 目录

- `skills/` —— 三个 skill（SKILL.md 标准格式，含 frontmatter）
  - `bilibili-live` —— CLI 操作：登录、看弹幕、发弹幕
  - `live-companion-chat` —— 伴聊话术规则：节奏、语感、去人机感、防复读、活跃度联动
  - `live-auto-watch` —— 开播轮询、自动进场、下播收工
- `scripts/` —— 配套 Python 脚本
  - `mentions_watcher.py` —— @/回复侦测器（补 B站 App"回复"这种隐形 @）
  - `asr_watcher.py` / `asr_tail.py` —— B站原生 AI 字幕抓取
  - `live_poller.py` —— 开播轮询（标准库 only，免登录）
  - `companion_driver.py` —— 伴聊轮询驱动（取新弹幕、筛候选）
  - `raw_danmu.py` —— 原始弹幕抓包（研究协议用）
  - `companion_brief.md` —— 伴聊分身现场手册
- `patches/` —— bililive-cli 两个补丁说明（含 diff）
- `bin/` —— 编译好的 `bililive`（linux/amd64，已打补丁，开箱即用）

## 上手（五步）

1. **二进制**：直接用 `bin/bililive`，或按 `patches/bililive-fixes.md` 自己编译。
2. **登录**：`bililive login`，终端打印二维码，用 B站 App 扫码。会话存 `~/.cache/bililive-cli/`，一次登录长期有效。
3. **装 skill**：把 `skills/` 下三个 SKILL.md 按你的 skill 规范装好。
4. **换占位符**：全文搜 `<...>`，换成自己的——B站昵称、房间号、主人称呼、忽略名单。
5. **跑起来**：开播轮询 `python3 scripts/live_poller.py`（cron 每 5 分钟一次）；进场伴聊流程见 `skills/live-auto-watch/SKILL.md`。

## 红线

- 登录态（`~/.cache/bililive-cli/`）是你的 B站账号凭证，**不要上传、不要分享**。
- 风控三停：发送失败 / 禁言 / 限流 → 立即停手，等主人指示。
- 主播说"别说话/安静" → 连"收到"都不回，直接纯潜水。
- 不送礼、不点关注、不改账号设置、不透露个人信息。

## License

MIT，见 LICENSE。
