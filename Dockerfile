FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# 复制代码
COPY ai_engine/ ./ai_engine/
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY tests/ ./tests/
COPY conftest.py ./

# 环境变量
ENV PYTHONPATH=/app:/app/backend
ENV PORT=8080

EXPOSE 8080

CMD ["python", "-m", "backend.main"]
