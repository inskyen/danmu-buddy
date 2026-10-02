#!/usr/bin/env python3
"""@ / 回复 侦测器：tail bililive --debug 的 stderr 日志，从 DANMU_MSG 的 extra 里
揪出 reply_uname == 目标 的弹幕（即有人点了"回复"伴聊号），再到 plain 日志里按
时间戳找回发送者和正文，写入 mentions.log 供伴聊优先回复。

为什么需要两份日志：--debug 的 body 会被截断（~1530 字符，extra 里就没了），
发送者/正文不在其中；但时间戳对得上 plain 日志。
文本 @（@昵称）本来就在 plain 日志里，这里只补"回复"这种隐形 @。

用法: mentions_watcher.py <debug_log> <plain_log> <mentions_log>
"""
import re, sys, time

if len(sys.argv) < 4:
    print("用法: mentions_watcher.py <debug_log> <plain_log> <mentions_log>",
          file=sys.stderr)
    sys.exit(1)

DEBUG_LOG = sys.argv[1]
PLAIN_LOG = sys.argv[2]
MENTIONS_LOG = sys.argv[3]

# 改成你的伴聊号昵称（可多个）
TARGETS = ("<你的B站昵称>",)
# 伴聊号自己发的前缀，plain 日志里形如 "HH:MM:SS 昵称: 内容"
SELF_PREFIX = "<你的B站昵称>:"

# reply_uname 藏在 extra（JSON 字符串的 JSON）里，文件里是三重转义 \\\"
REPLY_RE = re.compile(r'reply_uname\\\\\\":\\\\\\"([^"\\\\]*)\\\\\\"')
TS_RE = re.compile(r'time=\S+T(\d{2}:\d{2}:\d{2})')

def find_plain(ts, tries=4):
    """在 plain 日志里找该秒的弹幕行（排除伴聊号自己）"""
    for _ in range(tries):
        hits = []
        try:
            with open(PLAIN_LOG, encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.startswith(ts + " "):
                        body = line[len(ts) + 1:].strip()
                        if body and not body.startswith(SELF_PREFIX) and not body.startswith("▶"):
                            hits.append(body)
        except FileNotFoundError:
            pass
        if hits:
            return hits
        time.sleep(1)
    return []

def main():
    out = open(MENTIONS_LOG, "a", encoding="utf-8")
    with open(DEBUG_LOG, encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)  # 只跟新到的
        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue
            if "cmd=DANMU_MSG" not in line:
                continue
            m = REPLY_RE.search(line)
            reply_to = m.group(1) if m else ""
            if reply_to not in TARGETS:
                continue
            tm = TS_RE.search(line)
            ts = tm.group(1) if tm else time.strftime("%H:%M:%S")
            cands = find_plain(ts)
            if cands:
                for c in cands:
                    out.write(f"{ts} [回复@{reply_to}] {c}\n")
            else:
                out.write(f"{ts} [回复@{reply_to}] （正文未在 plain 日志中找到）\n")
            out.flush()

if __name__ == "__main__":
    main()
