# api 계약

`api`가 노출하는 HTTP 계약. **`agent`의 도구와 `ui`가 같이 쓴다.**
에이전트가 할 수 있는 일의 목록이 곧 이 계약이므로([../README.md](../README.md) 경계 1),
여기 없는 동작은 에이전트도 못 한다.

> **OpenAPI와 나누는 기준** — 엔드포인트별 필드와 타입은 FastAPI가 자동 생성하는
> `/docs`가 정본이다. 이 문서는 자동 생성이 담지 못하는 것만 적는다. 규약(멱등성, 헤더,
> 에러 코드), 그리고 왜 그렇게 정했는지. 필드 목록을 여기에 복사해 두지 않는다 — 곧 어긋난다.

---

## 1. 공통 규약

- 모든 경로는 `/v1` 아래. 깨는 변경은 `/v2`로 가고, `/v1`을 조용히 바꾸지 않는다.
- 요청·응답은 JSON, 필드명은 snake_case.
- 시간은 RFC 3339에 오프셋을 붙인다 — `2026-09-16T12:30:00+09:00`.
  오프셋 없는 문자열은 거부한다([development-rules.md 6.1](development-rules.md#61-시간--저장은-utc-경계는-사용자-타임존)).
- 금액은 정수 최소단위와 통화를 함께 보낸다. 소수점은 없다.

```json
{ "amount": 8500, "currency": "KRW" }
```

---

## 2. 헤더 — 누가 무엇을 대신하는가

| 헤더 | 보내는 쪽 | 뜻 |
|---|---|---|
| `X-User-Id` | `ui` → `agent` → `api` | 이 요청의 주인. **`agent`가 만들어 내지 않고 받은 것을 그대로 전달한다** |
| `X-Request-Id` | `ui`가 생성 | 로그 상관관계. 끝까지 전파한다 |
| `X-Agent-Run-Id` | `agent`만 | 있으면 `source=agent`와 `run_id`를 거래에 박는다. 없으면 `source=manual` |
| `X-Confirmed-By` | `ui` → `agent` → `api` | 사용자가 확인한 쓰기에만 붙는다 (4장) |
| `Idempotency-Key` | 쓰기 요청 전부 | 3장 |

인증은 아직 없다. 단일 사용자이고 `api`는 compose 내부 네트워크에만 열려 있다는 전제다.
다중 사용자로 가는 순간 `X-User-Id`는 서명된 토큰으로 바뀐다. **그때까지 `api`를
호스트로 노출하지 않는다.**

---

## 3. 멱등성 — 같은 거래가 두 번 들어가지 않게

**이 계약에서 가장 중요한 부분이다.**

에이전트 루프는 실패하면 재시도한다. `POST /v1/transactions`가 타임아웃 났는데 실제로는
DB에 들어간 상황에서 재시도하면, 같은 지출이 두 건이 된다. 가계부에서 이건 합계가 틀리는
버그이고, 사용자는 한참 뒤에야 알아챈다.

### 규칙

- **모든 쓰기 요청(`POST`·`PATCH`·`PUT`·`DELETE`)에 `Idempotency-Key`가 필수다.**
  없으면 `400 idempotency_key_required`. 읽기에는 필요 없다.
- 에이전트는 키를 `{run_id}:{tool_call_seq}`로 만든다. 재시도해도 같은 키가 나온다.
  `ui`의 직접 입력은 화면에서 만든 UUID를 쓴다.
- `api`는 키마다 `(요청 본문 해시, 응답 본문, 상태 코드)`를 저장한다.

| 상황 | 응답 |
|---|---|
| 처음 보는 키 | 실행하고, 결과를 키와 함께 저장한다 |
| 같은 키 + 같은 본문 | **다시 실행하지 않고** 저장된 응답을 그대로 돌려준다 |
| 같은 키 + 다른 본문 | `409 idempotency_key_reused` |
| 처리 중인 키가 또 들어옴 | `409 request_in_progress` |

- 보존 기간은 24시간. 그 뒤 키는 지워지고, 같은 키가 와도 새 요청으로 본다.
- 저장은 실제 쓰기와 **같은 트랜잭션**에서 한다. 따로 커밋하면 그 사이에 중복이 들어간다.

```
POST /v1/transactions
Idempotency-Key: 01J9X...:3
X-Agent-Run-Id: 01J9X...
```

---

## 4. 확인이 필요한 쓰기

확인을 받는 화면은 `ui`가 그리고 대화는 `agent`가 하지만, **판단은 `api`가 한다.**
권한을 한 곳에서만 지키기로 했기 때문이다.

- `AGENT_CONFIRM_THRESHOLD` 이상의 금액, 그리고 모든 `DELETE`는 `X-Confirmed-By: user`가
  없으면 `412 confirmation_required`로 거부한다.
- 에이전트는 412를 받으면 사용자에게 확인을 묻고, 확인을 받으면 **같은 `Idempotency-Key`로**
  헤더를 붙여 다시 보낸다.
- 거부된 요청도 `tool_calls`에 남는다. 무엇을 하려다 막혔는지가 감사에서는 중요하다.

> **한계를 적어 둔다.** `X-Confirmed-By`는 에이전트가 붙이는 헤더라서, 에이전트가
> 거짓으로 붙이는 걸 `api`가 구분할 수 없다. 사용자를 대신해 호출하는 구조에서는 피할 수
> 없다. 그래서 확인 여부는 `tool_calls.confirmed_at`에 기록되고, 사후에 대조할 수 있다.
> 이 구멍을 진짜로 막으려면 확인 토큰을 `ui`가 서명해 넘겨야 한다 — 다중 사용자로 갈 때 같이 한다.

---

## 5. 에러 응답

모든 에러는 같은 모양이다.

```json
{
  "error": {
    "code": "budget_exceeded",
    "message": "이번 달 식비 예산을 32,000원 초과합니다.",
    "details": { "category_id": "food", "over_by": 32000 },
    "request_id": "01J9X..."
  }
}
```

- **`code`는 기계가 읽고 `message`는 사람이 읽는다.** 에이전트는 `code`로 분기한다.
  `message` 문자열을 파싱하는 코드는 만들지 않는다.
- `code` 목록과 상태 코드 매핑은
  [development-rules.md 6.5](development-rules.md#65-예외)의 표가 정본이다.
- `500`의 `message`는 항상 일반 문구다. 스택·SQL·경로는 로그에만 남는다(6.4).
- `details`는 선택이다. 에이전트가 사용자에게 설명할 때 쓸 값만 담는다.

### 5.1 프로토콜 코드

도메인 예외에서 나오지 않는, 이 계약 자체의 코드들. 도메인 쪽 코드는
[development-rules.md 6.5](development-rules.md#65-예외)에 있다.

| 상태 | 코드 | 언제 |
|---|---|---|
| `400` | `idempotency_key_required` | 쓰기 요청에 `Idempotency-Key`가 없다 |
| `409` | `idempotency_key_reused` | 같은 키로 다른 본문이 왔다 |
| `409` | `request_in_progress` | 같은 키의 요청이 아직 처리 중이다 |

에이전트는 `request_in_progress`를 받으면 재시도하지 않고 기다린다. 이미 같은 일이
진행 중이라는 뜻이라서, 재시도가 중복을 만들지는 않지만 루프 예산만 태운다.

---

## 6. 엔드포인트 (초안)

도구와 1:1로 맞춘다. 도구 하나가 엔드포인트 둘을 부르는 일이 없게 한다.

| 메서드 | 경로 | 대응 도구 | 확인 |
|---|---|---|---|
| `GET` | `/v1/transactions` | `search_transactions` | — |
| `POST` | `/v1/transactions` | `create_transaction` | 임계값 이상 |
| `PATCH` | `/v1/transactions/{id}` | `update_transaction` | 임계값 이상 |
| `DELETE` | `/v1/transactions/{id}` | `delete_transaction` | **항상** |
| `GET` | `/v1/summary` | `summarize_spending` | — |
| `GET` | `/v1/budgets/status` | `get_budget_status` | — |
| `PUT` | `/v1/budgets/{category_id}` | `set_budget` | 확인 |
| `POST` | `/v1/categories/suggest` | `suggest_category` | — |
| `GET` | `/v1/healthz` | — | — |

### 집계는 서버가 한다

`summary`와 `budgets/status`는 **계산된 숫자**를 돌려준다. 거래 목록을 내려주고
에이전트가 합산하게 두지 않는다. LLM에게 산수를 시키지 않는다는 원칙(README 1장)이
계약 수준에서 지켜져야 하는 자리다.

### 목록은 항상 페이지네이션

`GET /v1/transactions`는 기본 50건, 최대 200건을 넘기지 않는다. 커서로 넘긴다.
에이전트가 3년치 거래를 통째로 받아 컨텍스트에 밀어 넣는 일을 계약이 막는다.

---

## 7. 이 문서를 고치는 때

- 도구를 추가하면 여기 표에 줄이 하나 늘어난다. 반대도 같다.
- 에러 `code`를 추가하면 [development-rules.md 6.5](development-rules.md#65-예외)와 함께 고친다.
- 필드가 바뀌었을 때는 고치지 않는다. 그건 OpenAPI가 안다.
