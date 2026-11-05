FROM contrato AS contrato_src

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
COPY app ./app
COPY --from=contrato_src / /tmp/planta-contrato
RUN pip install --no-cache-dir ".[integration,voice]" /tmp/planta-contrato
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
