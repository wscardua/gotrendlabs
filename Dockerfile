FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system gotrendlabs \
    && adduser --system --ingroup gotrendlabs gotrendlabs \
    && mkdir -p /app/staticfiles /app/media /app/.runtime \
    && chown -R gotrendlabs:gotrendlabs /app

USER gotrendlabs
