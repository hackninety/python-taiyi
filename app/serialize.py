# -*- coding: utf-8 -*-
"""kintaiyi 排盘序列化：把 Taiyi 实例的输出整理成 JSON 友好的 dict。

字段集与 react-taiyi 的黄金用例生成器（scripts/gen_fixtures.py）完全一致，
前端以同一套键名与本地 TS 引擎逐字段对照（漂移检测）。
"""
import datetime as _dt
import os
from functools import lru_cache
from pathlib import Path

from kintaiyi import kintaiyi as kt
from kintaiyi import config, jieqi

DAY_ACCUMULATOR_FIX = "integer-day-accumulator"


class ChartTaiyi(kt.Taiyi):
    """保留上游积数公式，将日计太乙局 round(x, 0) 的整值恢复为整数下标。"""

    def accnum(self, ji_style, taiyi_acumyear):
        value = super().accnum(ji_style, taiyi_acumyear)
        if ji_style == 2 and taiyi_acumyear == 3 and isinstance(value, float) and value.is_integer():
            return int(value)
        return value


def _jsonable(o):
    """pan()/taiyi_life() 输出 JSON 安全化：中文键原样、tuple→list、其余不可序列化对象→str。"""
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_jsonable(x) for x in o]
    if o is None or isinstance(o, (str, int, float, bool)):
        return o
    return str(o)


def kintaiyi_version() -> str:
    try:
        from importlib.metadata import version
        return version("kintaiyi")
    except Exception:  # noqa: BLE001
        return "unknown"


def serialize_chart(year: int, month: int, day: int, hour: int, minute: int,
                    ji: int, acum: int) -> dict:
    """完整盘面（与 gen_fixtures.py 的 case 字段一一对应）。"""
    t = ChartTaiyi(year, month, day, hour, minute)
    acc = t.accnum(ji, acum)
    kook = t.kook(ji, acum)
    acc_key = [k for k in kook if k.startswith("積")][0]
    doors = t.geteightdoors(ji, acum)
    lunar = t._get_lunar_date()
    return {
        "input": [year, month, day, hour, minute],
        "ji": ji,
        "acum": acum,
        "gz": t._get_gangzhi(),
        "lunar": [lunar.get("年"), lunar.get("月"), lunar.get("日")],
        "jq": jieqi.jq(year, month, day, hour, minute),
        "acc": acc,
        "kook_text": kook.get("文"),
        "kook_num": kook.get("數"),
        "kook_year": kook.get("年"),
        "kook_acc": kook.get(acc_key),
        "ty": t.ty(ji, acum),
        "wc": t.skyeyes(ji, acum),
        "wc_des": t.skyeyes_des(ji, acum),
        "sf": t.sf(ji, acum),
        "se": t.se(ji, acum),
        "jigod": t.jigod(ji),
        "hegod": t.hegod(ji),
        "taishui": t.taishui(ji),
        "home_cal": t.home_cal(ji, acum),
        "home_g": t.home_general(ji, acum),
        "home_v": t.home_vgen(ji, acum),
        "away_cal": t.away_cal(ji, acum),
        "away_g": t.away_general(ji, acum),
        "away_v": t.away_vgen(ji, acum),
        "set_cal": t.set_cal(ji, acum),
        "set_g": t.set_general(ji, acum),
        "set_v": t.set_vgen(ji, acum),
        "kingbase": t.kingbase(ji, acum),
        "officerbase": t.officerbase(ji, acum),
        "pplbase": t.pplbase(ji, acum),
        "fgd": t.fgd(ji, acum),
        "skyyi": t.skyyi(ji, acum),
        "earthyi": t.earthyi(ji, acum),
        "zhifu": t.zhifu(ji, acum),
        "flyfu": t.flyfu(ji, acum),
        "doors": {str(k): v for k, v in doors.items()},
        "geju": sorted(t.shi_geju(ji, acum).keys()),
        "geju_detail": t.shi_geju(ji, acum),
        "jiyuan": t.jiyuan(ji, acum),
        "five_yuan": t.get_five_yuan_kook(ji, acum),
        "yangjiu": config.yangjiu(year, month, day),
        "baliu": config.baliu(year, month, day),
        "yeargua": t.yeargua(acum),
        "daygua": t.daygua(acum),
        "hourgua": t.hourgua(acum),
        "year_chin": t.year_chin(),
        "sf_num": t.sf_num(ji, acum),
        "tian_wang": config.tian_wang(acc),
        "tian_shi": config.tian_shi(acc),
        "wuxing_god": config.wuxing(acc),
        "kingfu": config.kingfu(acc),
        "taijun": config.taijun(acc),
        "wufu": config.wufu(acc),
        "threewind": config.threewind(acc),
        "fivewind": config.fivewind(acc),
        "eightwind": config.eightwind(acc),
        "flybird": config.flybird(acc),
        "bigyo": config.bigyo(acc),
        "smyo": config.smyo(acc),
    }


