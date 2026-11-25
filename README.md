# python-taiyi

太乙神数排盘 API —— **直接引用** [kentang2017/kintaiyi](https://github.com/kentang2017/kintaiyi)（MIT，事实上的太乙权威开源实现）作为计算内核，FastAPI 只做输入校验、序列化与 HTTP 封装，**不改写任何算法**。

配套前端：[hackninety/react-taiyi](https://github.com/hackninety/react-taiyi)（后端优先调用本 API，本地 TS 引擎逐字段对照做漂移检测，API 不可用时自动回退本地引擎）。

## 端点

| 端点 | 说明 |
|---|---|
| `POST /api/taiyi` | 完整盘面 JSON（字段集与 react-taiyi 黄金用例同构，便于逐字段对照）。body：`{year,month,day,hour,minute,ji,acum}`，`ji` 0-4=年/月/日/时/分计，`acum` 0-3=统宗/金镜/淘金歌/太乙局 |
| `POST /api/taiyi/mingfa` | 太乙命法。body：`{year,month,day,hour,minute,sex}`（`sex`=男/女） |
| `GET /api/taiyi/pan.svg?...` | **kintaiyi 原生圆盘 SVG**（drawsvg 生成，随上游渲染更新）。参数同上 + `tenching`（0=带十精行星层，1=不带） |
| `GET /api/health` | 健康检查（含 kintaiyi 版本与 pin 的 commit） |
| `GET /api/version` | 版本信息 |

日计×太乙局在固定版本 `6950878` 会给列表传入整值浮点下标。图盘封装保留原积数公式，传给下游前将这个组合的整值转换为整数。`/api/version` 的 `adapter_fixes` 列出 `integer-day-accumulator` 表示实例已应用该修正。其他上游计算异常保留 HTTP 422 与具体错误详情。

## 与上游同步

kintaiyi 以 **pin SHA** 方式安装（见 [Dockerfile](Dockerfile) / [docker-compose.yml](docker-compose.yml) 的 `KINTAIYI_REF`）。升级：

```bash
# 改 docker-compose.yml 里的 KINTAIYI_REF 为上游新 commit，然后
docker compose up -d --build
```

react-taiyi 前端会把本 API 返回的字段与其本地 TS 引擎逐字段对照——上游若变更算法语义，前端立即醒目提示差异（漂移报警），再决定是否同步移植。

## 部署（docker-compose 单机）

```bash
git clone https://github.com/hackninety/python-taiyi /opt/python-taiyi
cd /opt/python-taiyi
docker compose up -d --build
curl http://127.0.0.1:8018/api/health
```

容器仅监听 `127.0.0.1:8018`，经 Nginx / Cloudflare 反代对外提供 HTTPS；无鉴权（公开只读数据），CORS 全放开。

Nginx 反代示例：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8018;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 本地开发

```bash
pip install -r requirements.txt
pip install "kintaiyi @ git+https://github.com/kentang2017/kintaiyi@<REF>"
uvicorn app.main:app --reload
python scripts/smoke.py   # 冒烟：对照 react-taiyi 黄金用例抽查
```

仅供术数文化研究。算法版权与实现归上游 kintaiyi（MIT）。
