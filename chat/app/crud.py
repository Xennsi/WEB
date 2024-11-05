from sqlalchemy.orm import Session
from . import models
from passlib.context import CryptContext
from datetime import datetime

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция для хэширования пароля
def hash_password(password: str) -> str:
    """Хэширует пароль с использованием bcrypt."""
    return pwd_context.hash(password)

# Создание нового пользователя
def create_user(db: Session, email: str, password: str) -> models.User:
    """Создает пользователя и добавляет его в базу данных."""
    hashed_password = hash_password(password)
    user = models.User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Получение пользователя по email
def get_user_by_email(db: Session, email: str) -> models.User:
    """Возвращает пользователя по email, если он существует в базе данных."""
    return db.query(models.User).filter(models.User.email == email).first()

# Создание новой чат-комнаты
def create_chatroom(db: Session, name: str, owner_id: int) -> models.ChatRoom:
    """Создает чат-комнату и добавляет ее в базу данных."""
    chatroom = models.ChatRoom(name=name, owner_id=owner_id)
    db.add(chatroom)
    db.commit()
    db.refresh(chatroom)
    return chatroom

# Получение списка всех комнат, соответствующих поисковому запросу
def get_chatrooms(db: Session, search: str) -> list[models.ChatRoom]:
    """Возвращает список всех комнат, содержащих строку поиска в названии."""
    return db.query(models.ChatRoom).filter(models.ChatRoom.name.contains(search)).all()

# Получение комнаты по ID
def get_chatroom_by_id(db: Session, room_id: int) -> models.ChatRoom:
    """Возвращает комнату по ее ID, если она существует в базе данных."""
    return db.query(models.ChatRoom).filter(models.ChatRoom.id == room_id).first()

# Создание нового сообщения
def create_message(db: Session, user_id: int, chat_room_id: int, content: str) -> models.Message:
    """Создает новое сообщение в указанной чат-комнате."""
    db_message = models.Message(user_id=user_id, chat_room_id=chat_room_id, content=content, timestamp=datetime.utcnow())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# Получение всех сообщений для комнаты чата
def get_messages_by_chat_room(db: Session, chat_room_id: int) -> list[models.Message]:
    """Возвращает список всех сообщений для указанной комнаты чата."""
    return db.query(models.Message).filter(models.Message.chat_room_id == chat_room_id).order_by(models.Message.timestamp).all()

# Удаление комнаты чата
def delete_chatroom(db: Session, room_id: int):
    """Удаляет комнату чата по ID, если она существует в базе данных."""
    chatroom = db.query(models.ChatRoom).filter(models.ChatRoom.id == room_id).first()
    if not chatroom:
        raise ValueError("Комната не найдена")
    db.delete(chatroom)
    db.commit()
