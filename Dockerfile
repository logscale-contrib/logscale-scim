FROM python:3.12.7-slim-bookworm

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock /app/
COPY logscalescim /app/logscalescim

RUN poetry install --without dev && rm -rf $POETRY_CACHE_DIR

CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:5000", "logscalescim.app:app"]