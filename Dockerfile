# python-taiyi：太乙神数排盘 API（直接引用 kentang2017/kintaiyi）
# 升级上游：修改 KINTAIYI_REF（commit SHA 或分支名）后重建镜像即可。
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# pin 上游 kintaiyi 版本（可在 docker compose build --build-arg 覆盖）
ARG KINTAIYI_REF=695087889532f0f91d84185d8534df0474617376

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
# 克隆到 vendor 后本地安装：docs/*.md（局數史例/災異統計/古籍書目等）需随包提供
RUN pip install --no-cache-dir -r requirements.txt \
 && git clone https://github.com/kentang2017/kintaiyi /srv/vendor/kintaiyi \
 && git -C /srv/vendor/kintaiyi checkout ${KINTAIYI_REF} \
 && pip install --no-cache-dir /srv/vendor/kintaiyi

ENV KINTAIYI_REF=${KINTAIYI_REF} \
    KINTAIYI_DOCS=/srv/vendor/kintaiyi/docs \
    KINTAIYI_APPS=/srv/vendor/kintaiyi/apps

COPY app ./app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/api/health', timeout=4)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
