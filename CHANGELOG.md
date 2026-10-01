# 변경 기록

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를,
버전은 [semver](https://semver.org)를 따른다. 맨 위가 최신이다.

쓰는 방법은 [docs/release.md](docs/release.md)에 있다.

## Unreleased

### 추가

- **한 줄로 채우기에 진짜 AI** — 거래 폼에 카드 문자나 "어제 저녁 교촌치킨 2만3천원 현금"
  같은 한 줄을 보내면 `agent`가 LLM(기본 Gemini Flash-Lite)으로 읽어 칸을 채운다. 각본
  대역이 알아듣지 못하던 모양도 읽는다. 날짜는 LLM이 아니라 코드가 계산하고, 글에 없는
  가맹점명은 버린다. 저장은 여전히 사람이 누른다.
  ([ui_docs/pages/transaction-form.md](ui_docs/pages/transaction-form.md) 4.5)
- **카테고리 AI로 고르기(RAG)** — 거래 폼의 카테고리 옆 버튼을 누르면 `agent`가 내 지난
  기록에서 비슷한 거래를 찾아 고르고, 셀렉트 아래에 근거 한 줄을 보여 준다("같은 가맹점 최근
  5건 중 5건: 식비", "비슷한 기록: 메가커피 · 스타벅스 → 카페"). 자주 가는 곳은 LLM 없이
  기록만으로 정하고, 처음 보는 곳이 애매할 때만 LLM이 근거를 보고 고른다. 한 줄로 채우기도
  카테고리를 같은 방법으로 채운다. 평가는 `make eval`.
  ([docs/ai/category-suggestion-rag.md](docs/ai/category-suggestion-rag.md))
- **`agent` 서비스** — compose에 붙었다. 포트를 열지 않고 `ui`만 부른다. LLM 키를 가진
  유일한 서비스다. ([README.md](README.md) 3장)

- **기록이 DB에 남는다** — `make dev`로 띄운 화면이 진짜 `api`를 쓴다. 거래·예산이 PostgreSQL에
  저장돼 다시 띄워도 그대로다. 카테고리 고르기의 검색도 `api`로 옮겨 가 벡터 이웃을 pgvector(코사인
  거리, HNSW 인덱스)로 찾는다 — 방금 저장한 거래가 다음 분류의 근거가 된다.
  ([ui_docs/stand-ins.md](ui_docs/stand-ins.md))
- **집계·예산 api** — `/v1/summary`, `/v1/reports/monthly`·`pace`, `/v1/budgets/status`,
  `PUT /v1/budgets/{category_id}`. 합계는 DB가 내고, 페이스(말일 예상·넘는 날)는 사용자 타임존의 날로 센다.
  예산은 바꾼 달부터 이어진다 — 한 번 정하면 바꿀 때까지 매달 같다.
- **거래 api** — `api`가 `/v1/transactions`(목록·한 건·넣기·고치기·지우기)와 `/v1/categories`·
  `/v1/accounts`를 낸다. 쓰기는 멱등 키를 DB에 저장하고(같은 키 두 번 = 한 건), 10만 원 이상과 삭제는
  확인 머리글이 있어야 한다. 개발용 구성은 DB가 비어 있으면 여섯 달치 예시 거래를 넣는다(`make demo`).
- **`db`와 `api`** — PostgreSQL(pgvector 확장 포함)과 그 앞의 `api` 서비스가 compose에 떴다.
  스키마는 README 7장의 테이블과 카테고리 고르기의 `text_embeddings`(768차원, 코사인 HNSW
  인덱스)·`category_rules`. `api`가 뜰 때 Alembic으로 스키마를 올리고, `make seed`가 카테고리·
  결제수단을 넣는다.
  (README 7장, [docs/development-rules.md](docs/development-rules.md) 6.6)

### 변경

- **데모 버튼(비우기·다시 채우기)이 사라졌다.** 진짜 api에서는 쓰던 가계부를 비우는 버튼을 두지
  않는다. 예시는 DB가 비어 있을 때 개발용 구성이 한 번 넣는다(`make demo`). api 없이
  `API_BASE_URL`을 비우고 띄우면 메모리 대역과 함께 버튼이 돌아온다.
- **각 서비스는 자기 비밀만 받는다.** ui는 키도 DB 비밀번호도, agent는 DB 비밀번호를, api는 LLM 키를
  모른다. compose가 `.env`를 통째로 넘기지 않는다.
- **가맹점을 넣어도 카테고리가 저절로 채워지지 않는다.** AI로 고르기를 눌러야 고른다 —
  누르기 전에는 AI를 부르지 않는다. 한 줄로 채우기는 지금처럼 카테고리까지 채운다.
- `.env.sample`에 카테고리 고르기의 변수 여섯(`EMBEDDING_MODEL` 등)이 생겼다. 기본 임베딩은
  `gemini/gemini-embedding-001`이라 `GEMINI_API_KEY`가 있어야 한다. 비우면 벡터 검색 없이
  돈다.
- **`.env`에 `POSTGRES_PASSWORD`를 채워야 뜬다.** 비어 있으면 compose가 멈춘다. `POSTGRES_HOST`·
  `POSTGRES_PORT`도 생겼다(`db`, `5432`). 의존성이 바뀌었으니 `make build`를 한 번 친다.
- **`make dev`가 `agent`도 띄운다.** `.env`에 `AGENT_MODEL` 제공자의 키(기본은
  `GEMINI_API_KEY`)가 있어야 뜬다. 키 없이 화면만 보려면 `AGENT_BASE_URL`을 비운다 —
  지금까지처럼 각본 대역이 선다.
- **이미지가 서비스마다 하나다.** `ui` 이미지에는 LLM 라이브러리도 `agent` 코드도 들어가지
  않는다. `ui` 컨테이너는 `.env`를 통째로 받지 않고 쓰는 변수만 받는다 — LLM 키를 모른다.
- `.env.sample`의 `AGENT_MODEL` 기본값을 `gemini/gemini-flash-lite-latest`로 바꾸고,
  `AGENT_TIMEOUT_SECONDS`를 더했다. 의존성이 바뀌었으니 `make build`를 한 번 친다.

## 0.2.0 — 2026-09-26

화면이 생겼다. **AI는 아직 붙지 않았다** — `api`·`agent` 자리에 메모리 저장소와 각본 대역이
서서, 버튼은 전부 동작하지만 기록은 서버를 끄면 사라진다.

### 추가

- **동작하는 ui** — 채팅·거래 목록·입력·리포트·예산이 끝까지 돈다. `make dev`로 띄우면
  <http://localhost:8080>. 처음 뜰 때 여섯 달치 예시 데이터가 들어 있고, 상단 띠의 버튼으로
  비우거나 다시 채울 수 있다. ([ui_docs/stand-ins.md](ui_docs/stand-ins.md))
- **한 줄로 채우기** — 거래 폼에 카드 결제 문자를 붙여넣거나 "오늘 오후 3시에 카페에서
  5천원 썼어"처럼 적으면 금액·날짜·가맹점·결제수단·카테고리가 채워진다. 채워진 칸에는
  "AI가 채움" 표시가 붙고, 저장은 사람이 누른다.
  ([ui_docs/pages/transaction-form.md](ui_docs/pages/transaction-form.md) 4.4)
- **AI 표시와 AI 위키** — AI가 들어갈 자리 넷(기록, 카테고리 고르기, 대화로 묻는 통계,
  상황에 맞는 통계)에 `AI · 단발`처럼 어떤 에이전트 흐름이 도는지를 달았다. 누르면 상단 바
  오른쪽 끝의 AI 위키(`/wiki`)로 가서, 어디에 어떤 흐름이 도는지와 지금 서 있는 대역을
  볼 수 있다. ([ui_docs/pages/wiki.md](ui_docs/pages/wiki.md))
- **AI 기능 설계** — 카테고리 고르기(RAG), 대화로 묻는 통계, 상황에 맞는 통계, 그리고
  세 기능에 걸리는 도구 규약·에이전트 흐름·외부 AI가 들어오는 MCP 통로.
  ([docs/ai/README.md](docs/ai/README.md))
- **개발용 compose** — `make dev`로 띄우면 코드·템플릿·CSS는 저장하는 대로 반영되고,
  의존성이 바뀌면 이미지를 다시 만들어 띄운다. ([README.md](README.md) 9장)

### 변경

- **`docker compose up`은 운영처럼 뜬다.** 코드를 이미지에 굽고, 고쳐도 다시 뜨지 않는다.
  개발할 때는 `make dev`(또는 `make up`)를 쓴다. 의존성이 바뀐 뒤 옛 이미지로 뜨면
  `docker compose up --build`로 다시 만든다.
- **목 UI는 8081로 옮겼다.** `make mock` → <http://localhost:8081>. 8080은 ui가 쓴다.
- **화면 모양** — 목 UI의 모양에서 shadcn/ui(new-york, neutral)의 모양으로. 빌드 단계는
  없다. ([ui_docs/ui-design.md](ui_docs/ui-design.md) 7장)

## 0.1.1 — 2026-09-17

### 수정

- 릴리스 태그가 `v` 없이 붙던 것. 이제 `v0.1.1`처럼 붙는다.
  **이미 클론해 둔 저장소는 [docs/release.md](docs/release.md) 1장의 설정 두 줄을
  한 번 실행해야 한다.** 설정은 저장소마다 따로 있어서 커밋으로는 따라오지 않는다.

## 0.1.0 — 2026-09-17

첫 릴리스. **동작하는 가계부는 아직 없다.** 무엇을 만들지 정한 설계와, 그것을 만들
개발 기반이 들어 있다. `0.x`는 언제든 깨질 수 있다는 뜻이다.

### 추가

- **설계** — AI 에이전트가 들어가는 가계부가 어떤 형태인지. `ui` · `agent` · `api` · `db`
  네 서비스와 그 사이에 그은 경계 두 개. 에이전트는 DB를 모르고, 화면은 도메인 로직을
  갖지 않는다. ([README.md](README.md))
- **개발 룰** — 한 파일 300줄, 한 파일 한 클래스, clean architecture 네 계층,
  strict 타입, 그리고 시간·비동기·설정·로깅·예외를 다루는 규칙.
  ([docs/development-rules.md](docs/development-rules.md))
- **api 계약** — 에이전트가 재시도해도 같은 거래가 두 번 들어가지 않게 하는 멱등성 규약,
  신원을 넘기는 헤더, 에러 코드, 엔드포인트 목록. ([docs/api-contract.md](docs/api-contract.md))
- **화면 설계** — 대화로 넣는 길과 폼으로 넣는 길을 대등하게 둔 구성, 화면 다섯 개의
  구조와 빈 상태. ([ui_docs/](ui_docs/ui-design.md))
- **목 UI** — 서버 없이 화면을 눈으로 보는 정적 HTML 여섯 장. 리포트에는 인라인 SVG
  차트 세 장이 들어 있다. `make mock`으로 띄운다. ([mock_ui/](mock_ui/README.md))
- **개발 기반** — `make`와 docker만 있으면 된다. 파이썬도 ruff도 mypy도 호스트에
  설치하지 않는다. `make up` 뒤에 `make all`.
- **Codespaces** — 같은 컨테이너로 열린다. 로컬과 환경이 갈라지지 않는다.
- **검사** — 파일 길이와 문서 정합성을 기계가 본다. 문서끼리 어긋난 링크·앵커·도구
  이름·에러 코드를 잡는다. ([scripts/](scripts/check_docs.py))
- **작업 절차** — git flow 브랜치 구성, `finish` 전 점검, 릴리스 절차.
  ([docs/git-flow-guide.md](docs/git-flow-guide.md), [docs/release.md](docs/release.md))

### 아직 없음

`src/`가 비어 있다. 서비스 코드도, 테스트도, 배포도 다음 버전부터다.
