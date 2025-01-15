FROM python:3.12-slim as python-base

RUN apt-get update && apt-get install -y build-essential libpq-dev curl

ENV POETRY_VERSION=1.6.0
ENV POETRY_HOME=/opt/poetry
ENV PATH="${PATH}:${POETRY_HOME}/bin"

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-interaction --no-cache

COPY . /app/

EXPOSE 5000

CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()", "--access-logfile", "-", "--error-logfile", "-"]