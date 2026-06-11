from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings
from src.models.task import Base


class DatabaseManager:
    def __init__(self, database_url: str | None = None):
        self.engine = create_engine(
            database_url or settings.database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        self._session_factory = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        return self._session_factory()

    def log_task(
        self,
        task_type: str,
        input_text: str,
        session_id: str,
        agent_used: str | None = None,
        status: str = "pending",
        result_text: str | None = None,
        confidence: float | None = None,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ):
        from src.models.task import TaskLog
        from datetime import datetime, timezone

        with self.get_session() as session:
            log = TaskLog(
                session_id=session_id,
                task_type=task_type,
                input_text=input_text,
                agent_used=agent_used,
                status=status,
                result_text=result_text,
                confidence=confidence,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                completed_at=datetime.now(timezone.utc) if status == "completed" else None,
            )
            session.add(log)
            session.commit()
            return log.id
