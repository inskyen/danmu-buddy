# 开播自动伴聊流程（分身现场手册）

触发：live_poller 报 `EVENT LIVE | <name> | <room_id> | <title>`。

## 1. 起监听（主智能体在 handoff 回合执行）

```bash
export PATH="$HOME/.local/bin:$PATH"
bililive whoami  # 确认登录态
# 后台起监听（一路 --debug 同时出两种流）
bililive watch <room_id> --debug --plain --unicode -q \
  >> room-<room_id>.log \
  2>> room-<room_id>.debug.log
# 起 @ 侦测器
python3 scripts/mentions_watcher.py \
  room-<room_id>.debug.log \
  room-<room_id>.log \
  room-<room_id>.mentions.log
# 写进场锁（防重复进场）
python3 -c "
import json, time
json.dump({'room_id':'<room_id>','room_name':'<name>','entered_at':time.time()},
          open('active-session.json','w'), ensure_ascii=False)
"
```

进场前先看一眼锁：如果 `active-session.json` 里已是该房间且 10 分钟内，
或已有 `bililive watch <room_id>` 进程在跑 → 说明已进场，直接复用，不起第二套。

## 2. 派伴聊分身

spawn 一个 subagent 带这个房间出去伴聊（分身只干活：看弹幕、写弹幕、回来汇报）。

分身指令要点：

- 风格：见 live-companion-chat skill（气质配方、汪曾祺语感、去人机感、说人话）
- 弹幕一律**不用任何标点符号**；回复带对方 ID 前2字＋后2字（不超过4字照念）
- **不主动回怼**：不挑事、不找茬；遇到引战/人身攻击，冷处理不接招
- 红线：**绝不跟人对线**；不说脏话；不攻击家人外貌隐私；刻薄只走刀法不走脏口
- 节奏：有话接再发，不刷屏凑数；`bililive send <room_id> "内容"`，发完 grep 日志确认回流（`<伴聊昵称>:` 前缀）
- 风控：发送失败/禁言/限流 → 立即停手，上报主智能体
- 在播判断：以 watch 日志有无弹幕流为准；1-2 分钟零弹幕视为无观众，不自言自语刷屏
- 下播（轮询报 OFFLINE 或主播长时间离线）→ kill 监听与 watcher，收工交回

## 3. 上报规则

- 回哪条、怎么回，分身自己决策，**不用先发主人过目**
- 只在大事上回来汇报：禁言、风控、主播要求安静
- 花钱（送礼物）：先提议，主人亲手来

## 4. 收工

- 房间下播 → kill 关监听，删 `active-session.json`（清进场锁），交回：本场发了几条、在播内容、氛围
- 主人说"停"/"快跑" → 立即停发并关监听，清进场锁
