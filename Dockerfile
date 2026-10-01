# syntax=docker/dockerfile:1
# 두 벌이다. 로컬에는 아무것도 설치하지 않는다.
#
#   runtime — 코드를 이미지에 굽는다. 운영처럼 뜨는 ui·agent (docker-compose.yml)
#             기본 CMD는 ui다. agent는 compose가 command를 바꿔 띄운다.
#   dev     — 의존성과 도구만 담는다. 코드는 바인드 마운트로 들어온다 (docker-compose.dev.yml)
FROM python:3.13-slim AS base

WORKDIR /app

# src/를 sys.path에 올려 api·agent·ui가 어디서 실행해도 import 되게 한다.
# 바이트코드는 남기지 않는다 — dev는 바인드 마운트라 호스트가 지저분해진다.
# litellm은 import할 때 모델 가격표를 인터넷에서 받아 온다. 이미지에 든 사본을 쓰게 한다 —
# 테스트가 네트워크를 타지 않고, 뜨는 시간이 네트워크에 묶이지 않는다.
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LITELLM_LOCAL_MODEL_COST_MAP=True


FROM base AS runtime

# 의존성 레이어 — requirements가 바뀔 때만 다시 설치된다. 개발 도구는 넣지 않는다.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

# root로 돌지 않는다.
RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8080
CMD ["uvicorn", "ui.main:create_app", "--factory", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8080"]


FROM base AS dev

# git — 변경 파일을 고르는 점검(--base)과 devcontainer 안에서의 작업에 쓴다.
# make — devcontainer로 들어오면 터미널이 이미 컨테이너 안이라 여기서 make를 친다.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git make \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
