# bililive-cli 补丁说明

上游：github.com/Arcadi4/bililive-cli（v0.1.0）
本仓库 `bin/bililive` 是打过下面两个补丁后重编的（linux/amd64）。

两个补丁都已向上游反馈（PR #3 / Issue #4），等上游合并后可直接用官方版。

## 补丁一：WebSocket 拨号器走代理

文件：`bili/danmaku.go`

原版 `websocket.Dialer` 没配代理，在需要代理的环境里连不上弹幕服务器。

```diff
- dialer := websocket.Dialer{HandshakeTimeout: 10 * time.Second}
+ dialer := websocket.Dialer{HandshakeTimeout: 10 * time.Second, Proxy: http.ProxyFromEnvironment}
```

（`net/http` 本来就 import 了。）

## 补丁二：放宽握手时的 Connection 头校验

文件：`go.mod`

B站弹幕服务器 101 响应里没有 `Connection: upgrade` 头，gorilla/websocket 的严格校验会拒收握手。

```diff
+ replace github.com/gorilla/websocket => ./third_party/websocket
```

`third_party/websocket` 是把 gorilla/websocket 的握手校验放宽后的本地版本（仅改校验逻辑）。

## 自己编译

```bash
git clone https://github.com/Arcadi4/bililive-cli && cd bililive-cli
# 应用上面两个补丁
go build -o bililive .
```
