FROM python:3.11.1-slim-buster as builder

ARG POETRY_VERSION=1.3.2

RUN python -m pip install --upgrade pip
RUN python -m pip install poetry==${POETRY_VERSION}
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN python -m venv /opt \
    && . /opt/bin/activate \
    && poetry install --no-root


FROM python:3.11.1-slim-buster as final

ENV PYTHONUNBUFFERED=1 \
    PATH=/opt/bin:$PATH \
    PYTHONPATH=/opt/lib/python3.10/site-packages:$PYTHONPATH

WORKDIR /app/

COPY --from=builder /opt /opt
COPY ./src/ /app/

EXPOSE 80
