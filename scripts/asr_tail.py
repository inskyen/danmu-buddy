#!/usr/bin/env python3
"""从 bililive debug 日志提取主播实时语音字幕(UNIVERSAL_ASR_TEXT)。
用法: python3 asr_tail.py <debug_log> [N]  -> 最近 N 句(默认10), 输出 "HH:MM:SS 文本"
"""
import json, sys
if len(sys.argv) < 2:
    print("用法: asr_tail.py <debug_log> [N]", file=sys.stderr)
    sys.exit(1)
out = []
with open(sys.argv[1], encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'UNIVERSAL_ASR_TEXT' not in line:
            continue
        i = line.find('body="')
        j = line.rfind('"')
        if i < 0 or j <= i + 6:
            continue
        inner = line[i + 6:j]
        raw = inner.replace('\\\\', '\\').replace('\\"', '"')
        try:
            d = json.loads(raw)
        except Exception:
            continue
        ts = line.split('time=')[1].split()[0] if 'time=' in line else '?'
        for s in d.get('data', {}).get('sentences', []):
            t = s.get('text', '').strip()
            if t:
                out.append((ts, t))
n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
for ts, t in out[-n:]:
    print(ts[11:19], t)
