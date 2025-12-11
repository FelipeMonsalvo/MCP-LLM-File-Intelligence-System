"""
Database functions for chat sessions and conversations
"""
from sqlalchemy.orm import Session
from .database import ChatSession, Conversation
from datetime import datetime
import uuid

def get_or_create_chat_session(db: Session, user_id: int, session_id: str = None) -> ChatSession:
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id, ChatSession.user_id == user_id).first()

        if session:
            return session
    
    new_session_id = session_id or str(uuid.uuid4())
    chat_session = ChatSession(session_id=new_session_id, user_id=user_id)

    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    return chat_session


def get_conversation_history(db: Session, session_id: str, user_id: int) -> list:
    chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id, ChatSession.user_id == user_id).first()
    
    if not chat_session:
        return []
    
    messages = db.query(Conversation).filter(Conversation.session_id == chat_session.id).order_by(Conversation.created_at).all()
    
    result = []

    for msg in messages:
        result.append({"role": msg.role, "content": msg.content})
    
    return result


def save_message(db: Session, session_id: str, user_id: int, role: str, content: str):
    chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id, ChatSession.user_id == user_id).first()
    
    if not chat_session:
        chat_session = get_or_create_chat_session(db, user_id, session_id)
    
    message = Conversation(session_id=chat_session.id, user_id=user_id, role=role, content=content)

    db.add(message)
    chat_session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    return message


def get_user_sessions(db: Session, user_id: int) -> list:
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()
    
    return [
        {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
        for session in sessions
    ]


def delete_chat_session(db: Session, session_id: str, user_id: int) -> bool:
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id, ChatSession.user_id == user_id).first()
    
    if not session:
        return False
    
    db.delete(session)
    db.commit()
    return True


def delete_all_user_sessions(db: Session, user_id: int) -> int:
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
    count = len(sessions)

    for session in sessions:
        db.delete(session)
    
    db.commit()
    return count