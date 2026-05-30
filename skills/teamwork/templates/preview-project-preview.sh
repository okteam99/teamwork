#!/usr/bin/env bash
# preview.sh — same-stack UI 预览:编译运行 + 输出可打开 URL(动态端口)
# v8.58 teamwork · 放在 preview-project 根 · 用项目自己的 dev server(不在 teamwork 层起 server)
#
# 解决:① same-stack 预览是 ES-module bundle · file:// 因 CORS 打不开 → 必须 dev server
#       ② 并行 worktree / 多终端裸起 server 抢端口 → 本脚本每次选一个动态空闲端口 · 天然不冲突
#       ③ 设计确认时直接拿可打开 URL(PMO 抓 PREVIEW_URL= 那行给用户)
#
# 用法:
#   bash preview.sh            # 选动态空闲端口 · 打印 PREVIEW_URL= · 前台运行(Ctrl-C 停)
#   PORT=5180 bash preview.sh  # 指定端口(覆盖动态选择)
#
# PMO 接法:后台跑本脚本(run_in_background)· 读早期 stdout 的 `PREVIEW_URL=...` 行 · 给用户 browse。
set -euo pipefail
cd "$(dirname "$0")"

# 1) 包管理器(按 lockfile)
if   [ -f pnpm-lock.yaml ]; then PM=pnpm
elif [ -f yarn.lock ];      then PM=yarn
else                             PM=npm; fi

# 2) 依赖(首次)
if [ ! -d node_modules ]; then
  echo "[preview] 安装依赖($PM install · 首次较慢)..." >&2
  $PM install >&2
fi

# 3) 动态空闲端口(并行 worktree / 多终端不冲突)· PORT env 可覆盖
if [ -z "${PORT:-}" ]; then
  PORT="$(node -e 'const s=require("net").createServer();s.listen(0,"127.0.0.1",()=>{const p=s.address().port;s.close(()=>console.log(p))})')"
fi
export PORT  # next.js / CRA 直接读 PORT env

# 4) 输出可打开 URL(PMO 抓这行 · 必须在 exec 之前打印)
echo "PREVIEW_URL=http://localhost:${PORT}/"
echo "[preview] dev server 启动中 · 端口 ${PORT} · 就绪后 browse 上面 URL · Ctrl-C 停" >&2

# 5) 起 dev server(锁定上面选的空闲端口)
# 🔴 按你的框架改这一行(preview-project 与真实前端同栈):
#   vite    : exec $PM run dev -- --port "$PORT" --strictPort --host 127.0.0.1
#   next.js : exec $PM run dev -- -p "$PORT"
#   CRA     : exec $PM run dev                 # CRA 读 $PORT env · 删 --port 参数
exec $PM run dev -- --port "$PORT" --strictPort --host 127.0.0.1
