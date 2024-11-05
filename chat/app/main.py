from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import List
import json
import logging

from .db import get_db
from .websocket_manager import WebSocketManager, create_message
from .auth import get_current_user_from_token  # Импортируем функцию из auth.py

app = FastAPI()
manager = WebSocketManager()

logging.basicConfig(level=logging.INFO)


@app.websocket("/ws/{room_id}")
async def websocket_chat(
        websocket: WebSocket,
        room_id: int,
        token: str = Query(None),
        db: Session = Depends(get_db)
):
    if not token:
        logging.error("Токен отсутствует. Закрытие соединения.")
        await websocket.close(code=4001)
        return

    # Используем get_current_user_from_token для проверки токена без await
    try:
        user = get_current_user_from_token(token, db)  # Убираем await
    except HTTPException as e:
        logging.error(f"Ошибка проверки токена: {e.detail}")
        await websocket.close(code=4003)
        return

    room_name = f"chatroom_{room_id}"
    await manager.connect(room_name, websocket)
    logging.info(f"Пользователь {user.email} подключен к комнате {room_name}")

    try:
        await manager.broadcast(
            room_name,
            {"type": "notification", "message": f"{user.email} присоединился к чату."}
        )

        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            if data.get("type") == "message":
                data['user'] = user.email
                await manager.handle_message(room_id, data, db, user.id)
    except WebSocketDisconnect:
        logging.info(f"Пользователь {user.email} отключился от комнаты {room_name}")
        await manager.disconnect(room_name, websocket)
        await manager.broadcast(
            room_name,
            {"type": "notification", "message": f"{user.email} покинул чат."}
        )
    except Exception as e:
        logging.error(f"Неожиданная ошибка: {e}")
        try:
            await websocket.close(code=4002)
        except RuntimeError as close_error:
            logging.error(f"Ошибка при попытке закрытия WebSocket: {close_error}")
