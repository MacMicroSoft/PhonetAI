FROM python:3.12-slim as python-base

RUN apt-get update && apt-get install -y build-essential libpq-dev curl

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . /app/

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()", "--access-logfile", "-", "--error-logfile", "-"]