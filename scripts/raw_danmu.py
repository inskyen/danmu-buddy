#!/usr/bin/env python3
"""B站直播原始弹幕抓包：直连 B站弹幕 WebSocket，把 DANMU_MSG 等原始 JSON 逐行记入 jsonl。
用于研究 @/回复 在协议层的真实形态（bililive --plain 会丢掉这些元数据）。
用法: raw_danmu.py <room_id> <out_jsonl>
"""
import json, struct, sys, time, zlib, threading
import urllib.request
import websocket

if len(sys.argv) < 3:
    print("用法: raw_danmu.py <room_id> <out_jsonl>", file=sys.stderr)
    sys.exit(1)

ROOM = sys.argv[1]
OUT = sys.argv[2]

def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=15))

def pack(op, body=b"", ver=1, seq=1):
    h = struct.pack(">IHHII", 16 + len(body), 16, ver, op, seq)
    return h + body

def main():
    info = api(f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={ROOM}")
    real_id = info["data"]["room_id"]
    conf = api(f"https://api.live.bilibili.com/room/v1/Danmu/getConf?room_id={real_id}&platform=pc&player=web")
    host = conf["data"]["host_server_list"][0]["host"]
    token = conf["data"]["token"]
    out = open(OUT, "a", encoding="utf-8")

    def on_message(ws, msg):
        off = 0
        while off + 16 <= len(msg):
            plen, hlen, ver, op, seq = struct.unpack(">IHHII", msg[off:off+16])
            body = msg[off+hlen:off+plen]
            off += plen
            if ver == 2:
                try:
                    body = zlib.decompress(body)
                except Exception:
                    continue
                inner = body
                ioff = 0
                pkts = []
                while ioff + 16 <= len(inner):
                    pl, hl, v, o, s = struct.unpack(">IHHII", inner[ioff:ioff+16])
                    pkts.append((o, inner[ioff+hl:ioff+pl]))
                    ioff += pl
                for o, b in pkts:
                    handle_op(ws, o, b, out)
                continue
            handle_op(ws, op, body, out)

    def handle_op(ws, op, body, out):
        if op == 5:
            try:
                d = json.loads(body.decode("utf-8", "replace"))
            except Exception:
                return
            cmd = d.get("cmd", "")
            if cmd in ("DANMU_MSG", "SUPER_CHAT_MESSAGE", "SEND_GIFT"):
                rec = {"ts": time.strftime("%H:%M:%S"), "cmd": cmd, "data": d.get("data") if cmd != "DANMU_MSG" else None, "info": d.get("info") if cmd == "DANMU_MSG" else None}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
        elif op == 8:
            pass  # auth ok

    def on_open(ws):
        auth = {"uid": 0, "roomid": real_id, "protover": 2, "platform": "web", "type": 2, "key": token}
        ws.send(pack(7, json.dumps(auth).encode()), ver=1)
        def hb():
            while True:
                time.sleep(30)
                try:
                    ws.send(pack(2))
                except Exception:
                    break
        threading.Thread(target=hb, daemon=True).start()

    ws = websocket.WebSocketApp(f"wss://{host}/sub", on_message=on_message, on_open=on_open)
    ws.run_forever()

if __name__ == "__main__":
    main()
