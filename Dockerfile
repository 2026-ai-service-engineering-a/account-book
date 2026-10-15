# syntax=docker/dockerfile:1
# 로컬에는 아무것도 설치하지 않는다.
#
#   ui, agent, api, mcp — 서비스 하나씩. 그 서비스의 의존성과 코드만 굽는다 (docker-compose.yml)
#   dev       — 의존성과 도구만 담는다. 코드는 바인드 마운트로 들어온다 (docker-compose.dev.yml)
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


FROM base AS ui

# 의존성 레이어 — requirements가 바뀔 때만 다시 설치된다. 개발 도구도 LLM 라이브러리도 넣지 않는다.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 자기 코드만 굽는다. 서비스끼리 import하지 않으니(development-rules 2.3) 다른 폴더는 필요 없다.
COPY src/ui ./src/ui

# root로 돌지 않는다.
RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8080
CMD ["uvicorn", "ui.main:create_app", "--factory", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8080"]


FROM base AS agent

COPY requirements.txt requirements-agent.txt ./
RUN pip install --no-cache-dir -r requirements-agent.txt

COPY src/agent ./src/agent

RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8001
CMD ["uvicorn", "agent.main:create_app", "--factory", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8001"]


FROM base AS api

COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

COPY src/api ./src/api

RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8000
# 뜨기 전에 스키마를 최신으로 올리고 기준 데이터를 맞춘다. 둘 다 몇 번을 돌려도 같다.
CMD ["sh", "-c", "alembic -c src/api/alembic.ini upgrade head && python -m api.seed && uvicorn api.main:create_app --factory --app-dir src --host 0.0.0.0 --port 8000"]


FROM base AS mcp

COPY requirements.txt requirements-mcp.txt ./
RUN pip install --no-cache-dir -r requirements-mcp.txt

# 자기 코드와 agent와 나누는 계약(JSON)만 굽는다. agent의 코드는 들어오지 않는다
COPY src/mcp_server ./src/mcp_server
COPY src/shared ./src/shared

RUN useradd --create-home --uid 10001 app
USER app

# 포트가 없다. 클라이언트가 이 프로세스를 띄우고 stdin·stdout으로 말한다(docs/ai/mcp.md 6장)
CMD ["python", "-m", "mcp_server.main"]


FROM base AS dev

# git — 변경 파일을 고르는 점검(--base)과 devcontainer 안에서의 작업에 쓴다.
# make — devcontainer로 들어오면 터미널이 이미 컨테이너 안이라 여기서 make를 친다.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git make \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory /app

COPY requirements.txt requirements-agent.txt requirements-api.txt requirements-mcp.txt \
    requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
