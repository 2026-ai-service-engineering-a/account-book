from __future__ import annotations

import logging

import httpx

from ui.application.errors import LedgerUnavailable, LedgerValidationError, TransactionNotFound

_log = logging.getLogger(__name__)
# 에러 봉투의 code → ui의 예외(docs/api-contract.md 5장). code로 가르고 message는 읽지 않는다.
_NOT_FOUND = "not_found"
_VALIDATION = "validation_error"


class ApiClient:
    """api를 HTTP로 부르는 얇은 층. 에러 봉투를 ui의 예외로 번역하는 곳이 여기 하나다.

    요청마다 클라이언트를 연다 — 수명 관리를 두지 않는다. 화면 한 장에 호출이 몇 번뿐이다.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 api를 끼운다
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._transport = transport

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
        json: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.request(
                    method, path, params=params, json=json, headers=headers
                )
        except httpx.HTTPError as error:
            raise LedgerUnavailable(type(error).__name__) from error
        if response.is_success:
            return response
        raise _translate(response)


def _translate(response: httpx.Response) -> Exception:
    try:
        parsed = response.json()
    except ValueError:
        parsed = None
    error = parsed.get("error") if isinstance(parsed, dict) else None
    if not isinstance(error, dict):
        error = {}
    code = error.get("code")
    if code == _NOT_FOUND:
        return TransactionNotFound()
    if code == _VALIDATION:
        details = error.get("details") or {}
        return LedgerValidationError({str(k): str(v) for k, v in details.items()})
    # 그 밖은 화면이 고칠 수 있는 게 아니다. 처리하는 곳이 여기라 한 번만 남긴다
    _log.warning("api error status=%d code=%s", response.status_code, code)
    return LedgerUnavailable(str(code or response.status_code))
