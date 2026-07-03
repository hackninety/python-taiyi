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

from .serialize import serialize_chart, serialize_mingfa, pan_svg, kintaiyi_version

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
    year: int = Field(ge=600, le=9999, description="公历年（kintaiyi/sxtwl 验证范围）")
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
        "upstream": "https://github.com/kentang2017/kintaiyi",
    }


@app.post("/api/taiyi")
def taiyi(req: ChartReq) -> dict:
    try:
        chart = serialize_chart(req.year, req.month, req.day, req.hour, req.minute,
                                req.ji, req.acum)
    except Exception as exc:  # noqa: BLE001 — 参考实现已知崩溃组合（如日计×太乙局）
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


@app.get("/api/taiyi/pan.svg")
def pan(
    year: int = Query(ge=600, le=9999),
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
