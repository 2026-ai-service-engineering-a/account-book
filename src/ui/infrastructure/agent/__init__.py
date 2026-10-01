"""agent 서비스를 HTTP로 부르는 어댑터. LLM은 모른다 — 키도 프롬프트도 여기 없다."""

from .agent_capture_reader import AgentCaptureReader
from .agent_capture_reply import AgentCaptureReply

__all__ = ["AgentCaptureReader", "AgentCaptureReply"]
