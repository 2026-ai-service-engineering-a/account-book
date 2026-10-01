"""api 계약의 일부를 ui가 대신 연다. agent가 진짜 api를 부르듯 부른다.

api가 없는 동안만 있다. 진짜 api가 서면 agent의 `API_BASE_URL`을 바꾸고 이 패키지는 빠진다.
"""

from .candidate_body import CandidateBody
from .category_body import CategoryBody
from .embedding_body import EmbeddingBody
from .evidence_body import EvidenceBody
from .pending_body import PendingBody
from .pending_response import PendingResponse
from .suggest_request import SuggestRequest
from .suggest_response import SuggestResponse

__all__ = [
    "CandidateBody",
    "CategoryBody",
    "EmbeddingBody",
    "EvidenceBody",
    "PendingBody",
    "PendingResponse",
    "SuggestRequest",
    "SuggestResponse",
]
