#!/usr/bin/env python3
"""伴聊轮询驱动：取新弹幕+新mentions，按本地规则筛出候选，输出JSON。

不依赖外部评审模型：候选按"是否被@/主人发言/钩子强度"打标，
最终回哪条、怎么回，由伴聊智能体按 live-companion-chat 的活跃度标准自己判断。
用法: companion_driver.py <plain_log> <mentions_log>
"""
import json, re, sys

if len(sys.argv) < 3:
    print("用法: companion_driver.py <plain_log> <mentions_log>", file=sys.stderr)
    sys.exit(1)

PLAIN = sys.argv[1]
MENT = sys.argv[2]
OFF = "/tmp/companion.offset"

# 换成自己的
SELF = "<你的B站昵称>"      # 伴聊号自己
OWNER = "<主人B站ID>"       # 主人，最高优先级
IGNORE = ("<忽略ID>",)      # 永久忽略名单
# 主播喊停关键词
SILENCE_WORDS = ("安静", "闭嘴", "别说话", "别吵")

def read_offsets():
    try:
        a, b = open(OFF).read().split()
        return int(a), int(b)
    except Exception:
        return 0, 0

def write_offsets(a, b):
    open(OFF, "w").write(f"{a} {b}\n")

def new_lines(path, frm):
    try:
        lines = open(path, errors="replace").read().splitlines()
    except FileNotFoundError:
        return [], frm
    return lines[frm:], len(lines)

# danmaku line format: "HH:MM:SS 用户名: 内容" (also "xxx 来了" join notices)
m = re.compile(r"^(\d{2}:\d{2}:\d{2}) ([^:]+): (.*)$")

def hook_strength(text):
    """本地钩子强度：提问/点名/玩梗 > 普通发言。只做粗筛，最终由智能体判断。"""
    if "?" in text or "？" in text or text.strip().endswith("吗"):
        return "question"
    if len(text.strip()) >= 8:
        return "chatty"
    return "plain"

po, mo = read_offsets()
plines, ptotal = new_lines(PLAIN, po)
mlines, mtotal = new_lines(MENT, mo)

cands, mentions, stops = [], [], []
for ln in plines:
    s = ln.strip()
    if not s:
        continue
    if "stream cut off" in s or "stream ended" in s or "切断直播流" in s:
        stops.append({"type": "stream_ended", "line": s[:80]})
        continue
    mm = m.match(s)
    if not mm:
        continue  # join notices etc.
    ts, user, text = mm.groups()
    if user == SELF or user in IGNORE or not text.strip():
        continue
    # 主播喊停检测
    if any(k in text for k in SILENCE_WORDS):
        stops.append({"type": "silence", "user": user, "line": s[:80]})
        continue
    cands.append({"ts": ts, "user": user, "text": text,
                  "owner": user == OWNER,
                  "hook": hook_strength(text)})

for ln in mlines:
    s = ln.strip()
    if s:
        mentions.append(s[:120])

write_offsets(ptotal, mtotal)
print(json.dumps({"candidates": cands, "mentions": mentions, "stops": stops,
                  "plain_total": ptotal, "ment_total": mtotal},
                 ensure_ascii=False, indent=1))
