# 대역으로 도는 ui

`api`는 떴고 거래·카탈로그·집계·예산을 DB로 한다. 그래도 화면은 아직 아래의 메모리 대역으로
돈다 — 카테고리 검색이 같은 저장소를 읽어서, 그것까지 `api`에 생긴 뒤 한꺼번에 바꾼다. `agent`는 기록(한 줄로 채우기)과 카테고리 고르기만 한다. 그래도 화면은 끝까지 돌아야
설계를 손으로 만져 볼 수 있다. 그래서 `src/ui`는 **포트 뒤에 대역을 세워** 돈다. 화면 코드는
대역을 모르고 포트만 안다. 진짜가 생기면 [../src/ui/main.py](../src/ui/main.py)에서 한 줄씩
바꾸고, 화면은 건드리지 않는다.

```bash
make dev     # 개발용으로 띄우고 라이브 업데이트 — http://localhost:8080
make ui      # ui만 띄울 때. devcontainer 안에서는 그 자리에서 직접 띄운다
```

코드는 바인드 마운트라 `src/`를 고치면 서버가 알아서 다시 뜬다. 다시 뜨면 메모리
저장소도 새로 채워진다.

[../mock_ui/](../mock_ui/README.md)와 헷갈리지 않는다. 목은 정적 HTML이고 버튼이 아무것도
하지 않는다. 여기는 버튼이 전부 동작한다 — 뒤에 있는 것이 가짜일 뿐이다.

---

## 1. AI가 들어갈 자리는 넷이다

사람이 손으로 하던 판단 한 가지씩을 대신하는 자리다. 모두 Protocol 하나와 각본 대역
하나로 되어 있다. 대역은 키 없이 돌고, **스스로 대역이라고 말한다.**

화면에서는 자리마다 `AI · 흐름` 표시가 붙고, 누르면 [AI 위키](pages/wiki.md)(`/wiki`)의 그
자리로 간다. 자리 목록은 `src/ui/interfaces/ai_map` 한 곳에 있다.

