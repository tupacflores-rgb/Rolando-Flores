"""Download the approved local Whisper model at a reproducible revision."""

from pathlib import Path
import os

from huggingface_hub import snapshot_download


MODEL_ID = "Systran/faster-whisper-small"
MODEL_REVISION = "536b0662742c02347bc0e980a01041f333bce120"
TARGET = Path(
    os.getenv(
        "WHISPER_MODEL_PATH",
        str(Path(__file__).resolve().parents[1] / "models" / "whisper-small"),
    )
)


def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=TARGET,
        allow_patterns=[
            "config.json",
            "model.bin",
            "tokenizer.json",
            "vocabulary.*",
            "preprocessor_config.json",
            "README.md",
        ],
    )
    print(f"Modelo descargado en {TARGET}")


if __name__ == "__main__":
    main()
