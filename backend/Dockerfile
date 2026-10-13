# Backend (REST API) — Flask + PostgreSQL
FROM python:3.12-slim

WORKDIR /app

# Зависимости копируются отдельно от кода — слой кэшируется при пересборке
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

# gunicorn — продакшн-сервер WSGI для Flask
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "main:app"]
