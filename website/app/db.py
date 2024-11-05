from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session  # Добавляем импорт Session
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эта функция будет использоваться в main.py, чтобы получить комнату из базы данных
def get_chat_room(room_id: int, db: Session):
    from .models import ChatRoom  # Импорт модели внутри функции для предотвращения циклического импорта
    return db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
