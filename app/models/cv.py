from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base_class import Base


class CV(Base):
    __tablename__ = "cvs"

    cv_id = Column(Integer, primary_key=True, index=True)
    user_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_key = Column(Text, nullable=False)
    file_url = Column(Text, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
