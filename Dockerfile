FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=8080

WORKDIR /app

# 中文PDF输出需要字体
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads/jobs /app/outputs/jobs

EXPOSE 8080

CMD ["gunicorn", "-c", "gunicorn_conf.py", "wsgi:app"]
