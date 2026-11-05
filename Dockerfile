FROM python:3.11-slim
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
COPY app ./app
COPY scripts ./scripts
RUN pip install --no-cache-dir ".[integration,voice]" \
    "git+https://github.com/NovitSoftware/academia2026-tp.git@ab65b95e911731351dba395817a74a8cc60da2b2#subdirectory=contrato"
EXPOSE 8000
CMD ["python", "scripts/ensure_whisper.py"]
