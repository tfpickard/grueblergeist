# assistant/db.py
"""
Database module for Grüblergeist.
Handles PostgreSQL connection, SQLAlchemy models, and basic CRUD functions.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import get_config_value

logger = logging.getLogger(__name__)

Base = declarative_base()
engine = None
SessionLocal = None

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    role = Column(String)  # 'user', 'assistant', or 'system'
    text = Column(Text)
    tone = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id = Column(Integer, primary_key=True, index=True)
    preferred_tone = Column(String, nullable=True)
    preferred_style = Column(String, nullable=True)

def init_db() -> None:
    """
    Initialize the database connection and create tables if needed.
    """
    global engine, SessionLocal
    db_url = get_config_value("database_url")
    logger.info(f"Initializing DB with URL: {db_url}")
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

def get_session() -> Session:
    """
    Retrieve a new Session object from SessionLocal.

    :return: A Session object bound to the current engine.
    """
    global SessionLocal
    if SessionLocal is None:
        init_db()
    return SessionLocal()

def save_interaction(user_id: int, user_message: str, assistant_reply: str, tone_detected: Optional[str]) -> None:
    """
    Save a user-assistant interaction to the database.

    :param user_id: ID of the user.
    :param user_message: The text the user sent.
    :param assistant_reply: The text the assistant responded with.
    :param tone_detected: The tone detected in user message (if any).
    """
    session = get_session()
    try:
        session.add(Message(user_id=user_id, role='user', text=user_message, tone=tone_detected))
        session.add(Message(user_id=user_id, role='assistant', text=assistant_reply))
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving interaction: {e}")
    finally:
        session.close()

def get_conversation_history(user_id: int, limit: int = 10) -> List[Tuple[str, str]]:
    """
    Retrieve the last N messages from the conversation.

    :param user_id: ID of the user.
    :param limit: Number of messages to retrieve.
    :return: A list of (role, text) tuples.
    """
    session = get_session()
    try:
        messages = (
            session.query(Message)
            .filter(Message.user_id == user_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        messages.reverse()
        return [(m.role, m.text) for m in messages]
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        return []
    finally:
        session.close()

def get_user_profile(user_id: int) -> Optional[UserProfile]:
    """
    Retrieve the user profile from the database.

    :param user_id: ID of the user.
    :return: A UserProfile object if found, else None.
    """
    session = get_session()
    try:
        profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        return profile
    finally:
        session.close()

def update_user_profile(user_id: int, tone: Optional[str] = None, style: Optional[str] = None) -> None:
    """
    Update the user profile for the given user with new tone/style preferences.

    :param user_id: ID of the user.
    :param tone: The new preferred tone.
    :param style: The new preferred style.
    """
    session = get_session()
    try:
        profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id)
            session.add(profile)
        if tone is not None:
            profile.preferred_tone = tone
        if style is not None:
            profile.preferred_style = style
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating user profile: {e}")
    finally:
        session.close()

