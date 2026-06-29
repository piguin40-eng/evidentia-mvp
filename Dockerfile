FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV EVIDENTIA_HOST=0.0.0.0
ENV EVIDENTIA_PORT=8892

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg curl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN mkdir -p /app/data/uploads /app/data/rag/chroma /app/data/exports /app/data/audit /app/data/derived

EXPOSE 8892

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8892/api/healthz || exit 1

CMD ["python", "server.py"]
