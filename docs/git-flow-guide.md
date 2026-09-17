# git flow 가이드

브랜치를 어떻게 따고 어떻게 합치는지, 그리고 **합치기 전에 무엇을 점검하는지**.

코드 규칙 자체는 [development-rules.md](development-rules.md)에 있다. 이 문서는 그 규칙을
**언제 누가 확인하느냐**를 다룬다.

---

## 1. 브랜치 구성

git-flow(classic)으로 초기화돼 있다. 설정은 `.git/config`의 `gitflow.*`에 들어 있다.

| 브랜치 | 어디서 따고 | 어디로 합치고 | 쓰임 |
|---|---|---|---|
| `main` | — | — | 릴리스. 태그가 붙는 지점 |
| `develop` | `main` | `main` | 기본 작업 브랜치. 모든 feature의 출발점 |
| `feature/*` | `develop` | `develop` | 기능 개발 |
| `bugfix/*` | `develop` | `develop` | 릴리스 전 버그 수정 |
| `release/*` | `develop` | `main` | 릴리스 준비. 끝나면 태그 |
| `hotfix/*` | `main` | `main` | 운영 긴급 수정. 끝나면 태그 |
| `support/*` | `main` | — | 구버전 유지 |

---

## 2. 일상 흐름

```bash
git flow feature start transaction-entity    # develop에서 딴다
# ... 작업, 커밋 ...
# ── 여기서 점검 (3장) ──
git flow feature finish transaction-entity   # develop으로 합치고 브랜치를 지운다
```

`finish`는 이름을 생략하면 현재 브랜치를 끝낸다. 리모트가 아직 없어도 그냥 된다.

---

## 3. finish 전 점검 — AI 에이전트가 한다

**`git flow feature finish`를 치기 전에 반드시 한 번 거친다.** 합쳐진 다음에 잡으면
`develop` 히스토리에 이미 들어간 뒤라 되돌리는 비용이 훨씬 크다.

### 3.1 왜 훅이 아니라 에이전트인가

git-flow 훅(`pre-flow-feature-finish`)으로 막을 수도 있지만 쓰지 않는다. 이유가 둘이다.

첫째, **훅은 조용히 안 도는 경우가 있다.** 훅 파일은 작업 트리에서 읽히기 때문에, 그 파일이
없는 브랜치에서 `finish`하면 아무 경고 없이 검사를 건너뛴다. 막아주는 줄 알았는데 안 막는
장치가 제일 나쁘다.

둘째, **규칙 대부분이 기계 판정 대상이 아니다.** 300줄 상한은 세면 되지만,
"이 클래스가 `domain`에 있는 게 맞나", "이 파일명이 내용과 맞나", "이 300줄은 책임이 둘인가
그냥 긴 건가"는 읽고 판단해야 한다. 그 판단을 에이전트가 한다.

기계적인 부분은 스크립트로 세고, 나머지는 에이전트가 읽는다.

### 3.2 에이전트에게 주는 지시

그대로 복사해서 쓴다.

```
feature/<이름>을 finish하기 전 점검해줘.

- 대상은 develop...HEAD로 바뀐 파일만.
- 기준은 docs/development-rules.md.
- 발견한 것마다 파일:줄 위치와 근거가 되는 규칙 번호를 붙여줘.
- 지금은 고치지 말고 목록만.
```

### 3.3 에이전트가 확인하는 것

변경 파일 목록은 여기서 나온다.

```bash
git diff --name-only --diff-filter=d develop...HEAD
```

| 확인 항목 | 방법 | 규칙 |
|---|---|---|
| 300줄 상한 | `python3 scripts/check_file_length.py --base develop` | 1.1 |
| 길어진 이유 | 250줄을 넘겼다면 책임이 둘인지 읽고 판단 | 1.1 |
| 한 파일 한 클래스 | 새 `.py`마다 최상위 `class` 정의가 하나인지 | 1.2 |
| 파일명 = 클래스명 | `Transaction` → `transaction.py` | 1.2 |
| 금지된 이름 | `utils` · `helpers` · `common` · `misc` | 1.3 |
| 계층 의존 | `domain`의 import가 표준 라이브러리뿐인지 | 2.2 |
| 서비스 격리 | `src/api` ↔ `src/agent` ↔ `src/ui` 상호 import | 2.3 |
| 테스트 미러 | 새 `src/` 파일마다 `tests/` 같은 경로에 테스트가 있는지 | 4.1 |
| 빈 계층 폴더 | 쓰지도 않을 폴더를 미리 만들지 않았는지 | 2.4 |

`scripts/check_file_length.py`는 의존성 없이 표준 라이브러리만 쓴다. 컨테이너가 떠 있지 않아도
돈다.

```
  주의  src/api/domain/entities/near.py  260줄 (상한 300)

파일 300줄 상한을 넘었습니다. (1개)

  초과  src/api/domain/entities/huge.py  350줄  (+50)
```

### 3.4 결과 처리

| 결과 | 할 일 |
|---|---|
| 걸린 게 없다 | `finish`한다 |
| 걸렸다 | **`finish`하지 않는다.** 고치고 커밋한 뒤 3.2부터 다시 |
| 고치면 더 나빠진다 | [development-rules.md 9장](development-rules.md#9-룰을-어겨야-할-때)의 예외 절차. 코드에 `# rule-exception:` 주석을 남긴다 |

점검 결과는 머지 커밋 메시지에 남긴다. 나중에 "이건 왜 통과됐지"에 답할 수 있다.

```bash
git flow feature finish transaction-entity -M "Merge feature/transaction-entity

룰 점검 통과. 변경 7개 파일, 최대 파일 길이 148줄.
domain/values/money.py는 Money 전용 Enum을 같이 둠 — 규칙 1.2 예외.
"
```

### 3.5 finish는 사람이 친다

점검은 에이전트가 하고, `finish` 명령은 사람이 친다. 브랜치를 합치고 지우는 건
되돌리기 번거로운 동작이라 마지막 한 번은 사람 손을 거친다.

---

## 4. release / hotfix

```bash
git flow release start 0.1.0     # develop에서 딴다
# 버전 표기, 변경 로그, 막판 수정만. 새 기능은 넣지 않는다
git flow release finish 0.1.0    # main에 합치고 태그, develop에도 되돌려 합친다

git flow hotfix start 0.1.1      # main에서 딴다 — 운영이 깨졌을 때만
git flow hotfix finish 0.1.1     # main에 합치고 태그, develop에도 반영
```

`release`와 `hotfix`도 3장 점검을 똑같이 거친다. 급할수록 더 거친다.

---

## 5. 자주 겪는 상황

**합치다 충돌났다**

```bash
# 충돌 해결하고 git add 한 뒤
git flow feature finish --continue
# 되돌리려면
git flow feature finish --abort
```

**브랜치를 남기고 싶다** — `finish`는 기본으로 브랜치를 지운다.

```bash
git flow feature finish <name> -k
```

**잘못 딴 브랜치를 버린다**

```bash
git flow feature delete <name>
```

**지금 어떤 브랜치들이 있나**

```bash
git flow feature list
git branch -vv
```

---

## 6. 하지 않는 것

- `main`·`develop`에 직접 커밋하지 않는다. 항상 `feature/*`를 거친다.
- `feature`에서 또 `feature`를 따지 않는다. 출발점은 언제나 `develop`이다.
- 점검 없이 `finish`하지 않는다.
- 한 `feature`에 관심사를 둘 담지 않는다. 브랜치 이름을 두 개 붙이고 싶어지면 갈라야 한다.
