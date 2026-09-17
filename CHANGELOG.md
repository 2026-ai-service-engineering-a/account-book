# 변경 기록

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를,
버전은 [semver](https://semver.org)를 따른다. 맨 위가 최신이다.

쓰는 방법은 [docs/release.md](docs/release.md)에 있다.

## Unreleased

### 수정

- 릴리스 태그에 `v`가 붙지 않던 것. 설정 키가 틀렸다 — `gitflow.prefix.versiontag`는
  git-flow-avh의 것이고, 우리가 쓰는 git-flow-next는 `gitflow.branch.release.tagprefix`를
  읽는다. `docs/release.md`도 함께 고쳤다.

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
