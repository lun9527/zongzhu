import os


# 兼容不同平台：优先使用平台注入的 PORT（如 Hugging Face Spaces），否则回退 8080
default_bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
bind = os.getenv('GUNICORN_BIND', default_bind)
workers = int(os.getenv('GUNICORN_WORKERS', '1'))
threads = int(os.getenv('GUNICORN_THREADS', '2'))
timeout = int(os.getenv('GUNICORN_TIMEOUT', '300'))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '5'))

accesslog = '-'
errorlog = '-'
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
