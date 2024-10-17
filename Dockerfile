FROM python:3.12.7-slim-bookworm
RUN useradd -m appuser

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update && apt-get install -y curl==7.88.1-10+deb12u7 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry==1.8.4

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
COPY logscalescim /app/logscalescim

RUN poetry install --without dev && rm -rf $POETRY_CACHE_DIR

USER appuser
HEALTHCHECK --interval=5m --timeout=3s \
    CMD curl -f http://localhost/ServiceProviderConfig || exit 1
CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:5000", "logscalescim.app:app"]