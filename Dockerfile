FROM python:3.11-slim

WORKDIR /app

# Орта айнымалылары
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Тәуелділіктерді орнату
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Жоба файлдарын көшіру
COPY . .

# Ботты іске қосу
CMD ["python", "main.py"]
