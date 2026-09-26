# 대역으로 도는 ui

`api`와 `agent`가 아직 없다. 그래도 화면은 끝까지 돌아야 설계를 손으로 만져 볼 수 있다.
그래서 `src/ui`는 **포트 뒤에 대역을 세워** 돈다. 화면 코드는 대역을 모르고 포트만 안다.
진짜가 생기면 [../src/ui/main.py](../src/ui/main.py)에서 한 줄씩 바꾸고, 화면은 건드리지 않는다.

```bash
make up      # dev와 함께 ui 컨테이너가 뜬다 — http://localhost:8080
make ui      # ui만 띄울 때. devcontainer 안에서는 그 자리에서 직접 띄운다
```

코드는 바인드 마운트라 `src/`를 고치면 서버가 알아서 다시 뜬다. 다시 뜨면 메모리
저장소도 새로 채워진다.

[../mock_ui/](../mock_ui/README.md)와 헷갈리지 않는다. 목은 정적 HTML이고 버튼이 아무것도
하지 않는다. 여기는 버튼이 전부 동작한다 — 뒤에 있는 것이 가짜일 뿐이다.

---

## 1. AI가 들어갈 자리는 넷이다

사람이 손으로 하던 판단 한 가지씩을 대신하는 자리다. 셋 다 Protocol 하나와 각본 대역
하나로 되어 있다. 대역은 키 없이 돌고, **스스로 대역이라고 말한다.**

| 포트 | 대신하는 판단 | 지금 서 있는 대역 | 진짜가 올 곳 |
|---|---|---|---|
| `ChatAgent` | 자연어 한 줄 → 거래 제안이나 답 | `ScriptedChatAgent` — 정해진 모양만 알아듣는다 | `agent`의 `POST /chat` SSE |
| `CategorySuggester` | 가맹점명 → 카테고리 | `ScriptedCategorySuggester` — 낱말 표 | api의 `POST /v1/categories/suggest` |
| `ReportNarrator` | 리포트의 "눈에 띈 것" 문장 | `ScriptedReportNarrator` — 규칙 문구 | 아직 안 정했다([pages/reports.md 3.2](pages/reports.md#32-눈에-띈-것은-문장으로-낸다)) |
| `CardMessageReader` | 카드 결제 문자 → 거래 칸 | `ScriptedCardMessageReader` — 승인 문자 한 모양 | `agent`. 엔드포인트는 아직 안 정했다([pages/transaction-form.md 4.4](pages/transaction-form.md#44-카드-문자를-붙여넣으면-채운다)) |

포트는 `src/ui/application/ports/`, 대역은 `src/ui/infrastructure/scripted/`에 있다.

각본 대역이 알아듣는 것:

- 기록 — 금액이 든 한 줄. `어제 점심 김밥천국 8500원 카드로`, `이마트 3만원 현금`
- 질문 — `얼마`·`보여줘`·`?`가 든 한 줄. `이번 달 식비 얼마 썼어?`, `지난달 카페에 얼마 썼어?`
- 카드 문자 — `신한카드(1234)승인 8,500원 09/16 12:31 김밥천국 누적…` 모양 하나. 누적·잔액
  금액은 거르고, 승인 취소 문자와 금액이 없는 문자는 읽지 않는다고 답한다.
- 그 밖 — 대역이라 못 알아듣는다고 답한다. **규칙을 늘려 LLM 흉내를 내지 않는다.**
  대역이 똑똑해질수록 진짜로 바꿀 때 무엇이 달라졌는지 가려진다.

대역도 규칙은 지킨다. 쓰기는 제안 → 확인 → 실행이고, 확인 전에는 아무것도 쓰지 않는다.
답에 나오는 숫자는 전부 리포트·예산 포트가 낸 값이다.

## 2. api 자리 — 메모리 저장소

| 포트 | 대역 |
|---|---|
| `TransactionGateway` | `MemoryTransactionGateway` |
| `ReportGateway` | `MemoryReportGateway` |
| `BudgetGateway` | `MemoryBudgetGateway` |
| `CatalogGateway` | `MemoryCatalogGateway` |

`src/ui/infrastructure/memory/`에 있다. 합계·페이스·검증·멱등성을 **여기서만** 계산한다.
이 패키지가 api의 대역이기 때문이다. 화면 쪽(`interfaces`)에는 나눗셈 하나 없다.

- 서버를 끄면 기록이 사라진다.
- 처음 뜰 때 오늘을 기준으로 여섯 달치 예시를 채운다. 상단 띠의 버튼으로 비우거나
  다시 채운다 — 빈 화면 두 종류를 보려는 것이다. 이 버튼은 `DemoData` 포트가 있을
  때만 보이고, 진짜 api가 붙으면 사라진다.

## 3. 대역이라 아직 안 하는 것

진짜가 붙을 때 같이 한다. 여기 적어 두지 않으면 된 줄 안다.

- **세션과 신원** — `X-User-Id`, 세션 쿠키가 없다. 단일 사용자 전제다([ui-design.md 3장](ui-design.md#3-세션과-신원)).
- **스트림 재연결** — 끊기면 "다시 보내 주세요"만 띄운다. `run_id`로 이어 받기는
  진짜 `agent`가 있어야 한다([pages/chat.md 4.2](pages/chat.md#42-스트림이-끊기면)).
- **대화 기록** — 새로고침하면 사라진다. 기록은 `agent_runs`의 몫이다.
- **예산은 카테고리당 하나** — 달마다 따로 두지 않는다. `budgets.period`는 api가 생길 때.
- **`confirmation_required`** — 임계값 확인은 api가 판단한다. 대역은 늘 확인 카드를 띄운다.
