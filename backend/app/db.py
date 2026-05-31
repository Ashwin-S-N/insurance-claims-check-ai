from __future__ import annotations

import json

from sqlalchemy import DateTime, Float, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import get_settings
from app.models import DecisionResponse


class Base(DeclarativeBase):
    pass


class ClaimRecord(Base):
    __tablename__ = "claims"

    claim_id: Mapped[str] = mapped_column(String, primary_key=True)
    member_id: Mapped[str] = mapped_column(String, index=True)
    decision: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_amount: Mapped[float] = mapped_column(Float, default=0)
    response_json: Mapped[str] = mapped_column(Text)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())


engine = create_engine(get_settings().database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def save_response(member_id: str, response: DecisionResponse) -> None:
    with Session(SessionLocal().bind) as session:
        session.merge(
            ClaimRecord(
                claim_id=response.claim_id,
                member_id=member_id,
                decision=response.decision.value if response.decision else None,
                approved_amount=response.approved_amount,
                response_json=response.model_dump_json(),
            )
        )
        session.commit()


def list_claims() -> list[dict]:
    with Session(SessionLocal().bind) as session:
        rows = session.query(ClaimRecord).order_by(ClaimRecord.created_at.desc()).limit(50).all()
        return [json.loads(row.response_json) for row in rows]
