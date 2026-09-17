# 목 UI

화면 설계를 눈으로 보는 물건이다. **서버가 없다.** 정적 HTML 여섯 장이고,
데이터는 전부 손으로 써넣은 가짜이며, 버튼은 아무것도 하지 않는다.

```bash
make mock      # http://localhost:8080
```

개발 컨테이너 안에서 `python3 -m http.server`로 뜬다. 새 의존성은 없다.

## 무엇이 아닌가

- `src/ui`가 아니다. 진짜 `ui` 서버는 FastAPI + Jinja2 + HTMX로 따로 만든다
  ([../README.md](../README.md) 3장).
- `api`·`agent`를 부르지 않는다. 네트워크 호출이 하나도 없다.
- 개발 룰의 적용 대상이 아니다. 계층도 테스트도 없다. 버려질 수 있는 코드다.

## 왜 만드나

문서로만 있는 화면은 합의된 것처럼 보이기 쉽다. 실제로 그려 보면 그제야
"이 줄은 어디에 놓이나", "빈 화면은 뭐라고 말하나" 같은 것이 드러난다.
[../ui_docs/](../ui_docs/)의 판단들이 화면에서 말이 되는지 확인하는 용도다.

## 화면

| 파일 | 설계 문서 | 확인하려는 것 |
|---|---|---|
| `index.html` | [chat.md](../ui_docs/pages/chat.md) | 확인 카드, 진행 줄, 첫 방문 예시 |
| `transactions.html` | [transactions.md](../ui_docs/pages/transactions.md) | 부호 표기, 출처 표시, 지출·수입 분리 합계 |
| `transactions-empty.html` | [transactions.md](../ui_docs/pages/transactions.md) | 빈 화면 두 종류의 문구 차이 |
| `transaction-form.html` | [transaction-form.md](../ui_docs/pages/transaction-form.md) | 방향 먼저, 필드 옆 검증, 삭제 확인 문구 |
| `reports.html` | [reports.md](../ui_docs/pages/reports.md) | 증가만 강조, 첫 달 열 숨김, 대화로 넘기기 |
| `budgets.html` | [budgets.md](../ui_docs/pages/budgets.md) | 막대+숫자 병기, 초과 표시, 줄 단위 편집 |

## 고칠 때

설계를 바꾸면 `ui_docs/`를 먼저 고치고 여기를 맞춘다. 반대로 하면
그림만 남고 이유가 사라진다.
