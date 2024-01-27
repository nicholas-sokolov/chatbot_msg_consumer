FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev

RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.12-slim as runtime

WORKDIR /app

COPY --from=builder /app/wheels /wheels

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir /wheels/*

COPY . /app

ENV NAME MyApp

CMD ["/bin/bash"]
