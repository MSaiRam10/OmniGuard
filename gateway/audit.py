from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class AuditLogs(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    role = Column(String, nullable=True)
    tool = Column(String, nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    block_reason = Column(String, nullable=True)
    blocked = Column(Boolean, default=False, nullable=False)

Base.metadata.create_all(engine)

def log_event(user_id: str, role: str, tool: str, action: str, blocked: bool, block_reason: str = None):
    db = Session()
    try:
        audit_log = AuditLogs(
            user_id=user_id,
            role=role,
            tool=tool,
            action=action,
            blocked=blocked,
            block_reason=block_reason
        )
        db.add(audit_log)
        db.commit()
    finally:
        db.close()

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()