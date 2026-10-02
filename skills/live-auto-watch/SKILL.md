---
name: "live-auto-watch"
description: "B站开播自动监测与进场伴聊：轮询房间开播状态，开播自动起监听、派伴聊分身进场，下播自动收工。触发词：开播提醒、自动进场、开播监测、盯直播间。"
---

# 开播自动监测与进场伴聊

## Purpose

把"蹲开播"变成自动化流水线：每 5 分钟轮询监测名单，一开播就自动起弹幕监听、派伴聊分身进场伴聊；下播自动关监听收工。话术与风格规则见 `live-companion-chat` skill，本 skill 只管"进场"这条线。

## Tooling

- 轮询器：`scripts/live_poller.py`（标准库 only，免登录；`ROOMS` 字典即监测名单）
- 状态：`live_state.json`（0/1；首次运行只建基线、不报警）
- 定时：cron 每 5 分钟跑一次轮询器，把 EVENT 行交回
- 进场：`bililive watch <room_id> --debug --plain --unicode -q`（stdout→plain 日志，stderr→debug 日志）＋ `scripts/mentions_watcher.py`（@ 侦测，见 `bilibili-live` skill）
- 发送：`bililive send <room_id> "内容"`，发后 grep 日志确认 `<伴聊昵称>:` 回流
- 现场手册：`scripts/companion_brief.md`（分身指令全文：风格、节奏、风控、收工）
- 看门狗：每 20 分钟跑一次；在播无监听→报 NEED_ENTRY 补进场；下播有残留→报 STALE_SESSION 收工；正常时静默
- 进场锁：`active-session.json`（进场时写，收工时删；防重复进场）

## Workflow

1. **加/减监测名单**：改 `live_poller.py` 的 `ROOMS`，删 `live_state.json` 让下轮重建基线（避免名单变动造成误报）。
2. **开播**（cron 交回 `EVENT LIVE | <name> | <room_id> | <title>`）：主智能体在 handoff 回合执行——两种模式：
   - **提醒模式**：只通知主人开播了，不自动进场、不起监听、不派分身；主人说"去"才进场。
   - **自动进场模式**：`bililive whoami` 确认登录态 → 后台起 `watch` 监听 → 起 mentions watcher → spawn 伴聊分身（指令按 companion_brief.md）。
   - 默认用哪种模式，主人拍板。
3. **伴聊中**：分身按 brief 自主决策回哪条、怎么回；只在禁言/风控/主播要求安静时上报；花钱（送礼）先提议，主人亲手来。
4. **下播**（`EVENT OFFLINE`）：kill 监听与 watcher，分身收工交回（发了几条、在播内容、氛围）。
5. **主人喊停**："停/快跑/回来" → 立即停发并关监听，不预约下次。

## Operating Rules

1. 监测名单的增减是主人的拍板权。
2. 在播与否以 watch 日志有无弹幕流为准；1–2 分钟零弹幕视为无观众，绝不对着空房间发弹幕试探。
3. 风控三停：发送失败/禁言/限流 → 立即停手并上报，等指示再动。
4. 永久忽略名单见 `live-companion-chat` skill：不回复、不评审，被@也不接。
5. 演习用"只看不发"：借别人正在播的房间测试进场时，只做监听＋拟回复，不实际发送测试弹幕。
6. 看门狗是安全网：正常进场走 `EVENT LIVE`；若 handoff 漏接、监听中途死亡，看门狗会报 `NEED_ENTRY` 补进场、`STALE_SESSION` 补收工。
