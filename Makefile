# 모든 명령은 컨테이너 안에서 돈다. 호스트에는 아무것도 설치하지 않는다.
# 개발 명령은 전부 개발용 구성(docker-compose.dev.yml)을 겹쳐 쓴다.
COMPOSE := docker compose -f docker-compose.yml -f docker-compose.dev.yml
BASE ?= develop

# devcontainer로 들어오면 터미널이 이미 컨테이너 안이다. 그때는 그대로 실행하고,
# 호스트에서는 compose를 거친다. 같은 make 명령이 양쪽에서 똑같이 동작한다.
ifeq ($(wildcard /.dockerenv),)
EXEC := $(COMPOSE) exec -T dev
RUN  := $(COMPOSE) exec dev
else
EXEC :=
RUN  :=
endif

MOCK_PORT ?= 8081
UI_PORT ?= 8080

.DEFAULT_GOAL := help
.PHONY: help env build up dev prod down shell mock ui agent seed demo docs psql review check lint format type test test-db eval eval-chat all

help:  ## 이 목록
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*## /\t/' | expand -t 12

env:  ## .env가 없으면 .env.sample에서 만든다
	@[ -f .env ] || { cp .env.sample .env; echo ".env를 만들었다. 키를 채운다."; }

build: env  ## 이미지를 빌드한다
	$(COMPOSE) build

up: env  ## 개발용으로 뒤에서 띄운다 — ui는 http://localhost:8080, 코드를 고치면 다시 뜬다
	$(COMPOSE) up -d

dev: env  ## 개발용으로 앞에서 띄우고 라이브 업데이트 — 의존성이 바뀌면 이미지도 다시 만든다
	$(COMPOSE) up --build --watch

prod: env  ## 운영처럼 띄운다 — 코드를 이미지에 굽고 다시 뜨지 않는다
	docker compose up -d --build

down:  ## 컨테이너를 내린다
	$(COMPOSE) down

shell:  ## 컨테이너 안으로 들어간다
	$(COMPOSE) exec dev bash

mock:  ## 목 UI를 띄운다 — http://localhost:8081 (Ctrl+C로 멈춘다)
	@echo "http://localhost:$(MOCK_PORT)"
	$(RUN) python3 -m http.server $(MOCK_PORT) --directory mock_ui --bind 0.0.0.0

# 호스트에서는 ui 컨테이너를 띄운다. devcontainer 안에서는 ui 컨테이너가 없으므로
# (runServices) 이 컨테이너에서 직접 띄운다. 어느 쪽이든 8080이다.
ifeq ($(wildcard /.dockerenv),)
ui: env  ## 대역으로 도는 ui를 띄운다 — http://localhost:8080
	$(COMPOSE) up -d ui
	@echo "http://localhost:$(UI_PORT)  — 로그는 docker compose logs -f ui"
agent: env  ## agent를 띄운다 — 포트는 열지 않는다. ui가 compose 안에서 부른다
	$(COMPOSE) up -d agent
	@echo "로그는 docker compose logs -f agent"
else
# 같은 컨테이너에서 둘 다 띄우므로 ui는 agent를 localhost로 부른다. .env의 주소는 compose용이다.
# devcontainer에는 db·api가 없다 — api 자리에는 메모리 대역이 선다(카테고리 고르기는 근거를 못 찾는다).
ui:  ## 대역으로 도는 ui를 띄운다 — http://localhost:8080 (Ctrl+C로 멈춘다)
	API_BASE_URL= AGENT_BASE_URL=http://localhost:8001 uvicorn ui.main:create_app --factory --reload --reload-dir src/ui --app-dir src --host 0.0.0.0 --port 8080

agent:  ## agent를 띄운다 — http://localhost:8001 (Ctrl+C로 멈춘다. ui와 다른 터미널에서)
	uvicorn agent.main:create_app --factory --reload --reload-dir src/agent --app-dir src --host 0.0.0.0 --port 8001
endif

seed:  ## 기준 데이터(카테고리·결제수단)를 넣는다 — 몇 번을 쳐도 같다
	$(COMPOSE) exec -T api python -m api.seed

demo:  ## 거래가 하나도 없으면 여섯 달치 예시를 넣는다 — 개발용 구성은 뜰 때 알아서 한다
	$(COMPOSE) exec -T api python -m api.seed --demo

docs:  ## 문서 Q&A의 자료(법령 아홉 조문)를 세 전략의 조각으로 넣는다 — 몇 번을 쳐도 같다
	$(COMPOSE) exec -T api python -m api.load_documents tests/fixtures/ai/documents/laws

psql:  ## DB에 붙는다 — 표를 눈으로 볼 때 (\dt, \d text_embeddings)
	$(COMPOSE) exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

review:  ## finish 전 점검 — BASE 이후 바뀐 파일만 (기본 develop)
	$(EXEC) python3 scripts/check_file_length.py --base $(BASE)
	$(EXEC) python3 scripts/check_docs.py

check:  ## 저장소 규칙 검사 — 300줄 상한, 문서 정합성
	$(EXEC) python3 scripts/check_file_length.py
	$(EXEC) python3 scripts/check_docs.py

lint:  ## ruff 검사
	$(EXEC) ruff check .
	$(EXEC) ruff format --check .

format:  ## ruff 자동 수정
	$(EXEC) ruff check --fix .
	$(EXEC) ruff format .

type:  ## mypy strict
	$(EXEC) mypy

test:  ## 단위 테스트
	@$(EXEC) pytest -m "not integration"; status=$$?; \
		if [ $$status -eq 5 ]; then echo "아직 테스트가 없다."; exit 0; fi; \
		exit $$status

# DB가 필요한 테스트. 테스트마다 빈 DB를 만들고 지운다 — 개발용 DB의 데이터는 그대로다.
test-db:  ## DB 통합 테스트 — 실제 Postgres + pgvector. make dev로 db가 떠 있어야 한다
	$(EXEC) pytest -m integration -q tests/api

# 실제 모델을 부른다 — 돈이 들고 점수가 매번 조금씩 다르다. CI에 넣지 않는다.
# agent 컨테이너 안에서 돈다. 키와 api 주소(ui의 대역)가 거기 있다.
eval:  ## 카테고리 고르기 평가 — 실제 모델. make dev로 ui·agent가 떠 있어야 한다
	$(COMPOSE) exec -T agent pytest -m integration -s -q tests/agent/application/use_cases/test_classify_category_eval.py

eval-chat:  ## 대화 통계 평가 — 실제 모델. make dev로 api·agent가 떠 있어야 한다
	$(COMPOSE) exec -T agent pytest -m integration -s -q tests/agent/application/use_cases/test_answer_question_eval.py

all: check lint type test  ## 전부
