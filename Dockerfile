FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-root --no-interaction --no-ansi

COPY src ./src
COPY README.md ./README.md
COPY .env.example ./.env.example

EXPOSE 8000

CMD ["uvicorn", "api_test.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
