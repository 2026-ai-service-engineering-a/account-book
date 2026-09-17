# 개발 룰

이 저장소의 코드가 지켜야 할 규칙. 리뷰에서 매번 다시 다투지 않으려고 미리 정해둔다.
규칙을 어겨야 할 이유가 생기면 [9장](#9-룰을-어겨야-할-때)의 절차를 따른다.

전체 구성은 [../README.md](../README.md)를 먼저 읽는다. 이 문서는 그 구성을
**코드로 어떻게 배치하느냐**만 다룬다.

---

## 1. 파일

### 1.1 한 파일은 300줄을 넘지 않는다

공백·주석·import를 포함한 실제 줄 수 기준이다. 250줄을 넘으면 리뷰에서 한 번 묻고,
300줄에서 CI가 막는다. 테스트 파일도 똑같이 적용한다.

300줄은 **목표가 아니라 한계**다. 대부분의 파일은 100줄 아래여야 정상이다.
300줄에 가까워졌다는 건 거의 항상 아래 중 하나다.

1. **한 파일에 클래스가 둘 이상** → 1.2 위반이다. 쪼갠다.
2. **유스케이스가 둘 이상** → 유스케이스 하나에 파일 하나.
3. **함수 하나가 100줄** → 계층이 섞인 신호다. 도메인 규칙을 `domain`으로 내린다.
4. **위 셋 다 아닌데 길다** → 책임이 둘이다. 이름을 두 개 붙여보면 갈라지는 자리가 보인다.

길다고 기계적으로 반 잘라 `_part2.py`를 만드는 건 규칙 위반보다 나쁘다.

### 1.2 한 파일에 클래스 하나

엔티티, 값 객체, 데이터클래스, 유스케이스, 리포지토리, 어댑터 전부 해당한다.

- 파일명 = 클래스명의 snake_case. `Transaction` → `transaction.py`,
  `CreateTransaction` → `create_transaction.py`.
- 패키지 `__init__.py`에서 re-export 해 import 경로를 짧게 유지한다.

```python
# src/api/domain/entities/__init__.py
from .budget import Budget
from .transaction import Transaction

__all__ = ["Budget", "Transaction"]
```

```python
# 쓰는 쪽은 짧게
from api.domain.entities import Transaction
```

**유일한 예외**: 그 클래스 *전용*으로만 쓰이는 Enum·TypedDict·상수는 같은 파일에 둔다.
다른 모듈이 import하는 순간 자기 파일로 나간다.

### 1.3 파일 이름

- 모듈·패키지는 snake_case.
- 축약하지 않는다. `txn.py`가 아니라 `transaction.py`.
- `utils.py` · `helpers.py` · `common.py` · `misc.py`는 금지한다.
  무엇이든 들어갈 수 있는 이름에는 결국 무엇이든 들어간다. 그 코드가 무슨 일을 하는지로
  이름을 짓는다 — `money_format.py`, `date_range.py`.

---

## 2. 아키텍처 — Clean Architecture

### 2.1 계층 넷

| 계층 | 들어가는 것 | import해도 되는 것 |
|---|---|---|
| `domain` | 엔티티, 값 객체, 도메인 예외, 도메인 규칙 | **표준 라이브러리만** |
| `application` | 유스케이스, 포트(추상 인터페이스), DTO | `domain` |
| `infrastructure` | 리포지토리 구현, DB 세션, HTTP 클라이언트, LLM 어댑터 | `domain`, `application` |
| `interfaces` | FastAPI 라우터, 요청/응답 스키마, CLI, 템플릿 | `domain`, `application` |

### 2.2 의존 규칙 — 화살표는 안쪽으로만

```
interfaces ─┐
            ├─→ application ─→ domain
infrastructure ─┘
```

`domain`은 아무것도 import하지 않는다. sqlalchemy도, pydantic도, fastapi도 `domain`에
들어오지 않는다. 도메인이 바깥을 필요로 하면 `application`에 **포트**(추상 클래스)를 두고
`infrastructure`가 구현한다. 둘을 잇는 일은 조립 지점(`main.py`)에서만 한다.

한 문장 판정법: **`domain` 폴더만 떼어 다른 프로젝트에 붙여도 import 에러가 나지 않아야 한다.**

```python
# src/api/application/ports/transaction_repository.py  — 포트 (추상)
class TransactionRepository(ABC):
    @abstractmethod
    def add(self, transaction: Transaction) -> Transaction: ...

# src/api/infrastructure/repositories/sql_transaction_repository.py  — 구현
class SqlTransactionRepository(TransactionRepository):
    ...
```

유스케이스는 `SqlTransactionRepository`를 모른다. `TransactionRepository`만 안다.
덕분에 application 계층 테스트에 DB가 필요 없다.

### 2.3 서비스끼리 import하지 않는다

`src/api`, `src/agent`, `src/ui`는 서로를 import하지 않는다. 통신 수단은 HTTP 하나뿐이다.
README의 "의존은 한 방향" 규칙을 코드 레벨에서도 그대로 지킨다.

공용 코드가 정말 필요하면 `src/shared`에 두되, **도메인 지식은 넣지 않는다.**
`shared`에 `Transaction`이 생기는 순간 서비스 경계는 사라진 것이다.

### 2.4 계층 깊이는 서비스마다 다르다

- `api` — 네 계층 전부. 도메인 규칙이 사는 곳이다.
- `agent` — 네 계층. `domain`은 도구 스키마와 루프 상태, `application`은 ReAct 루프와
  하네스 정책, `infrastructure`는 litellm 어댑터와 api 클라이언트.
- `ui` — `domain`이 사실상 없다. 화면과 세션뿐이다.

**없는 계층의 빈 폴더를 만들지 않는다.** 필요해질 때 만든다.

---

## 3. 디렉터리 구조

```
account-book/
├── src/
│   ├── shared/                  # 서비스 공통 — 도메인 지식 없음
│   ├── api/
│   │   ├── domain/
│   │   │   ├── entities/        # transaction.py, budget.py, account.py ...
│   │   │   ├── values/          # money.py, period.py ...
│   │   │   └── errors/
│   │   ├── application/
│   │   │   ├── use_cases/       # create_transaction.py, summarize_spending.py ...
│   │   │   ├── ports/           # transaction_repository.py ...
│   │   │   └── dto/
│   │   ├── infrastructure/
│   │   │   ├── db/              # 세션, 매핑
│   │   │   └── repositories/    # sql_transaction_repository.py ...
│   │   ├── interfaces/
│   │   │   ├── routers/
│   │   │   └── schemas/         # 요청·응답 (도메인 객체를 그대로 노출하지 않는다)
│   │   └── main.py              # 조립 지점 — 여기서만 구현체를 주입한다
│   ├── agent/
│   │   ├── domain/              # 도구 스키마, 루프 상태
│   │   ├── application/         # ReAct 루프, 하네스 정책
│   │   ├── infrastructure/      # litellm 어댑터, api HTTP 클라이언트
│   │   ├── interfaces/          # HTTP + SSE 엔드포인트, CLI
│   │   └── main.py
│   └── ui/
│       ├── application/
│       ├── infrastructure/      # api·agent 클라이언트
│       ├── interfaces/          # 라우터, templates/, static/
│       └── main.py
├── tests/                       # src/ 구조를 그대로 미러링 (4장)
├── docs/
├── scripts/                       # 룰 검사 스크립트
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.sample
```

---

## 4. 테스트

### 4.1 tests/는 src/를 그대로 미러링한다

```
src/api/domain/entities/transaction.py
  → tests/api/domain/entities/test_transaction.py

src/api/application/use_cases/create_transaction.py
  → tests/api/application/use_cases/test_create_transaction.py
```

파일명은 `test_<원본 파일명>.py`. 폴더 경로는 `src/` 아래 경로와 **한 글자도 다르지 않게** 맞춘다.
테스트를 찾을 때 고민할 일이 없어야 하고, 대응되는 테스트가 없는 파일이 눈에 보여야 한다.

> `tests/` 하위 모든 폴더에 빈 `__init__.py`를 둔다. 없으면 서로 다른 폴더의 같은 이름
> 테스트 파일(`tests/api/.../test_transaction.py`와 `tests/agent/.../test_transaction.py`)에서
> pytest가 import file mismatch 에러를 낸다.

### 4.2 계층별 테스트 전략

| 계층 | 방식 | 외부 의존 |
|---|---|---|
| `domain` | 순수 단위 테스트. 목도 픽스처도 거의 없다 | 없음 |
| `application` | 포트를 가짜 구현(in-memory)으로 갈아끼운 단위 테스트 | 없음 |
| `infrastructure` | 실제 DB 컨테이너 대상 통합 테스트. `@pytest.mark.integration` | DB |
| `interfaces` | `TestClient`로 라우팅·검증·상태코드 | 없음 (유스케이스는 목) |

기본 실행(`pytest -m "not integration"`)은 컨테이너 없이 몇 초 안에 끝나야 한다.

### 4.3 테스트는 LLM을 호출하지 않는다

에이전트 테스트는 응답을 고정한 목으로 돌린다. 실제 모델 호출은 느리고, 비싸고,
매번 다른 답을 준다. 실제 호출이 필요한 확인은 테스트가 아니라 수동 스크립트로 둔다.

---

## 5. 코드 스타일

- 타입 힌트는 전부 붙인다. `mypy`가 CI에서 돈다.
- 금액은 정수 최소단위(원). `float` 금지. 값 객체 `Money`를 쓴다.
- 도메인 객체를 API 응답으로 그대로 내보내지 않는다. `interfaces/schemas`를 거친다.
- 예외는 계층에서 번역한다. `domain`의 `BudgetExceeded`가 `interfaces`에서 HTTP 409가 된다.
  `sqlalchemy` 예외가 라우터까지 올라오면 계층이 샌 것이다.
- 주석은 "무엇"이 아니라 "왜"를 적는다. 코드를 읽으면 아는 걸 반복하지 않는다.

---

## 6. 검사

규칙은 사람이 기억하는 게 아니라 두 지점에서 걸린다.

**1) feature를 finish하기 전** — 바뀐 파일을 AI 에이전트가 이 문서 기준으로 훑는다.
300줄처럼 기계적인 건 스크립트로 세고, "이 클래스가 이 계층에 있는 게 맞나" 같은 판단은
읽고 본다. 절차는 [git-flow-guide.md 3장](git-flow-guide.md#3-finish-전-점검--ai-에이전트가-한다).

```bash
git diff --name-only --diff-filter=d develop...HEAD   # 점검 대상
python3 scripts/check_file_length.py --base develop     # 300줄 상한
```

**2) CI** — 기계가 판정할 수 있는 것 전부.

