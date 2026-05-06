FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml* uv.lock* requirements.txt* ./

RUN if [ -f pyproject.toml ]; then \
        uv sync --frozen; \
    elif [ -f requirements.txt ]; then \
        uv pip install -r requirements.txt; \
    fi


COPY pyproject.toml* uv.lock* requirements.txt* ./
COPY . .

EXPOSE 8000
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
