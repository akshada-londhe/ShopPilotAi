import json
from dataclasses import dataclass
from typing import Any, Literal

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.models.query import ClarificationContext


class SearchRequest(BaseModel):
    query: str
    clarification_context: ClarificationContext | None = None


class SaveItemRequest(BaseModel):
    name: str
    price: float | None = None
    image: str | None = None
    merchant: str | None = None
    link: str | None = None


class UnsaveItemRequest(BaseModel):
    name: str
    link: str | None = None


SSEEventType = Literal[
    "progress",
    "needs_clarification",
    "result",
    "error",
]


@dataclass
class SSEEvent:
    event: SSEEventType
    payload: dict[str, Any]

    def to_sse_line(self) -> str:
        """Format event as the spec's SSE wire format."""
        body = json.dumps(
            {
                "event": self.event,
                "payload": jsonable_encoder(self.payload),
            }
        )
        return f"data: {body}\n\n"
