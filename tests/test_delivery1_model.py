"""Tests de la Entrega 1: descarga y montaje del modelo Whisper (P6)."""

import os
import sys
from pathlib import Path


def _load_script(name: str):
    import importlib.util

    scripts = Path(__file__).resolve().parents[1] / "scripts"
    spec = importlib.util.spec_from_file_location(name, scripts / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_model_revision_is_pinned():
    download = _load_script("download_whisper")
    assert download.MODEL_ID == "Systran/faster-whisper-small"
    # Revisión fija reproducible (hash completo de 40 caracteres).
    assert len(download.MODEL_REVISION) == 40


def test_model_target_respects_env(monkeypatch):
    monkeypatch.setenv("WHISPER_MODEL_PATH", "/tmp/test-whisper")
    download = _load_script("download_whisper")
    assert download.TARGET == Path("/tmp/test-whisper")


def test_ensure_whisper_uses_same_target(monkeypatch):
    download = _load_script("download_whisper")
    ensure = _load_script("ensure_whisper")
    # ensure_whisper reutiliza el TARGET de download_whisper: misma ruta.
    assert ensure.TARGET == download.TARGET
    monkeypatch.setattr(ensure, "TARGET", Path("/nonexistent/whisper-small"))
    assert ensure.model_is_ready() is False


def test_dockerfile_and_compose_reference_model_path():
    root = Path(__file__).resolve().parents[1]
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    assert "WHISPER_MODEL_PATH" in compose
    assert "scripts/ensure_whisper.py" in dockerfile
