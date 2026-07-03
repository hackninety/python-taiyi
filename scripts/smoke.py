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

# 全解释盘：JSON 可序列化 + 关键卷/键抽查
from app.serialize import full_pan, full_life, read_doc  # noqa: E402

pan = full_pan(*CASE, game=True)
json.dumps(pan, ensure_ascii=False)
for key in ("太歲值宿斷事", "釋格局", "軍事戰略", "卷八", "卷九", "卷十一", "卷十二",
            "卷十三", "卷十四", "卷十八", "太乙九星", "文昌九星", "五運六氣",
            "金函玉鏡", "軍事應用", "軍事占斷", "神將所主"):
    assert key in pan, f"pan 缺键：{key}"
print("pan keys:", len(pan), "| 卷十二子键:", list(pan["卷十二"])[:6] if isinstance(pan["卷十二"], dict) else type(pan["卷十二"]).__name__)

life = full_life(2026, 7, 3, 14, 30, "男")
json.dumps(life, ensure_ascii=False)
for key in ("十提金賦", "十二宮星斷", "雙星同宮論", "卷二十", "安命宮"):
    assert key in life, f"life 缺键：{key}"
print("life keys:", len(life))

for name in ("example", "disaster", "guji", "instruction", "tutorial", "update"):
    md = read_doc(name)
    assert md and len(md) > 100, f"doc {name} 读取失败"
print("docs ok: example/disaster/guji/instruction/tutorial/update")

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
