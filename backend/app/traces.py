from typing import List, Optional

from sqlmodel import Session, select

from app.db import engine
from app.models import DecisionTrace, OptionEvaluationTrace


def list_decision_traces(limit: int = 50) -> List[DecisionTrace]:
    with Session(engine) as session:
        rows = session.exec(
            select(DecisionTrace).order_by(DecisionTrace.created_at.desc())
        ).all()
        return rows[:limit]


def get_decision_trace(run_id: str) -> Optional[DecisionTrace]:
    with Session(engine) as session:
        row = session.exec(
            select(DecisionTrace).where(DecisionTrace.run_id == run_id)
        ).first()
        return row


def get_option_evaluations(run_id: str) -> List[OptionEvaluationTrace]:
    with Session(engine) as session:
        rows = session.exec(
            select(OptionEvaluationTrace)
            .where(OptionEvaluationTrace.run_id == run_id)
            .order_by(OptionEvaluationTrace.rank.asc())
        ).all()
        return rows