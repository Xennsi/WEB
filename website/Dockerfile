FROM python:3.12

# Установка рабочей директории
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app/templates /app/templates

COPY . /app

EXPOSE 8000
# Добавление задержки перед запуском
CMD ["sh", "-c", "sleep 3 && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
