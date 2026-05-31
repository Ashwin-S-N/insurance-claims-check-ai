from typing import Any

from app.models import TraceEvent


class TraceBuilder:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def add(self, step: str, status: str, message: str, **data: Any) -> None:
        self.events.append(TraceEvent(step=step, status=status, message=message, data=data))

    def list(self) -> list[TraceEvent]:
        return self.events
