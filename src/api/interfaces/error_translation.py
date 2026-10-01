"""예외를 HTTP로 번역한다(development-rules 6.5, api-contract 5장). 여기서만 한다."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.application.errors import IdempotencyKeyReused, RequestInProgress
from api.domain.errors import (
    ConfirmationRequired,
    InvalidEmbedding,
    InvalidTransaction,
    TransactionNotFound,
)

from .missing_idempotency_key import MissingIdempotencyKey
from .schemas import ErrorResponse

_log = logging.getLogger(__name__)


def install_error_translation(app: FastAPI) -> None:
    app.add_exception_handler(TransactionNotFound, _not_found)
    app.add_exception_handler(InvalidTransaction, _invalid)
    app.add_exception_handler(InvalidEmbedding, _invalid)
    app.add_exception_handler(RequestValidationError, _malformed)
    app.add_exception_handler(ConfirmationRequired, _confirmation)
    app.add_exception_handler(MissingIdempotencyKey, _missing_key)
    app.add_exception_handler(IdempotencyKeyReused, _reused)
    app.add_exception_handler(RequestInProgress, _in_progress)
    app.add_exception_handler(Exception, _internal)


async def _not_found(_: Request, __: Exception) -> JSONResponse:
    return ErrorResponse.reply(404, "not_found", "그 거래를 찾지 못했습니다.")


async def _invalid(_: Request, error: Exception) -> JSONResponse:
    details = error.details if isinstance(error, InvalidTransaction | InvalidEmbedding) else {}
    return ErrorResponse.reply(422, "validation_error", "입력을 확인해 주세요.", details)


async def _malformed(_: Request, error: Exception) -> JSONResponse:
    """요청 모양이 틀린 것도 validation_error다. 필드 이름 → 첫 번째 문구로 옮긴다."""
    details: dict[str, str] = {}
    if isinstance(error, RequestValidationError):
        for item in error.errors():
            field = str(item["loc"][-1]) if item.get("loc") else "body"
            details.setdefault(field, "값의 모양이 맞지 않습니다.")
    return ErrorResponse.reply(422, "validation_error", "입력을 확인해 주세요.", details)


async def _confirmation(_: Request, __: Exception) -> JSONResponse:
    message = "확인이 필요한 쓰기입니다. 사용자에게 확인을 받고 같은 키로 다시 보내 주세요."
    return ErrorResponse.reply(412, "confirmation_required", message)


async def _missing_key(_: Request, __: Exception) -> JSONResponse:
    return ErrorResponse.reply(
        400, "idempotency_key_required", "쓰기 요청에는 Idempotency-Key가 필요합니다."
    )


async def _reused(_: Request, __: Exception) -> JSONResponse:
    return ErrorResponse.reply(409, "idempotency_key_reused", "같은 키로 다른 요청이 왔습니다.")


async def _in_progress(_: Request, __: Exception) -> JSONResponse:
    return ErrorResponse.reply(409, "request_in_progress", "같은 요청을 아직 처리하고 있습니다.")


async def _internal(_: Request, error: Exception) -> JSONResponse:
    # 500에는 내부 정보를 담지 않는다. 스택은 로그에만 — 여기가 처리하는 곳이라 한 번만 남긴다
    _log.exception("unhandled %s", type(error).__name__)
    return ErrorResponse.reply(500, "internal_error", "문제가 생겼습니다.")
