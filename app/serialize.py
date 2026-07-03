# -*- coding: utf-8 -*-
"""kintaiyi 排盘序列化：把 Taiyi 实例的输出整理成 JSON 友好的 dict。

字段集与 react-taiyi 的黄金用例生成器（scripts/gen_fixtures.py）完全一致，
前端以同一套键名与本地 TS 引擎逐字段对照（漂移检测）。
"""
import datetime as _dt

from kintaiyi import kintaiyi as kt
from kintaiyi import config, jieqi


def kintaiyi_version() -> str:
    try:
        from importlib.metadata import version
        return version("kintaiyi")
    except Exception:  # noqa: BLE001
        return "unknown"


def serialize_chart(year: int, month: int, day: int, hour: int, minute: int,
                    ji: int, acum: int) -> dict:
    """完整盘面（与 gen_fixtures.py 的 case 字段一一对应）。"""
    t = kt.Taiyi(year, month, day, hour, minute)
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
    t = kt.Taiyi(year, month, day, hour, minute)
    drawing = t.gen_gong(ji, acum, tenching)
    # 上游部分计式分支直接返回 SVG 字符串，其余返回 drawsvg Drawing
    return drawing if isinstance(drawing, str) else drawing.as_svg()
