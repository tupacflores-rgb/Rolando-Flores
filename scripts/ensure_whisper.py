"""Ensure the pinned Whisper model exists before starting the API."""

import os
import subprocess
import sys
from pathlib import Path

# Permite importar download_whisper aunque el cwd no sea scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from download_whisper import MODEL_ID, MODEL_REVISION, TARGET, main as download_model  # noqa: E402


def model_is_ready() -> bool:
    return (TARGET / "model.bin").is_file()


def main() -> None:
    if not model_is_ready():
        try:
            download_model()
        except Exception as exc:
            raise RuntimeError(
                f"No se pudo descargar {MODEL_ID}@{MODEL_REVISION} en {TARGET}: {exc}"
            ) from exc
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(os.getenv("PORT", "8000")),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
