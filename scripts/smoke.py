# -*- coding: utf-8 -*-
"""冒烟测试：序列化一张盘 + 圆盘 SVG，可选对照 react-taiyi 黄金用例。

用法（若未 pip 安装 kintaiyi，可用 PYTHONPATH 指向其 src）：
    PYTHONPATH=<kintaiyi>/src python scripts/smoke.py [golden.json]
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.serialize import serialize_chart, serialize_mingfa, pan_svg  # noqa: E402

CASE = (2026, 7, 3, 14, 30, 3, 0)  # 时计 × 太乙统宗

chart = serialize_chart(*CASE)
print("kook:", chart["kook_text"], "| acc:", chart["acc"], "| ty:", chart["ty"],
      "| wc:", chart["wc"], "| sf:", chart["sf"])
assert chart["kook_num"] and chart["gz"] and chart["doors"], "关键字段缺失"

mf = serialize_mingfa(2026, 7, 3, 14, 30, "男")
print("mingfa life_accum:", mf["life_accum"], "| three_cai:", mf["three_cai"])

svg = pan_svg(*CASE, tenching=1)
assert svg.lstrip().startswith("<?xml") or "<svg" in svg[:200], "SVG 输出异常"
print("pan.svg bytes:", len(svg.encode("utf-8")))

# 可选：对照 react-taiyi 黄金用例
if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
    with open(sys.argv[1], encoding="utf-8") as f:
        golden = json.load(f)["cases"]
    match = next(c for c in golden
                 if c.get("input") == list(CASE[:5]) and c.get("ji") == CASE[5] and c.get("acum") == CASE[6])
    diffs = []
    for k, v in match.items():
        if k in ("input", "ji", "acum"):
            continue
        if k in chart and json.dumps(chart[k], ensure_ascii=False, sort_keys=True) \
                != json.dumps(v, ensure_ascii=False, sort_keys=True):
            diffs.append((k, v, chart.get(k)))
    if diffs:
        print("与黄金用例差异（可能因上游更新）:")
        for k, a, b in diffs:
            print(f"  {k}: golden={a!r} now={b!r}")
    else:
        print("与黄金用例逐字段一致 ✓")

print("SMOKE OK")
