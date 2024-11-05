FROM python:3.12

# Установка рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY . /app

# Создание статической папки
RUN mkdir -p /app/static

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Добавление задержки перед запуском
CMD ["sh", "-c", "sleep 3 && uvicorn app.main:app --host 0.0.0.0 --port 8001"]
