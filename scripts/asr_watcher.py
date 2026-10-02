#!/usr/bin/env python3
"""B站直播原生 AI 字幕抓取器.

bililive watch --debug 的 stderr 日志里自带 UNIVERSAL_ASR_TEXT 事件
(B站官方实时语音转写, 主播开了字幕功能就有, 无需自己搭 ASR).
本脚本 tail debug 日志, 解析出说话人和句子, 写入 asr 日志供伴聊"听见"主播说话.

用法: python3 asr_watcher.py <debug_log> <asr_log> <streamer_uid>
输出行: "18:30:15 [主播] <主播名>: 是有哦"
        "18:30:15 [连麦] 小范蠡逸三一: 他们有那个放映厅啊!"
"""
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone

DEBUG_LOG = sys.argv[1]
ASR_LOG = sys.argv[2]
STREAMER_UID = sys.argv[3]

BODY_RE = re.compile(r'body="(.*)"\s*$')
TIME_RE = re.compile(r'^time=(\S+)')
BJ = timezone(timedelta(hours=8))

seen = set()

def parse_line(line):
    m = BODY_RE.search(line)
    if not m:
        return None
    try:
        # body 是 logfmt 引号包裹的 JSON："{\\"cmd\\":...}"，
        # 只需把 \\" 还原成 "（不用 unicode_escape，它会搞坏 UTF-8 中文）。
        raw = m.group(1).replace('\\\\', '\x00').replace('\\"', '"').replace('\x00', '\\')
        obj = json.loads(raw)
    except Exception:
        return None
    if obj.get('cmd') != 'UNIVERSAL_ASR_TEXT':
        return None
    return obj.get('data') or {}

def fmt_time(line):
    m = TIME_RE.match(line)
    if m:
        try:
            dt = datetime.fromisoformat(m.group(1).replace('Z', '+00:00'))
            return dt.astimezone(BJ).strftime('%H:%M:%S')
        except Exception:
            pass
    return datetime.now(BJ).strftime('%H:%M:%S')

def main():
    out = open(ASR_LOG, 'a', encoding='utf-8')
    with open(DEBUG_LOG, encoding='utf-8', errors='replace') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            if 'UNIVERSAL_ASR_TEXT' not in line:
                continue
            data = parse_line(line)
            if not data:
                continue
            uid = str(data.get('uid', ''))
            uname = data.get('uname', '?')
            role = '主播' if uid == STREAMER_UID else '连麦'
            ts = fmt_time(line)
            for s in data.get('sentences') or []:
                text = (s.get('text') or '').strip()
                if not text:
                    continue
                key = (uid, s.get('start_time'), text)
                if key in seen:
                    continue
                seen.add(key)
                out.write(f'{ts} [{role}] {uname}: {text}\n')
                out.flush()

if __name__ == '__main__':
    main()