def serialize_mingfa(year: int, month: int, day: int, hour: int, minute: int,
                     sex: str) -> dict:
    """太乙命法（流年卦链依服务器当日，as_of 一并返回供核对）。"""
    t = kt.Taiyi(year, month, day, hour, minute)
    today = _dt.date.today()
    return {
        "input": [year, month, day, hour, minute],
        "sex": sex,
        "as_of": [today.year, today.month, today.day],
        "life_accum": t.taiyi_life_accum(),
        "three_cai": list(t.three_cai_num()),
        "twelve_palaces": t._twelve_palace_map(sex),
        "yangjiu_xingxian": list(t.yangjiu_xingxian(sex).items()),
        "bailiu_xingxian": list(t.bailiu_xingxian(sex).items()),
        "souqi_num": t.souqi_num(),
        "shouqi_ganzhi": t.shouqi_ganzhi(),
        "life_start_gua": t.life_start_gua(),
        "year_gua": t.year_gua(),
        "month_gua": t.month_gua(),
        "day_gua": t.day_gua(),
        "hour_gua": t.hour_gua(),
        "minute_gua": t.minute_gua(),
    }


def pan_svg(year: int, month: int, day: int, hour: int, minute: int,
            ji: int, acum: int, tenching: int) -> str:
    """kintaiyi 原生圆盘 SVG（drawsvg）。tenching: 0=带十精行星层, 1=不带。"""
    t = ChartTaiyi(year, month, day, hour, minute)
    drawing = t.gen_gong(ji, acum, tenching)
    # 上游部分计式分支直接返回 SVG 字符串，其余返回 drawsvg Drawing
    return drawing if isinstance(drawing, str) else drawing.as_svg()


# ---------------------------------------------------------------------------
# 全解释盘 pan() / 命法盘 taiyi_life()：直接透传上游综合输出（含《太乙統宗寶鑑》诸卷）
# pan() 内部重复计算较多，按参数 LRU 缓存
# ---------------------------------------------------------------------------

@lru_cache(maxsize=64)
def full_pan(year: int, month: int, day: int, hour: int, minute: int,
             ji: int, acum: int, game: bool) -> dict:
    """t.pan()：值宿断事/断法解释/明所主术/釋格局/卷三五六八九十…十八/军事/統運/卦象等全量输出。"""
    t = ChartTaiyi(year, month, day, hour, minute)
    return _jsonable(t.pan(ji, acum, enable_game_theory=game))


@lru_cache(maxsize=32)
def full_life(year: int, month: int, day: int, hour: int, minute: int, sex: str) -> dict:
    """t.taiyi_life()：命法全盘（含卷二十、十提金賦、十二宮星斷、雙星同宮論、諸星三等）。"""
    t = kt.Taiyi(year, month, day, hour, minute)
    return _jsonable(t.taiyi_life(sex))


# ---------------------------------------------------------------------------
# 上游 docs/*.md（局數史例/災異統計/古籍書目/看盤要領/教程/更新日誌）
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 流卦運多期时间轴：直接调用上游 apps/hex_timeline.py 的时步生成与推卦函数
# （上游作者不可联系，故 pin 其源码直调——与 pan 同理，零移植零漂移）
# ---------------------------------------------------------------------------

_LIU_SCALES = [("流年", "year"), ("流月", "month"), ("流日", "day"),
               ("流時", "hour"), ("流分", "minute")]


def _apps_dir() -> Path | None:
    env = os.environ.get("KINTAIYI_APPS")
    if env and Path(env).is_dir():
        return Path(env)
    cand = Path(kt.__file__).resolve().parents[2] / "apps"
    return cand if cand.is_dir() else None


def _hex_timeline():
    import sys
    d = _apps_dir()
    if d is None:
        raise RuntimeError("上游 apps 目录不可用（hex_timeline 需 vendor 克隆）")
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))
    import hex_timeline  # noqa: PLC0415
    return hex_timeline


@lru_cache(maxsize=64)
def liu_timelines(year: int, month: int, day: int, hour: int, minute: int) -> dict:
    """五计式流卦運多期序列（年12期/月12期/日15期/時12辰/分10期）。

    逐期直调上游 _compute_gua/_compute_yao（= Taiyi(时刻).year_gua/... 命法卦链），
    时步生成（2/29 回退、时辰跨日等）也用上游 _generate_time_steps 原逻辑。
    """
    ht = _hex_timeline()
    ty = kt.Taiyi(year, month, day, hour, minute)
    out: dict = {}
    for label, scale in _LIU_SCALES:
        rows = []
        for s in ht._generate_time_steps(ty, scale):
            name, symbol, num = ht._compute_gua(
                s["year"], s["month"], s["day"], s["hour"], s["minute"], scale)
            yao = ht._compute_yao(
                s["year"], s["month"], s["day"], s["hour"], s["minute"], scale)
            rows.append({
                "label": s["label"], "sub": s.get("sub_label", ""),
                "時刻": [s["year"], s["month"], s["day"], s["hour"], s["minute"]],
                "卦": name, "卦符": symbol, "卦數": num,
                "爻": yao, "爻名": ht._get_yao_name(name, yao),
            })
        out[label] = rows
    return _jsonable(out)


DOCS_WHITELIST = {"example", "disaster", "guji", "instruction", "tutorial", "update"}


def _docs_dir() -> Path | None:
    env = os.environ.get("KINTAIYI_DOCS")
    if env and Path(env).is_dir():
        return Path(env)
    # src 布局：src/kintaiyi/kintaiyi.py → 仓库根 /docs（本地 PYTHONPATH 与 docker vendor 克隆均适用）
    cand = Path(kt.__file__).resolve().parents[2] / "docs"
    return cand if cand.is_dir() else None


def read_doc(name: str) -> str | None:
    if name not in DOCS_WHITELIST:
        return None
    d = _docs_dir()
    if d is None:
        return None
    p = d / f"{name}.md"
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8")
