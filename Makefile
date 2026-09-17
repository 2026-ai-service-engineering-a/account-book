# 모든 명령은 컨테이너 안에서 돈다. 호스트에는 아무것도 설치하지 않는다.
COMPOSE := docker compose
EXEC := $(COMPOSE) exec -T dev
BASE ?= develop

.DEFAULT_GOAL := help
.PHONY: help env build up down shell review check lint format type test all

help:  ## 이 목록
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*## /\t/' | expand -t 12

env:  ## .env가 없으면 .env.sample에서 만든다
	@[ -f .env ] || { cp .env.sample .env; echo ".env를 만들었다. 키를 채운다."; }

build: env  ## 이미지를 빌드한다
	$(COMPOSE) build

up: env  ## 도구 컨테이너를 띄운다
	$(COMPOSE) up -d

down:  ## 컨테이너를 내린다
	$(COMPOSE) down

shell:  ## 컨테이너 안으로 들어간다
	$(COMPOSE) exec dev bash

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

all: check lint type test  ## 전부
