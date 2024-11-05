import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime

from . import models

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List] = {}

    async def connect(self, room_name: str, websocket):
        await websocket.accept()
        if room_name not in self.active_connections:
            self.active_connections[room_name] = []
        self.active_connections[room_name].append(websocket)
        logging.info(f"Connection added to room {room_name}")

    async def disconnect(self, room_name: str, websocket):
        if room_name in self.active_connections:
            self.active_connections[room_name].remove(websocket)
            if not self.active_connections[room_name]:
                del self.active_connections[room_name]
        logging.info(f"Connection removed from room {room_name}")

    async def broadcast(self, room_name: str, message: dict):
        if room_name in self.active_connections:
            for connection in self.active_connections[room_name]:
                await connection.send_json(message)

    async def handle_message(self, chat_room_id: int, data: dict, db: Session, user_id: int):
        # Создаем новое сообщение
        new_message = {
            "user_id": user_id,
            "chat_room_id": chat_room_id,
            "content": data.get("content"),
            "timestamp": datetime.utcnow(),
            "edited": False,
            "deleted": False
        }

        # Сохраняем сообщение в базе данных
        db_message = models.Message(**new_message)
        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # Отправляем сообщение всем пользователям в комнате
        await self.broadcast(
            f"chatroom_{chat_room_id}",
            {
                "type": "message",
                "user": data['user'],
                "content": data.get("content"),
                "timestamp": db_message.timestamp.strftime("%Y-%m-%d %H:%M")
            }
        )

def create_message(content: str, user_id: int, chat_room_id: int):
    return {
        "user_id": user_id,
        "chat_room_id": chat_room_id,
        "content": content,
        "timestamp": datetime.utcnow(),
        "edited": False,
        "deleted": False
    }
