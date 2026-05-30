#!/usr/bin/env python3
"""tools/preview.py — Teamwork UI 预览静态服务 hub(v8.57 新增 · 独立元工具)。

解决的问题(用户拍板 2026-05-30):
- same-stack 预览稿是编译出的 ES-module bundle · `file://` 因 CORS 不加载 module
  → browse 停在 about:blank → 必须起 HTTP server 才能预览
- 各 session / 并行 worktree / 多终端各自 `python3 -m http.server 8799`
  → 端口冲突 · 互相抢占
- 想让各 session 的 UI 预览稿跨 session 可访问

设计:**单 hub**(治本端口冲突)
- 全机唯一一个常驻 hub 进程 · 绑定一个端口(默认 8799 · 占用则顺延)
- 一个 registry(`~/.teamwork/preview/registry.json`)记录 slug → 预览目录映射
  · 落在 $HOME · 跨 worktree / 终端 / session 共享
- hub 按路径前缀 `http://127.0.0.1:<port>/<slug>/` 分发到各预览目录
- 后续 session 不再起新 server · 只往 registry 注册自己的目录 · 复用同一 hub
  → 永不端口冲突

与 update.py / bootstrap.py 对齐:独立元工具 · 不混 state.py 运行时状态机。

子命令:
    preview.py serve --dir <预览目录> [--slug X] [--feature <feature_dir>]
    preview.py list
    preview.py stop [--all | --slug X] [--prune]
    preview.py run-hub --port <P>     # 隐藏 · detached 子进程实际跑 server

🔴 same-stack 编译注意:preview-project 的 build 必须用**相对资产路径**
   (vite `base: './'` / 等价配置)· 否则 `/<slug>/` 前缀下 `/assets/*` 绝对路径会 404。
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

# ─── 常量 ─────────────────────────────────────────────────────────────────

PREVIEW_ROOT_ENV = "TEAMWORK_PREVIEW_ROOT"        # 测试覆盖用
PREVIEW_PORT_ENV = "TEAMWORK_PREVIEW_PORT"        # 偏好端口覆盖
DEFAULT_PREFERRED_PORT = 8799
PORT_SCAN_RANGE = 60                              # preferred..preferred+60 找可绑端口
HUB_MAGIC = "teamwork-preview-hub"
HEALTH_PATH = "/__teamwork_hub__"
HUB_START_TIMEOUT_SEC = 6.0
HEALTH_TIMEOUT_SEC = 1.5


# ─── 路径 / IO helpers ────────────────────────────────────────────────────


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _emit(payload: dict) -> None:
    """统一 stdout JSON emit · 风格与 update.py / bootstrap.py 对齐。"""
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _preview_root() -> Path:
    override = os.environ.get(PREVIEW_ROOT_ENV)
    root = Path(override) if override else (Path.home() / ".teamwork" / "preview")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _registry_path() -> Path:
    return _preview_root() / "registry.json"


def _hub_state_path() -> Path:
    return _preview_root() / "hub.json"


def _hub_log_path() -> Path:
    return _preview_root() / "hub.log"


def _lock_path() -> Path:
    return _preview_root() / ".lock"


def _preferred_port() -> int:
    raw = os.environ.get(PREVIEW_PORT_ENV)
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return DEFAULT_PREFERRED_PORT


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _atomic_write_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


@contextmanager
def _file_lock():
    """跨进程 advisory 锁(并行 worktree 同时注册防 registry 互相覆盖)。

    posix 用 fcntl.flock · 非 posix(无 fcntl)退化为 no-op(单机串行注册风险低)。
    """
    lock_file = _lock_path()
    try:
        import fcntl
    except ImportError:
        yield
        return
    fh = open(lock_file, "w")
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


def _slugify(name: str) -> str:
    out = []
    for ch in name.strip().lower():
        if ch.isalnum() or ch in "-_":
            out.append(ch)
        else:
            out.append("-")
    slug = "".join(out).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "preview"


# ─── registry ────────────────────────────────────────────────────────────


def _load_registry() -> dict:
    """registry: {slug: {dir, feature, project, registered_at}}。"""
    data = _load_json(_registry_path(), {})
    return data if isinstance(data, dict) else {}


def _register(slug: str, serve_dir: Path, feature: Optional[str],
              project: Optional[str]) -> dict:
    with _file_lock():
        reg = _load_registry()
        entry = {
            "dir": str(serve_dir.resolve()),
            "feature": feature,
            "project": project,
            "registered_at": _now_iso(),
        }
        reg[slug] = entry
        _atomic_write_json(_registry_path(), reg)
    return entry


def _unregister(slug: str) -> bool:
    with _file_lock():
        reg = _load_registry()
        if slug in reg:
            del reg[slug]
            _atomic_write_json(_registry_path(), reg)
            return True
    return False


def _prune_registry() -> list[str]:
    """删 dir 已不存在的 stale 条目 · 返删掉的 slug 列表。"""
    removed = []
    with _file_lock():
        reg = _load_registry()
        for slug in list(reg.keys()):
            d = reg[slug].get("dir", "")
            if not d or not Path(d).is_dir():
                removed.append(slug)
                del reg[slug]
        if removed:
            _atomic_write_json(_registry_path(), reg)
    return removed


# ─── hub HTTP server ─────────────────────────────────────────────────────


class _HubHandler(BaseHTTPRequestHandler):
    server_version = "TeamworkPreviewHub"

    # registry mtime 缓存(避免每个 asset 请求都读盘)
    _reg_cache: dict = {}
    _reg_mtime: float = -1.0

    def _registry(self) -> dict:
        try:
            mtime = _registry_path().stat().st_mtime
        except OSError:
            mtime = -1.0
        if mtime != _HubHandler._reg_mtime:
            _HubHandler._reg_cache = _load_registry()
            _HubHandler._reg_mtime = mtime
        return _HubHandler._reg_cache

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):  # noqa: N802
        self.do_GET()

    def do_GET(self):  # noqa: N802
        from urllib.parse import unquote, urlsplit
        path = urlsplit(self.path).path

        if path == HEALTH_PATH:
            payload = {
                "magic": HUB_MAGIC,
                "port": self.server.server_address[1],
                "pid": os.getpid(),
                "registry_count": len(self._registry()),
                "started_at": getattr(self.server, "_started_at", None),
            }
            self._send(200, json.dumps(payload).encode("utf-8"),
                       "application/json; charset=utf-8")
            return

        if path in ("/", "/index.html", ""):
            self._send(200, self._render_hub_index().encode("utf-8"),
                       "text/html; charset=utf-8")
            return

        # /<slug>/<subpath>
        parts = unquote(path).lstrip("/").split("/", 1)
        slug = parts[0]
        subpath = parts[1] if len(parts) > 1 else ""

        reg = self._registry()
        entry = reg.get(slug)
        if not entry:
            self._send(404, self._render_not_found(slug).encode("utf-8"),
                       "text/html; charset=utf-8")
            return

        base = Path(entry["dir"]).resolve()
        if not base.is_dir():
            self._send(410, f"预览目录已不存在:{base}".encode("utf-8"),
                       "text/plain; charset=utf-8")
            return

        # slug 根 → 渲染该目录下 *.html 列表(预览常多页 · 不强制 index.html)
        if subpath in ("", "/"):
            self._send(200, self._render_dir_index(slug, base).encode("utf-8"),
                       "text/html; charset=utf-8")
            return

        target = (base / subpath).resolve()
        # 路径穿越守卫:target 必须在 base 内
        if target != base and base not in target.parents:
            self._send(403, b"403 forbidden (path traversal)",
                       "text/plain; charset=utf-8")
            return
        if target.is_dir():
            self._send(200, self._render_dir_index(slug, target,
                                                   rel_base=base).encode("utf-8"),
                       "text/html; charset=utf-8")
            return
        if not target.is_file():
            self._send(404, f"404 not found: {subpath}".encode("utf-8"),
                       "text/plain; charset=utf-8")
            return
        try:
            body = target.read_bytes()
        except OSError as e:
            self._send(500, f"read error: {e}".encode("utf-8"),
                       "text/plain; charset=utf-8")
            return
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in (
                "application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self._send(200, body, ctype)

    def _render_hub_index(self) -> str:
        reg = self._registry()
        rows = []
        for slug, e in sorted(reg.items()):
            d = e.get("dir", "")
            stale = "" if d and Path(d).is_dir() else " ⚠️ stale"
            rows.append(
                f'<li><a href="/{slug}/">{slug}</a>{stale}'
                f'<br><small>{e.get("project") or "-"} · '
                f'{e.get("feature") or "-"}<br>{d}</small></li>')
        body = "\n".join(rows) or "<li><i>暂无注册的预览 · 用 preview.py serve 注册</i></li>"
        return (
            "<!doctype html><meta charset=utf-8>"
            "<title>Teamwork Preview Hub</title>"
            "<style>body{font-family:system-ui,sans-serif;max-width:760px;"
            "margin:40px auto;padding:0 16px}li{margin:10px 0}"
            "small{color:#666}</style>"
            "<h1>Teamwork Preview Hub</h1>"
            f"<p>已注册 {len(reg)} 个预览目录 · 单 hub 服务全部 session/worktree。</p>"
            f"<ul>{body}</ul>")

    def _render_dir_index(self, slug: str, directory: Path,
                          rel_base: Optional[Path] = None) -> str:
        rel_base = rel_base or directory
        items = []
        for child in sorted(directory.iterdir(),
                            key=lambda p: (p.is_file(), p.name)):
            rel = child.relative_to(rel_base).as_posix()
            label = child.name + ("/" if child.is_dir() else "")
            items.append(f'<li><a href="/{slug}/{rel}">{label}</a></li>')
        body = "\n".join(items) or "<li><i>(空目录)</i></li>"
        return (
            "<!doctype html><meta charset=utf-8>"
            f"<title>{slug}</title>"
            "<style>body{font-family:system-ui,sans-serif;max-width:760px;"
            "margin:40px auto;padding:0 16px}</style>"
            f"<h1>{slug}</h1><p><code>{directory}</code></p>"
            f"<ul>{body}</ul>")

    def _render_not_found(self, slug: str) -> str:
        reg = self._registry()
        known = ", ".join(sorted(reg.keys())) or "(无)"
        return (
            "<!doctype html><meta charset=utf-8>"
            f"<title>404 {slug}</title>"
            "<style>body{font-family:system-ui,sans-serif;max-width:760px;"
            "margin:40px auto;padding:0 16px}</style>"
            f"<h1>404 · slug 「{slug}」未注册</h1>"
            f"<p>已注册:{known}</p>"
            "<p>用 <code>python3 tools/preview.py serve --dir &lt;预览目录&gt;</code> 注册。</p>")

    def log_message(self, fmt, *args):  # noqa: A003
        # 写到 stderr(detached 时已重定向到 hub.log · 便于排查)
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def _run_hub(port: int) -> int:
    """实际跑 server(detached 子进程入口 · run-hub 子命令)。"""
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _HubHandler)
    httpd._started_at = _now_iso()  # type: ignore[attr-defined]
    _atomic_write_json(_hub_state_path(), {
        "magic": HUB_MAGIC,
        "port": port,
        "pid": os.getpid(),
        "started_at": httpd._started_at,  # type: ignore[attr-defined]
    })
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # 仅当 hub.json 仍指向自己才清理(避免删掉接管的新 hub)
        st = _load_json(_hub_state_path(), {})
        if st.get("pid") == os.getpid():
            try:
                _hub_state_path().unlink()
            except OSError:
                pass
    return 0


# ─── hub 生命周期 ─────────────────────────────────────────────────────────


def _health_check(port: int) -> Optional[dict]:
    """GET health · 验 magic · 返 payload 或 None。"""
    url = f"http://127.0.0.1:{port}{HEALTH_PATH}"
    try:
        with urllib.request.urlopen(url, timeout=HEALTH_TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data if data.get("magic") == HUB_MAGIC else None
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        return None


def _pid_alive(pid: int) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return pid and isinstance(pid, int) and _pid_alive_permission_hint(pid)
    except OSError:
        return False


def _pid_alive_permission_hint(pid: int) -> bool:
    # PermissionError 说明进程存在但非本用户(罕见)· 视作存活
    return True


def _find_running_hub() -> Optional[dict]:
    """读 hub.json · pid 存活 + health magic 通 → 返 {port, pid} · 否则 None(stale)。"""
    st = _load_json(_hub_state_path(), {})
    port = st.get("port")
    pid = st.get("pid")
    if not port:
        return None
    if pid and not _pid_alive(pid):
        return None
    health = _health_check(port)
    if health and health.get("magic") == HUB_MAGIC:
        return {"port": port, "pid": health.get("pid", pid)}
    return None


def _can_bind(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _pick_port() -> Optional[int]:
    start = _preferred_port()
    for p in range(start, start + PORT_SCAN_RANGE):
        if _can_bind(p):
            return p
    return None


def _ensure_hub() -> dict:
    """复用已跑 hub · 否则 detached 启动一个 · 返 {port, pid, reused, log}。"""
    existing = _find_running_hub()
    if existing:
        return {**existing, "reused": True, "log": str(_hub_log_path())}

    # 进锁内再检一次(并行 session 竞态 · 防双 hub)
    with _file_lock():
        existing = _find_running_hub()
        if existing:
            return {**existing, "reused": True, "log": str(_hub_log_path())}

        port = _pick_port()
        if port is None:
            return {"error": (
                f"端口 {_preferred_port()}..{_preferred_port() + PORT_SCAN_RANGE} "
                f"全被占用 · 无法启动 hub · 设 {PREVIEW_PORT_ENV} 换偏好端口")}

        log_fh = open(_hub_log_path(), "ab")
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()),
             "run-hub", "--port", str(port)],
            stdout=log_fh, stderr=log_fh, stdin=subprocess.DEVNULL,
            start_new_session=True,  # 脱离控制终端 · 终端关了 hub 仍活
        )
        log_fh.close()

    # 轮询 health(锁外 · 避免阻塞其他注册)
    deadline = time.time() + HUB_START_TIMEOUT_SEC
    while time.time() < deadline:
        health = _health_check(port)
        if health and health.get("magic") == HUB_MAGIC:
            return {"port": port, "pid": health.get("pid", proc.pid),
                    "reused": False, "log": str(_hub_log_path())}
        if proc.poll() is not None:
            break
        time.sleep(0.15)
    return {"error": (
        f"hub 启动后 {HUB_START_TIMEOUT_SEC}s 内 health 未通(port={port})· "
        f"查日志 {_hub_log_path()}")}


# ─── feature → 预览目录解析 ──────────────────────────────────────────────


def _resolve_serve_dir(args) -> tuple[Optional[Path], Optional[str], str]:
    """解析要 serve 的目录 · 返 (dir, feature_label, source_desc)。

    优先级:--dir 显式 > --feature(读 UI.md pages_changed[].panorama_file 父目录 /
    feature/preview)。
    """
    if getattr(args, "dir", None):
        d = Path(args.dir).expanduser().resolve()
        return d, getattr(args, "slug", None), "--dir"

    feat = getattr(args, "feature", None)
    if not feat:
        return None, None, "none"
    feat_dir = Path(feat).expanduser().resolve()
    label = feat_dir.name

    # 1) UI.md pages_changed[].panorama_file 父目录(v8.17 全景权威)
    ui_md = feat_dir / "UI.md"
    if ui_md.exists():
        panorama_dir = _panorama_dir_from_ui_md(ui_md, feat_dir)
        if panorama_dir and panorama_dir.is_dir():
            return panorama_dir, label, "UI.md:pages_changed[].panorama_file"

    # 2) feature/preview(老模式副本)
    legacy = feat_dir / "preview"
    if legacy.is_dir():
        return legacy, label, "feature/preview"

    return None, label, "unresolved"


def _panorama_dir_from_ui_md(ui_md: Path, feat_dir: Path) -> Optional[Path]:
    """从 UI.md frontmatter 抽第一个 panorama_file · 取其父目录(预览目录)。

    panorama_file 可能是绝对路径 / 相对仓库根 · 用 git 找 project_root 解析。
    轻量正则 · 不引 YAML 依赖。
    """
    import re
    try:
        text = ui_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"panorama_file:\s*([^\s#]+)", text)
    if not m:
        return None
    raw = m.group(1).strip().strip('"\'')
    pf = Path(raw)
    if pf.is_absolute():
        return pf.parent.resolve() if pf.parent.is_dir() else None
    # 相对 → 试 project_root · 再试 feat_dir
    for base in (_project_root_of(feat_dir), feat_dir):
        if base:
            cand = (base / pf).resolve()
            if cand.parent.is_dir():
                return cand.parent
    return None


def _project_root_of(start: Path) -> Optional[Path]:
    try:
        r = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return Path(r.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return None


# ─── 子命令 ──────────────────────────────────────────────────────────────


def cmd_serve(args) -> int:
    serve_dir, feature_label, source = _resolve_serve_dir(args)
    if serve_dir is None:
        _emit({
            "verdict": "FAIL", "command": "serve",
            "error": "未能解析预览目录",
            "hint": ("传 --dir <编译产物目录>(如 {子项目}/docs/design/preview)· "
                     "或 --feature <feature_dir>(自动从 UI.md / preview/ 解析)"),
            "resolve_source": source,
        })
        return 1
    if not serve_dir.is_dir():
        _emit({
            "verdict": "FAIL", "command": "serve",
            "error": f"预览目录不存在:{serve_dir}",
            "hint": ("same-stack 需先 `npm run build` 编译出 docs/design/preview/*.html · "
                     "详 stages/ui-design-stage.md"),
            "resolve_source": source,
        })
        return 1
    html_files = sorted(p.name for p in serve_dir.glob("*.html"))
    if not html_files:
        _emit({
            "verdict": "WARN", "command": "serve",
            "warning": f"目录无 *.html:{serve_dir}(仍注册 · 但可能没东西可预览)",
            "resolve_source": source,
        })

    slug = _slugify(getattr(args, "slug", None) or feature_label or serve_dir.name)
    project_root = _project_root_of(serve_dir)
    project = project_root.name if project_root else None
    _register(slug, serve_dir, feature_label, project)

    hub = _ensure_hub()
    if "error" in hub:
        _emit({
            "verdict": "FAIL", "command": "serve",
            "error": hub["error"],
            "slug": slug, "dir": str(serve_dir),
            "note": "已写入 registry · hub 起来后即可访问",
        })
        return 1

    base_url = f"http://127.0.0.1:{hub['port']}/{slug}/"
    _emit({
        "verdict": "OK", "command": "serve",
        "slug": slug, "dir": str(serve_dir),
        "project": project, "feature": feature_label,
        "resolve_source": source,
        "url": base_url,
        "page_urls": {h: f"{base_url}{h}" for h in html_files},
        "hub_port": hub["port"], "hub_pid": hub["pid"],
        "hub_reused": hub.get("reused"),
        "hub_index": f"http://127.0.0.1:{hub['port']}/",
        "hub_log": hub.get("log"),
        "next_hint": (
            f"✅ 预览已就绪 · browse {base_url} (单 hub · 不抢端口) · "
            f"多页见 page_urls · hub 服务全部 session/worktree · "
            f"列出全部:preview.py list"),
        "same_stack_note": (
            "🔴 same-stack:preview-project build 必须相对资产路径"
            "(vite base:'./')· 否则 /assets/* 绝对路径在 /<slug>/ 下 404"),
    })
    return 0


def cmd_list(args) -> int:
    hub = _find_running_hub()
    reg = _load_registry()
    entries = []
    for slug, e in sorted(reg.items()):
        d = e.get("dir", "")
        is_stale = not (d and Path(d).is_dir())
        item = {
            "slug": slug, "dir": d,
            "project": e.get("project"), "feature": e.get("feature"),
            "registered_at": e.get("registered_at"),
            "stale": is_stale,
        }
        if hub and not is_stale:
            item["url"] = f"http://127.0.0.1:{hub['port']}/{slug}/"
        entries.append(item)
    _emit({
        "verdict": "OK", "command": "list",
        "hub_running": bool(hub),
        "hub_port": hub.get("port") if hub else None,
        "hub_pid": hub.get("pid") if hub else None,
        "hub_index": (f"http://127.0.0.1:{hub['port']}/" if hub else None),
        "hub_log": str(_hub_log_path()),
        "registry_count": len(reg),
        "entries": entries,
        "next_hint": (
            "preview.py serve --dir <目录> 注册新预览 · "
            "preview.py stop --prune 清理 stale · "
            "preview.py stop --all 停 hub"),
    })
    return 0


def cmd_stop(args) -> int:
    pruned = _prune_registry() if getattr(args, "prune", False) else []

    if getattr(args, "slug", None):
        slug = _slugify(args.slug)
        ok = _unregister(slug)
        _emit({
            "verdict": "OK" if ok else "WARN", "command": "stop",
            "unregistered": slug if ok else None,
            "pruned": pruned,
            "note": ("已从 registry 移除(hub 仍服务其他 slug)"
                     if ok else f"slug 「{slug}」不在 registry"),
        })
        return 0

    if getattr(args, "all", False):
        hub = _find_running_hub()
        killed = None
        if hub and hub.get("pid"):
            try:
                os.kill(hub["pid"], 15)  # SIGTERM
                killed = hub["pid"]
            except OSError:
                pass
        try:
            _hub_state_path().unlink()
        except OSError:
            pass
        _emit({
            "verdict": "OK", "command": "stop",
            "hub_killed_pid": killed,
            "pruned": pruned,
            "note": ("hub 已停 · registry 保留(下次 serve 自动重启 hub)"
                     if killed else "hub 未在运行 · 已清理 hub.json"),
        })
        return 0

    _emit({
        "verdict": "WARN", "command": "stop",
        "pruned": pruned,
        "hint": "需指定 --all(停 hub)或 --slug X(注销单个)· --prune 清 stale",
    })
    return 0


def cmd_run_hub(args) -> int:
    """隐藏子命令:detached 子进程实际跑 server。"""
    return _run_hub(args.port)


# ─── argparse ────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="preview.py",
        description=(
            "Teamwork UI 预览静态服务 hub(v8.57 · 单 hub 治本端口冲突)。\n"
            "各 session/worktree 注册预览目录到共享 registry · 复用同一 hub 进程 · "
            "http://127.0.0.1:<port>/<slug>/ 分发。"),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("serve", help="注册预览目录 + 确保 hub 运行 + 打印 URL")
    s.add_argument("--dir", help="要 serve 的预览目录(编译产物 · 如 docs/design/preview)")
    s.add_argument("--feature", help="feature 目录(自动从 UI.md/preview 解析预览目录)")
    s.add_argument("--slug", help="URL slug(默认 = feature 名 / 目录名 slugify)")
    s.set_defaults(func=cmd_serve)

    li = sub.add_parser("list", help="列出 hub 状态 + 所有已注册预览 + URL")
    li.set_defaults(func=cmd_list)

    st = sub.add_parser("stop", help="停 hub(--all)/ 注销单个(--slug)/ 清 stale(--prune)")
    st.add_argument("--all", action="store_true", help="停 hub 进程(registry 保留)")
    st.add_argument("--slug", help="从 registry 注销指定 slug")
    st.add_argument("--prune", action="store_true", help="删 dir 已不存在的 stale 条目")
    st.set_defaults(func=cmd_stop)

    rh = sub.add_parser("run-hub", help="[隐藏] detached 子进程入口 · 实际跑 server")
    rh.add_argument("--port", type=int, required=True)
    rh.set_defaults(func=cmd_run_hub)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
