# ===== Multi-stage build для минимального размера образа =====

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY bot/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim

WORKDIR /app

# Создание пользователя для безопасности (не root)
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app/logs && \
    chown -R botuser:botuser /app

# Копирование установленных пакетов из builder
COPY --from=builder /root/.local /home/botuser/.local

# Копирование кода бота
COPY --chown=botuser:botuser bot/ /app/

# Переключение на непривилегированного пользователя
USER botuser

# Добавление .local/bin в PATH
ENV PATH=/home/botuser/.local/bin:$PATH

# Health check (опционально)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Запуск бота
CMD ["python", "main.py"]
