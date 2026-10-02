#!/usr/bin/env python3
"""B站直播间开播轮询。

每 N 分钟被 cron 调起一次，用 B站公开房间信息接口查 live_status，
检测 0->1（开播）/ 1->0（下播）跳变并打印 EVENT 行。
状态持久化在 live_state.json；首次运行只建状态、不报警。
标准库 only，无需登录。
"""
import json
import os
import sys
import urllib.request

STATE_PATH = os.path.expanduser("~/bilibili-live/live_state.json")

# 监测名单：{"主播名": "房间号"}，按需增减
ROOMS = {
    "<主播名>": "<room_id>",
}

API = "https://api.live.bilibili.com/room/v1/Room/get_info?room_id={}"


def fetch(room_id):
    req = urllib.request.Request(
        API.format(room_id),
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r)["data"]
    anchor = (d.get("anchor_info") or {}).get("base_info", {}) or {}
    return (
        int(d.get("live_status", 0)),
        d.get("title", "") or "",
        anchor.get("uname", "") or "",
    )


def main():
    try:
        with open(STATE_PATH) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}

    events = []
    for name, rid in ROOMS.items():
        try:
            status, title, uname = fetch(rid)
        except Exception as e:  # noqa: BLE001 - 单个房间失败不影响其他房间
            print(f"WARN {name}({rid}): {e}", file=sys.stderr)
            continue
        prev = state.get(rid)
        state[rid] = status
        tag = "LIVE" if status == 1 else "offline"
        print(f"[{tag}] {name}({rid}) {uname}《{title}》")
        if prev == 0 and status == 1:
            events.append(("LIVE", name, rid, title))
        elif prev == 1 and status == 0:
            events.append(("OFFLINE", name, rid, title))

    with open(STATE_PATH, "w") as f:
        json.dump(state, f, ensure_ascii=False)

    for kind, name, rid, title in events:
        # cron agent 只看 EVENT 行决定是否打扰用户
        print(f"EVENT {kind} | {name} | {rid} | {title}")


if __name__ == "__main__":
    main()
