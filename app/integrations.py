from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
import tempfile
from typing import Protocol

import httpx

from .models import Equipment, FilaParte, TabletResponse, VoiceNote


class PlantClient(Protocol):
    def download(self, path: str) -> bytes: ...


class LocalFilePlantClient:
    """Adaptador local para reemplazar al simulador HTTP durante las pruebas."""

    def __init__(self, files: dict[str, bytes] | None = None) -> None:
        self.files = files or {}

    def download(self, path: str) -> bytes:
        if path not in self.files:
            raise FileNotFoundError(f"Recurso no disponible: {path}")
        return self.files[path]


class Transcriber(Protocol):
    def transcribe(self, audio: bytes) -> str: ...


class FixtureTranscriber:
    def __init__(self, transcripts: dict[str, str] | None = None) -> None:
        self.transcripts = transcripts or {}

    def transcribe(self, audio: bytes) -> str:
        key = audio.decode("utf-8")
        if key not in self.transcripts:
            raise ValueError("No hay transcripción local para la nota")
        return self.transcripts[key]


class AmbiguousInputError(ValueError):
    def __init__(self, message: str, *, options: list[str], note: str | None = None) -> None:
        super().__init__(message)
        self.options = options
        self.note = note


class WhisperTranscriber:
    """Transcriptor local; no realiza llamadas de inferencia a servicios externos."""

    def __init__(self, model_path: str, *, device: str = "cpu", compute_type: str = "int8") -> None:
        if not model_path:
            raise ValueError("WHISPER_MODEL_PATH debe apuntar a un modelo local")
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo Whisper local inexistente: {self.model_path}")
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def transcribe(self, audio: bytes) -> str:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "Instalá el extra voice para transcribir notas localmente"
                ) from exc
            self._model = WhisperModel(
                str(self.model_path),
                device=self.device,
                compute_type=self.compute_type,
            )
        suffix = ".flac" if audio.startswith(b"fLaC") else ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix) as audio_file:
            audio_file.write(audio)
            audio_file.flush()
            segments, _ = self._model.transcribe(
                audio_file.name, language="es", vad_filter=True
            )
            return " ".join(segment.text.strip() for segment in segments).strip()


def download_media(base_url: str, path: str) -> bytes:
    if not path.startswith("/"):
        raise ValueError("La ruta de media debe ser absoluta dentro de la planta")
    response = httpx.get(f"{base_url.rstrip('/')}{path}", timeout=15)
    response.raise_for_status()
    return response.content


