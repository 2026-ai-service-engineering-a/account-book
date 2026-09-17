# syntax=docker/dockerfile:1
# 개발 도구 이미지. 저장소를 /app에 바인드 마운트하므로 이미지는 의존성만 담는다.
# 로컬에는 아무것도 설치하지 않는다.
FROM python:3.13-slim

# git — 변경 파일을 고르는 점검(--base)과 devcontainer 안에서의 작업에 쓴다.
# make — devcontainer로 들어오면 터미널이 이미 컨테이너 안이라 여기서 make를 친다.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git make \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory /app

WORKDIR /app

# 의존성 레이어 — requirements가 바뀔 때만 다시 설치된다.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# src/를 sys.path에 올려 api·agent·ui가 어디서 실행해도 import 되게 한다.
# 바이트코드는 남기지 않는다 — 바인드 마운트라 호스트가 지저분해진다.
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
