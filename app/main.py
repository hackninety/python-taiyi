# -*- coding: utf-8 -*-
"""python-taiyi：太乙神数排盘 API。

直接引用 kentang2017/kintaiyi（MIT）作为权威排盘实现——本服务只做输入校验、
序列化与 HTTP 封装，不改写任何算法；升级上游 = 重建镜像（bump KINTAIYI_REF）。

前端（react-taiyi）以「后端优先」调用本 API，并用本地 TS 引擎逐字段对照做漂移检测；
API 不可用时前端自动回退本地引擎。
"""
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .serialize import (
    serialize_chart, serialize_mingfa, pan_svg, kintaiyi_version, DAY_ACCUMULATOR_FIX,
    full_pan, full_life, read_doc, liu_timelines,
)

KINTAIYI_REF = os.environ.get("KINTAIYI_REF", "unknown")

app = FastAPI(
    title="python-taiyi",
    description="太乙神数排盘 API（直接引用 kentang2017/kintaiyi，MIT）",
    version="0.1.0",
)

# 公开只读数据、无鉴权，放开 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChartReq(BaseModel):
    # sxtwl 古历实测支持至公元前约 6000 年（负数=公元前 N 年直记，无 0 年）；异常仍兜 422
    year: int = Field(ge=-6000, le=9999, description="公历年（负数=公元前 N 年，kintaiyi/sxtwl 约定）")
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    ji: int = Field(ge=0, le=4, description="计式 0年 1月 2日 3时 4分")
    acum: int = Field(ge=0, le=3, description="积年法 0统宗 1金镜 2淘金歌 3太乙局")


class MingfaReq(BaseModel):
    year: int = Field(ge=600, le=9999)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    sex: str = Field(pattern="^(男|女)$")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "kintaiyi": kintaiyi_version(), "ref": KINTAIYI_REF}


@app.get("/api/version")
def version() -> dict:
    return {
        "app": "python-taiyi",
        "kintaiyi_version": kintaiyi_version(),
        "kintaiyi_ref": KINTAIYI_REF,
        "adapter_fixes": [DAY_ACCUMULATOR_FIX],
        "upstream": "https://github.com/kentang2017/kintaiyi",
    }


@app.post("/api/taiyi")
def taiyi(req: ChartReq) -> dict:
    try:
        chart = serialize_chart(req.year, req.month, req.day, req.hour, req.minute,
                                req.ji, req.acum)
    except Exception as exc:  # noqa: BLE001 — 上游计算异常保留错误类型和信息
        raise HTTPException(
            status_code=422,
            detail={"code": "KINTAIYI_ERROR", "message": f"{type(exc).__name__}: {exc}"},
        ) from exc
    return {"source": "kintaiyi", "ref": KINTAIYI_REF, "chart": chart}


@app.post("/api/taiyi/mingfa")
def mingfa(req: MingfaReq) -> dict:
    try:
        data = serialize_mingfa(req.year, req.month, req.day, req.hour, req.minute, req.sex)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=422,
            detail={"code": "KINTAIYI_ERROR", "message": f"{type(exc).__name__}: {exc}"},
        ) from exc
    return {"source": "kintaiyi", "ref": KINTAIYI_REF, "mingfa": data}


class PanReq(ChartReq):
    """全解释盘请求；game=True 附运筹博弈分析（Nash 均衡）"""
    game: bool = False


@app.post("/api/taiyi/pan")
def taiyi_pan(req: PanReq) -> dict:
    """kintaiyi 全解释盘（t.pan）：值宿断事、断法解释、明所主术、釋格局全文、
    《太乙統宗寶鑑》卷三/五/六/八/九/十/十一/十二(統運)/十三(卦象)/十四/十五/十七/十八、
    军事三卷、金函玉鏡、九星贵神、五運六氣等全量输出（中文键与上游一致）。"""
    try:
        data = full_pan(req.year, req.month, req.day, req.hour, req.minute,
                        req.ji, req.acum, req.game)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=422,
            detail={"code": "KINTAIYI_ERROR", "message": f"{type(exc).__name__}: {exc}"},
        ) from exc
    return {"source": "kintaiyi", "ref": KINTAIYI_REF, "pan": data}


@app.post("/api/taiyi/life")
def taiyi_life(req: MingfaReq) -> dict:
    """kintaiyi 命法全盘（t.taiyi_life）：含卷二十、十提金賦、十二宮星斷、
    雙星同宮論、諸星上中下三等。"""
    try:
        data = full_life(req.year, req.month, req.day, req.hour, req.minute, req.sex)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=422,
            detail={"code": "KINTAIYI_ERROR", "message": f"{type(exc).__name__}: {exc}"},
        ) from exc
    return {"source": "kintaiyi", "ref": KINTAIYI_REF, "life": data}


class LiuReq(BaseModel):
    # 上游 hex_timeline 时步用 Python datetime（MINYEAR=1），流卦運不支持公元前
    year: int = Field(ge=1, le=9998)  # 流年往后推 12 年，留 1 年余量
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)


@app.post("/api/taiyi/liu")
def taiyi_liu(req: LiuReq) -> dict:
    """流卦運多期时间轴（流年12/流月12/流日15/流時12辰/流分10），
    逐期直调上游 apps/hex_timeline 推法（命法卦链 + 干支序动爻）。"""
    try:
        data = liu_timelines(req.year, req.month, req.day, req.hour, req.minute)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=422,
            detail={"code": "KINTAIYI_ERROR", "message": f"{type(exc).__name__}: {exc}"},
        ) from exc
    return {"source": "kintaiyi", "ref": KINTAIYI_REF, "liu": data}


@app.get("/api/docs/{name}")
def docs(name: str) -> Response:
    """上游 docs/*.md 原文（example=局數史例 disaster=災異統計 guji=古籍書目
    instruction=看盤要領步骤 tutorial=教程 update=更新日誌）。"""
    md = read_doc(name)
    if md is None:
        raise HTTPException(status_code=404, detail={"code": "DOC_NOT_FOUND", "message": name})
    return Response(content=md, media_type="text/markdown; charset=utf-8",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/taiyi/pan.svg")
def pan(
    year: int = Query(ge=-6000, le=9999),
    month: int = Query(ge=1, le=12),
    day: int = Query(ge=1, le=31),
    hour: int = Query(ge=0, le=23),
    minute: int = Query(ge=0, le=59),
    ji: int = Query(ge=0, le=4),
    acum: int = Query(ge=0, le=3),
    tenching: int = Query(default=1, ge=0, le=1, description="0=带十精行星层 1=不带"),
) -> Response:
    """kintaiyi 原生圆盘（drawsvg 生成的 SVG，随上游渲染样式更新）。"""
    try:
        svg = pan_svg(year, month, day, hour, minute, ji, acum, tenching)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=422,
            detail={"code": "KINTAIYI_ERROR", "message": f"{type(exc).__name__}: {exc}"},
        ) from exc
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})