```bash
ruff check src tests            # 린트 + import 정렬
ruff format --check src tests   # 포맷
mypy src                        # 타입
lint-imports                    # 계층·서비스 의존 규칙 (import-linter)
python3 scripts/check_file_length.py  # 300줄 상한 (전체)
pytest -m "not integration"     # 단위 테스트
```

`import-linter` 계약 예시 — 2.2와 2.3을 그대로 강제한다.

```ini
[importlinter:contract:api-layers]
name = api 계층은 안쪽으로만 의존한다
type = layers
layers =
    interfaces
    application
    domain
containers = api

[importlinter:contract:service-isolation]
name = 서비스끼리 import하지 않는다
type = independence
modules =
    api
    agent
    ui
```

---

## 7. 커밋·브랜치

git-flow(classic). `main`은 릴리스, `develop`이 기본, 기능은 `feature/*`.
브랜치를 따고 합치는 절차와 finish 전 점검은 [git-flow-guide.md](git-flow-guide.md)에 있다.

커밋 메시지는 `<type>: <한 줄 요약>` — `feat` / `fix` / `docs` / `refactor` / `test` / `chore`.
**왜 그렇게 했는지**는 본문에 적는다. 나중에 그 판단을 뒤집으려는 사람이 읽을 유일한 글이다.

---

## 8. 새 코드를 넣기 전 체크리스트

- [ ] 이 클래스는 어느 계층인가? 그 계층이 import해도 되는 것만 import하는가?
- [ ] 파일에 클래스가 하나인가? 파일명이 클래스명과 일치하는가?
- [ ] 300줄 아래인가? (100줄을 넘었다면 한 번 더 본다)
- [ ] `tests/`의 같은 경로에 테스트가 있는가?
- [ ] `domain`에 프레임워크가 들어오지 않았는가?
- [ ] 다른 서비스를 import하지 않았는가?

---

## 9. 룰을 어겨야 할 때

규칙이 코드를 나쁘게 만드는 순간이 온다. 그때는 어긴다. 대신 조용히 어기지 않는다.

1. PR 본문에 **어떤 규칙을, 왜** 어겼는지 적는다.
2. 코드에 `# rule-exception: <규칙> — <이유>` 주석을 남긴다.
3. 같은 예외가 세 번 나오면 예외가 아니라 **규칙이 틀린 것**이다. 이 문서를 고친다.
