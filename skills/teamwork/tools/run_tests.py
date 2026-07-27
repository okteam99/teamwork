#!/usr/bin/env python3
"""teamwork 自测跑法:有 pytest-xdist 用它,否则按历史耗时分片并行(v8.299)。

why:实测 1015 条 / 58s,其中 **61.4% 的用例 <5ms(合计 0.00s)** ——
成本在**进程派生**(起 state.py 子进程 / git init 建仓)不在用例数量。
并行是零测试改动、零失败定位损失的最大杠杆(实测 58s → 19.3s)。

判据与手段见 `standards/scripts-policy.md § R-SP-1b`。

用法:
    python3 tools/run_tests.py            # 默认 4 分片
    python3 tools/run_tests.py -n 8       # 指定分片数
    python3 tools/run_tests.py -- -k foo  # `--` 之后原样透传 pytest
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tools" / "tests"
# 上一轮各分片实测耗时(贪心装箱的输入 · 缺省则按文件大小近似)
CACHE = ROOT / "tools" / ".test-durations.json"


def shard(files: list, weights: dict, n: int) -> list:
    """把文件贪心装箱到 n 个分片,使各片预估耗时尽量均衡。

    权重缺失时用文件字节数近似(与执行耗时弱相关,但好过均分)。
    返回 n 个列表(可能有空片 —— 调用方跳过)。
    """
    n = max(1, n)
    ranked = sorted(files, key=lambda f: -weights.get(f.name, f.stat().st_size / 1000))
    buckets: list = [[] for _ in range(n)]
    load = [0.0] * n
    for f in ranked:
        i = load.index(min(load))
        buckets[i].append(f)
        load[i] += weights.get(f.name, f.stat().st_size / 1000)
    return buckets


def _has_xdist() -> bool:
    try:
        __import__("xdist")
        return True
    except ImportError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("-n", "--shards", type=int, default=4, help="分片数(默认 4)")
    ap.add_argument("passthrough", nargs="*", help="`--` 之后原样透传 pytest")
    args = ap.parse_args()
    extra = args.passthrough

    if _has_xdist():
        print("▶ pytest-xdist 可用 · -n auto")
        return subprocess.run([sys.executable, "-m", "pytest", str(TESTS), "-q",
                               "-n", "auto", *extra], cwd=ROOT).returncode

    files = sorted(TESTS.glob("test_*.py"))
    weights = {}
    if CACHE.is_file():
        try:
            weights = json.loads(CACHE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            weights = {}
    buckets = [b for b in shard(files, weights, args.shards) if b]
    print(f"▶ 无 pytest-xdist · 手动分 {len(buckets)} 片"
          f"({'有' if weights else '无'}历史耗时数据 · 装了 xdist 会自动改走 -n auto)")

    t0 = time.time()
    procs = []
    for b in buckets:
        procs.append((b, subprocess.Popen(
            [sys.executable, "-m", "pytest", *[str(f) for f in b], "-q",
             "--durations=0", "--durations-min=0", *extra],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
    rc = 0
    measured: dict = {}
    for i, (b, p) in enumerate(procs):
        out, _ = p.communicate()
        rc = rc or p.returncode
        for m in re.finditer(r"([\d.]+)s\s+\w+\s+tools/tests/([^:]+)::", out):
            measured[m.group(2)] = measured.get(m.group(2), 0.0) + float(m.group(1))
        tail = [l for l in out.splitlines() if l.strip() and "durations" not in l
                and not re.match(r"^[\d.]+s ", l)]
        print(f"  分片{i}: {tail[-1] if tail else '(无输出)'}")
        if p.returncode:
            for l in out.splitlines():
                if l.startswith(("FAILED", "ERROR")):
                    print(f"      {l}")
    # 🔴 自学:把实测耗时写回缓存 —— 首跑按文件大小近似(必然不均),第二跑起才装得平
    if measured:
        try:
            CACHE.write_text(json.dumps(measured, indent=0, sort_keys=True), encoding="utf-8")
        except OSError:
            pass
    print(f"{'✅ 全绿' if rc == 0 else '❌ 有失败(见上)'} · 墙钟 {time.time()-t0:.1f}s")
    return rc


if __name__ == "__main__":
    sys.exit(main())
