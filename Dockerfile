FROM python:3.11-slim

WORKDIR /app

# Системні утиліти для збирання
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Встановлення Python-залежностей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіювання коду застосунку
COPY . .

# Порт середовища Render / хостингу
ENV PORT=10000
EXPOSE 10000

# Запуск бота та веб-сервера
CMD ["python", "main.py"]
