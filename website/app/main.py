from fastapi import FastAPI, Depends, Request, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import logging
import os

# Импорт других модулей проекта
from . import crud, models, db, auth
from .config import ACCESS_TOKEN_EXPIRE_MINUTES
from .auth import create_access_token, verify_password, get_current_user
from .db import get_db

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание приложения FastAPI
app = FastAPI()

# Получаем базовую директорию
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Подключаем статические файлы и шаблоны
static_directory = os.path.join(BASE_DIR, "static")
template_directory = os.path.join(BASE_DIR, "templates")

# Проверяем наличие директорий и создаем их, если их нет
if not os.path.exists(static_directory):
    os.makedirs(static_directory)
if not os.path.exists(template_directory):
    os.makedirs(template_directory)

# Монтируем статические файлы и подключаем шаблоны
app.mount("/static", StaticFiles(directory=static_directory), name="static")
templates = Jinja2Templates(directory=template_directory)

# Создание всех таблиц при запуске приложения
@app.on_event("startup")
async def startup_event():
    try:
        models.Base.metadata.create_all(bind=db.engine)
        logger.info("Успешное подключение к базе данных и создание таблиц.")
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных и создании таблиц: {e}")

# Главная страница
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return RedirectResponse(url="/login/")

# Форма регистрации
@app.get("/register/", response_class=HTMLResponse)
def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Регистрация пользователя
@app.post("/register/")
def register_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user_in_db = crud.get_user_by_email(db, email=email)
        if user_in_db:
            logger.warning(f"Пользователь с email {email} уже существует.")
            return HTMLResponse(content="Пользователь с таким email уже существует.", status_code=400)

        user = crud.create_user(db=db, email=email, password=password)
        logger.info(f"Пользователь с email {email} успешно зарегистрирован.")
        return RedirectResponse(url="/login/", status_code=302)
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при регистрации пользователя.")

# Форма входа в систему
@app.get("/login/", response_class=HTMLResponse)
def show_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Вход пользователя и получение токена
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user:
        logger.warning(f"Пользователь с email {form_data.username} не найден.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Неверный пароль для пользователя: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    response = RedirectResponse(url="/chatrooms/", status_code=302)
    response.set_cookie(key="Authorization", value=f"Bearer {access_token}", httponly=True)

    logger.info(f"Пользователь {form_data.username} успешно вошел в систему.")
    return response

# Маршрут для получения всех комнат чата или поиска по названию
@app.get("/chatrooms/", response_class=HTMLResponse)
async def get_chatrooms(request: Request, search: str = Query("", description="Поиск по названию комнаты"),
                        db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Не удалось получить текущего пользователя.")

        chatrooms = crud.get_chatrooms(db, search=search) or []

        # Разделяем комнаты на мои и другие
        my_chatrooms = [chatroom for chatroom in chatrooms if chatroom.owner_id == current_user.id]
        other_chatrooms = [chatroom for chatroom in chatrooms if chatroom.owner_id != current_user.id]

        token = request.cookies.get("Authorization", "").replace("Bearer ", "")

        return templates.TemplateResponse("chatrooms.html", {
            "request": request,
            "my_chatrooms": my_chatrooms,
            "other_chatrooms": other_chatrooms,
            "search_query": search,
            "token": token
        })
    except Exception as e:
        logger.error(f"Ошибка при получении списка комнат: {str(e)}")
        return HTMLResponse(content="Ошибка при загрузке чатов.", status_code=500)

# Маршрут для создания комнаты чата
@app.post("/chatrooms/create", status_code=status.HTTP_201_CREATED)
async def create_chat_room(name: str = Form(...), db: Session = Depends(get_db),
                           current_user=Depends(get_current_user)):
    try:
        if not name.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Название комнаты не может быть пустым.")

        chat_room = crud.create_chatroom(db=db, name=name, owner_id=current_user.id)
        logger.info(f"Комната '{chat_room.name}' успешно создана с ID: {chat_room.id}")
        return JSONResponse(content={"detail": "Комната успешно создана", "chat_room_id": chat_room.id},
                            status_code=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Не удалось создать комнату: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Не удалось создать комнату: {str(e)}")

# Маршрут для удаления комнаты чата
@app.delete("/chatrooms/delete/{room_id}", status_code=status.HTTP_200_OK)
async def delete_chat_room(room_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        chat_room = crud.get_chatroom_by_id(db=db, room_id=room_id)
        if not chat_room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена")

        if chat_room.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет прав на удаление этой комнаты")

        crud.delete_chatroom(db=db, room_id=room_id)
        logger.info(f"Комната с ID {room_id} успешно удалена")
        return JSONResponse(content={"detail": "Комната успешно удалена"}, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Не удалось удалить комнату с ID {room_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось удалить комнату.")

# Маршрут для получения комнаты чата и сообщений
@app.get("/chatrooms/chat/{chat_room_id}", response_class=HTMLResponse)
async def get_chat_room(request: Request, chat_room_id: int, db: Session = Depends(get_db),
                        current_user=Depends(get_current_user)):
    try:
        chat_room = crud.get_chatroom_by_id(db, chat_room_id)
        if not chat_room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена")

        messages = crud.get_messages_by_chat_room(db, chat_room_id)

        token = request.cookies.get("Authorization", "").replace("Bearer ", "")

        logger.info(f"Пользователь {current_user.email} зашел в комнату {chat_room.name} с ID {chat_room_id}")

        return templates.TemplateResponse("chat.html", {
            "request": request,
            "chat_room": chat_room,
            "messages": messages,
            "user_token": token,
            "user": current_user
        })
    except Exception as e:
        logger.error(f"Ошибка при получении комнаты: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении комнаты.")

# Маршрут для поиска комнат по названию
@app.get("/chatrooms/search")
async def search_chatrooms(query: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        chatrooms = crud.get_chatrooms(db, search=query) or []

        return {"chatrooms": chatrooms}
    except Exception as e:
        logger.error(f"Ошибка при поиске комнат: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при поиске комнат.")
