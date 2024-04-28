FROM arm64v8/python:3.11.8-slim-bullseye

RUN pip install poetry

ARG TOKEN
ENV TOKEN=$TOKEN

RUN echo TOKEN

ARG SC_API_KEY
ENV SC_API_KEY=$SC_API_KEY

RUN echo SC_API_KEY

ARG FIREBASE_SECRET
ENV FIREBASE_SECRET=$FIREBASE_SECRET

RUN echo FIREBASE_SECRET

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cachez


RUN mkdir -p ./app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

COPY AstralAdmin ./app
RUN ls ./app

WORKDIR /app

ENTRYPOINT ["poetry", "run", "python", "main.py"]