| 포트 | 대신하는 판단 | 지금 서 있는 대역 | 진짜가 올 곳 |
|---|---|---|---|
| `ChatAgent` | 자연어 한 줄 → 거래 제안이나 답 | `ScriptedChatAgent` — 정해진 모양만 알아듣는다 | `agent`의 `POST /chat` SSE |
| `CategorySuggester` | 가맹점·메모 → 카테고리 | `ScriptedCategorySuggester` — 낱말 표 | **붙었다.** `AgentCategorySuggester` → `agent`의 `POST /classify`([pages/transaction-form.md 4.1](pages/transaction-form.md#41-카테고리는-ai로-고르기를-누를-때만-고른다)) |
| `ReportNarrator` | 리포트의 "눈에 띈 것" 문장 | `ScriptedReportNarrator` — 규칙 문구 | 아직 안 정했다([pages/reports.md 3.2](pages/reports.md#32-눈에-띈-것은-문장으로-낸다)) |
| `CaptureReader` | 카드 문자나 말로 쓴 한 줄 → 거래 칸 (기록) | `ScriptedCaptureReader` — 승인 문자 한 모양과 채팅 대역의 귀 | **붙었다.** `AgentCaptureReader` → `agent`의 `POST /capture`([pages/transaction-form.md 4.5](pages/transaction-form.md#45-agent와-주고받는-것--post-capture)) |

포트는 `src/ui/application/ports/`, 대역은 `src/ui/infrastructure/scripted/`에 있다.

진짜가 선 자리는 `AGENT_BASE_URL`로 고른다. 값이 있으면 그 주소의 `agent`를 부르고, 비어
있으면 각본 대역이 선다 — 키 없이 화면을 만질 때다. 위키는 지금 어느 자리에 진짜가 섰는지
말한다(`Services.live_seats`). 테스트는 언제나 각본 대역으로 돈다.

각본 대역이 알아듣는 것:

- 기록 — 금액이 든 한 줄. `어제 점심 김밥천국 8500원 카드로`, `이마트 3만원 현금`
- 질문 — `얼마`·`보여줘`·`?`가 든 한 줄. `이번 달 식비 얼마 썼어?`, `지난달 카페에 얼마 썼어?`
  금액은 `5천원`·`1만5천원`처럼 써도 되고, 시각은 `오후 3시`·`3시 반`, 가맹점은 `카페에서`처럼
  장소 조사가 붙은 낱말을 먼저 본다. 말하지 않은 날짜·결제수단은 채우지 않는다.
- 카드 문자 — `신한카드(1234)승인 8,500원 09/16 12:31 김밥천국 누적…` 모양 하나. 누적·잔액
  금액은 거르고, 승인 취소 문자와 금액이 없는 문자는 읽지 않는다고 답한다.
  거래 폼의 한 줄로 채우기는 카드 문자와 기록 한 줄을 둘 다 받고, 질문은 채팅으로 돌려보낸다.
- 그 밖 — 대역이라 못 알아듣는다고 답한다. **규칙을 늘려 LLM 흉내를 내지 않는다.**
  대역이 똑똑해질수록 진짜로 바꿀 때 무엇이 달라졌는지 가려진다.

대역도 규칙은 지킨다. 쓰기는 제안 → 확인 → 실행이고, 확인 전에는 아무것도 쓰지 않는다.
답에 나오는 숫자는 전부 리포트·예산 포트가 낸 값이다.

## 2. api 자리 — 메모리 저장소

진짜 `api`와 `db`(PostgreSQL + pgvector)는 compose에 떠 있다. 거래·카탈로그·집계·예산 포트의
진짜(`Http*Gateway`, `src/ui/infrastructure/api/`)도 있다. 아직 끼우지 않았을 뿐이다 — 카테고리
검색 대역이 메모리 저장소의 거래를 읽기 때문이다. 검색까지 `api`에 생기면 `API_BASE_URL` 하나로
한꺼번에 바뀐다.

| 포트 | 대역 |
|---|---|
| `TransactionGateway` | `MemoryTransactionGateway` |
| `ReportGateway` | `MemoryReportGateway` |
| `BudgetGateway` | `MemoryBudgetGateway` |
| `CatalogGateway` | `MemoryCatalogGateway` |
| `CategoryIndex` | `MemoryCategoryIndex` — 카테고리 검색(규칙 → 이력 → 벡터 이웃)과 색인 |

`src/ui/infrastructure/memory/`에 있다. 합계·페이스·검증·멱등성·카테고리 검색을 **여기서만** 계산한다.
이 패키지가 api의 대역이기 때문이다. 화면 쪽(`interfaces`)에는 나눗셈 하나 없다.

- 서버를 끄면 기록이 사라진다.
- 처음 뜰 때 오늘을 기준으로 여섯 달치 예시를 채운다. 상단 띠의 버튼으로 비우거나
  다시 채운다 — 빈 화면 두 종류를 보려는 것이다. 이 버튼은 `DemoData` 포트가 있을
  때만 보이고, 진짜 api가 붙으면 사라진다.

### 2.1 agent가 부르는 api 대역 — `/v1`

카테고리 고르기는 검색이 `api`, 판단이 `agent`다. `agent`는 `api`를 HTTP로 부르는데 `api`가
없으니, `ui`가 `CategoryIndex`를 계약 그대로 `/v1`으로 연다
([../docs/api-contract.md 6장](../docs/api-contract.md#6-엔드포인트-초안)).

| 메서드 | 경로 | 하는 일 |
|---|---|---|
| `POST` | `/v1/categories/suggest` | 후보 + 근거 + 그 방향의 카테고리 사전 |
| `GET` | `/v1/embeddings/pending` | 그 모델의 벡터가 없는 색인 텍스트 |
| `PUT` | `/v1/embeddings/{text_hash}` | 벡터 저장. `Idempotency-Key`가 없으면 400 |

compose는 `agent`의 `API_BASE_URL`을 `http://ui:8080`으로 덮는다. `api`가 서면 그 한 줄을
지우고 이 라우터는 빠진다. 벡터는 메모리에 있어서 `ui`를 다시 띄우면 비고, 다음 분류 요청 때
`agent`가 다시 채운다(시드의 고유 텍스트 30여 개, 1초 남짓).

## 3. 대역이라 아직 안 하는 것

진짜가 붙을 때 같이 한다. 여기 적어 두지 않으면 된 줄 안다.

- **세션과 신원** — `X-User-Id`, 세션 쿠키가 없다. 단일 사용자 전제다([ui-design.md 3장](ui-design.md#3-세션과-신원)).
- **스트림 재연결** — 끊기면 "다시 보내 주세요"만 띄운다. `run_id`로 이어 받기는
  진짜 `agent`가 있어야 한다([pages/chat.md 4.2](pages/chat.md#42-스트림이-끊기면)).
- **대화 기록** — 새로고침하면 사라진다. 기록은 `agent_runs`의 몫이다.
- **예산은 카테고리당 하나** — 대역은 달마다 따로 두지 않는다. `api`는 바뀐 달을 적고 바꿀 때까지
  이어 쓴다([../docs/api-contract.md 6장](../docs/api-contract.md#예산은-바꿀-때까지-이어진다)) — 화면에서는 같아 보인다.
- **`confirmation_required`** — 임계값 확인은 api가 판단한다. 대역은 늘 확인 카드를 띄운다.
- **`/v1`이 ui의 공개 포트에 열린다** — 2.1의 api 대역은 `agent`만 부르라고 연 것인데, `ui`의
  8080에 같이 열려 있어서 브라우저도 부를 수 있다. 읽는 것은 카테고리 검색과 색인 텍스트(가맹점·
  메모)뿐이고 단일 사용자 전제지만, 진짜 `api`는 compose 내부에만 연다(README 3장).
- **규칙 표를 만드는 화면** — `category_rules`(0단계)는 자리만 있고 비어 있다. "김밥천국은
  항상 식비로 할까요?" 승격 배너는 아직 없다([../docs/ai/category-suggestion-rag.md 8.2](../docs/ai/category-suggestion-rag.md#82-고친-것이-다음-답이-된다)).
