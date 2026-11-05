"""Ensure the pinned Whisper model exists before starting the API."""

import os
import subprocess
import sys
from pathlib import Path

from download_whisper import MODEL_ID, MODEL_REVISION, main as download_model


def main() -> None:
    target = Path(os.getenv("WHISPER_MODEL_PATH", "/models/whisper-small"))
    if not (target / "model.bin").is_file():
        try:
            download_model()
        except Exception as exc:
            raise RuntimeError(
                f"No se pudo descargar {MODEL_ID}@{MODEL_REVISION} en {target}: {exc}"
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
            "8000",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