class VoicePartExtractor:
    """Extractor determinista de fixtures; el modelo local puede implementarlo."""

    _reading = re.compile(
        r"(?P<name>la dos|la tres|la uno|la bomba|la del medio|la del fondo|"
        r"la de la punta|la de reserva|el filtro [a-z])"
        r".*?(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>kg/?cm2|kilos?|psi|bar)?",
        re.IGNORECASE,
    )
    _word_reading = re.compile(
        r"(?P<name>la dos|la tres|la uno|la bomba|la del medio|la del fondo|"
        r"la de la punta|la de reserva|el filtro [a-z]).*?"
        r"(?P<value>(?:mil|seiscientos|quinientos|cuatrocientos|trescientos|"
        r"doscientos|ciento|cien|noventa|ochenta|setenta|sesenta|"
        r"cincuenta|cuarenta|treinta|veinte|dieciocho|dieciséis|dieciseis|"
        r"quince|catorce|trece|doce|once|diez|nueve|ocho|siete|seis|cinco|"
        r"cuatro|tres|dos|uno)(?:\s+(?:mil|ciento|cien|noventa|ochenta|"
        r"setenta|sesenta|cincuenta|cuarenta|treinta|veinte|dieciocho|"
        r"dieciséis|dieciseis|quince|catorce|trece|doce|once|diez|nueve|"
        r"ocho|siete|seis|cinco|cuatro|tres|dos|uno|con)){0,5})"
        r"\s*(?P<unit>kg/?cm2|kilos?|psi|bar)",
        re.IGNORECASE,
    )
    _numbers = {
        "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
        "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
        "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
        "dieciseis": 16, "dieciséis": 16, "dieciocho": 18, "veinte": 20,
        "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
        "setenta": 70, "ochenta": 80, "noventa": 90, "cien": 100,
        "ciento": 100, "doscientos": 200, "trescientos": 300,
        "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600,
        "mil": 1000,
    }

    _local_units = {"B-101": "kg/cm2", "B-102": "psi", "B-103": "bar"}

    def __init__(self, equipment: list[Equipment]) -> None:
        self.equipment = equipment

    def extract(self, note: VoiceNote, transcript: str) -> list[FilaParte]:
        rows: list[FilaParte] = []
        names = sorted(
            {
                alias
                for item in self.equipment
                for alias in (item.aliases + [item.name, item.tag])
            },
            key=len,
            reverse=True,
        )
        name_pattern = "|".join(re.escape(name) for name in names)
        reading = re.compile(
            rf"(?P<name>{name_pattern}).*?"
            r"(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>kg/?cm2|kgf/?cm2|kilos?|psi|bar)?",
            re.IGNORECASE,
        )
        word_reading = re.compile(
            rf"(?P<name>{name_pattern}).*?"
            rf"(?P<value>{self._word_value_pattern})\s*"
            r"(?P<unit>kg/?cm2|kgf/?cm2|kilos?|psi|bar)",
            re.IGNORECASE,
        )
        matches = list(reading.finditer(transcript))
        spans = {match.span() for match in matches}
        matches.extend(
            match for match in word_reading.finditer(transcript)
            if match.span() not in spans
        )
        for match in matches:
            equipment = self.resolve_equipment(match.group("name"))
            raw_value = match.group("value")
            if match.re is word_reading:
                prefix = transcript[match.end("name"):match.start("value")]
                prefix_words = [
                    word for word in re.findall(r"[a-záéíóú]+", prefix.casefold())
                    if word in self._numbers
                ]
                if prefix_words:
                    raw_value = " ".join((*prefix_words, raw_value))
            value = (
                float(raw_value.replace(",", "."))
                if re.fullmatch(r"\d+(?:[.,]\d+)?", raw_value)
                else self.parse_words(raw_value)
            )
            unit = self.normalize_unit(match.group("unit"))
            expected_unit = self._local_units.get(equipment.tag)
            if unit is None:
                unit = expected_unit
            elif expected_unit and unit != expected_unit:
                raise ValueError(
                    f"Unidad ambigua para {equipment.tag}: se esperaba {expected_unit}"
                )
            rows.append(
                FilaParte(
                    equipment_tag=equipment.tag,
                    variable="presion_descarga",
                    value=value,
                    unit=unit,
                    observed_at=note.observed_at,
                    observation=transcript,
                    photo_ids=note.photo_urls,
                )
            )
        return rows

    @property
    def _word_value_pattern(self) -> str:
        return (
            r"(?:mil|seiscientos|quinientos|cuatrocientos|trescientos|doscientos|"
            r"ciento|cien|noventa|ochenta|setenta|sesenta|cincuenta|cuarenta|"
            r"treinta|veinte|dieciocho|dieciséis|dieciseis|quince|catorce|"
            r"trece|doce|once|diez|nueve|ocho|siete|seis|cinco|cuatro|tres|"
            r"dos|uno)(?:\s+(?:mil|seiscientos|quinientos|cuatrocientos|"
            r"trescientos|doscientos|ciento|cien|noventa|ochenta|setenta|"
            r"sesenta|cincuenta|cuarenta|treinta|veinte|dieciocho|dieciséis|"
            r"dieciseis|quince|catorce|trece|doce|once|diez|nueve|ocho|siete|"
            r"seis|cinco|cuatro|tres|dos|uno|con)){0,5}"
        )

    @classmethod
    def parse_words(cls, value: str) -> float:
        tokens = value.casefold().replace(" con ", ".").split()
        if "." in tokens:
            integer = cls.parse_words(" ".join(tokens[:tokens.index(".")]))
            decimal = cls.parse_words(" ".join(tokens[tokens.index(".") + 1:]))
            return integer + decimal / (10 ** len(str(int(decimal))))
        total = 0
        for token in tokens:
            number = cls._numbers.get(token)
            if number is None:
                continue
            if number == 1000:
                total = max(total, 1) * 1000
            elif number == 100 and total:
                total = total * 100
            else:
                total += number
        return float(total)

    def resolve_equipment(self, informal_name: str) -> Equipment:
        normalized = informal_name.casefold()
        matches = [
            item
            for item in self.equipment
            if normalized == item.name.casefold()
            or normalized in {alias.casefold() for alias in item.aliases}
            or (normalized == "la de reserva" and item.reserve_available)
        ]
        if len(matches) != 1:
            raise AmbiguousInputError(
                f"Nombre de equipo ambiguo o inexistente: {informal_name}",
                options=[item.tag for item in matches],
                note=informal_name,
            )
        return matches[0]

    @staticmethod
    def normalize_unit(unit: str | None) -> str | None:
        if unit is None:
            return None
        normalized = unit.casefold()
        if normalized.startswith("kilo"):
            return "kg/cm2"
        if normalized.startswith("kgf"):
            return "kg/cm2"
        return normalized.replace("kg/cm2", "kg/cm2")


def apply_tablet_response(
    rows: list[FilaParte], response: TabletResponse
) -> list[FilaParte]:
    if not response.accepted and not response.corrections:
        raise ValueError("Una corrección rechazada debe incluir texto")
    if response.accepted:
        return rows
    # La corrección vuelve a la etapa de extracción; nunca confirma silenciosamente.
    return [
        row.model_copy(
            update={
                "requires_confirmation": True,
                "confirmation_reason": response.corrections,
            }
        )
        for row in rows
    ]


def merge_corrected_rows(
    rows: list[FilaParte], corrected: list[FilaParte]
) -> list[FilaParte]:
    """Replace only explicitly identified rows in a draft."""
    if not corrected:
        raise ValueError("No pude identificar la fila corregida")
    corrected_tags = [row.equipment_tag for row in corrected]
    if len(corrected_tags) != len(set(corrected_tags)):
        raise ValueError("La corrección identifica más de una lectura por equipo")
    result = list(rows)
    positions = {row.equipment_tag: index for index, row in enumerate(result)}
    for row in corrected:
        if row.equipment_tag not in positions:
            raise ValueError(f"La corrección refiere un equipo ausente: {row.equipment_tag}")
        result[positions[row.equipment_tag]] = row
    return result
