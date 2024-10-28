FROM python:3.13.0-slim-bookworm
RUN useradd -m appuser

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
# hadolint ignore=DL3015,DL3008
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry==1.8.4

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
COPY logscalescim /app/logscalescim

RUN poetry install --without dev && rm -rf $POETRY_CACHE_DIR

USER appuser
HEALTHCHECK --interval=5m --timeout=3s \
    CMD curl -f http://localhost/ServiceProviderConfig || exit 1
CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:8080", "logscalescim.app:app"]