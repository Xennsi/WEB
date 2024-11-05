from pydantic import BaseModel
from datetime import datetime

# Схема для создания пользователя
class UserCreate(BaseModel):
    email: str
    password: str

# Схема для создания комнаты чата
class ChatRoomCreate(BaseModel):
    name: str

# Схема для получения комнаты чата
class ChatRoom(ChatRoomCreate):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

# Схема для отображения сообщения (ответ от сервера)
class MessageResponse(BaseModel):
    id: int
    user_id: int
    chat_room_id: int
    content: str
    timestamp: datetime
    edited: bool = False
    deleted: bool = False
    last_edited_timestamp: datetime = None

    class Config:
        orm_mode = True

# Схема для создания сообщения
class MessageCreate(BaseModel):
    user_id: int
    chat_room_id: int
    content: str
