from __future__ import annotations

import re
import unicodedata
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


# --------------------------------------------------------------------------- normalización de texto

def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.casefold())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    # Superíndices y símbolos comunes en unidades dictadas.
    return (
        normalized.replace("²", "2")
        .replace("³", "3")
        .replace("°", "")
        .replace("\u00ba", "")
    )


# --------------------------------------------------------------------------- números en palabras

_NUMBER_TOKENS = {
    "cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciseis": 16, "dieciséis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    "veinte": 20, "veintiuno": 21, "veintiun": 21, "veintiún": 21, "veintidos": 22,
    "veintidós": 22, "veintitres": 23, "veintitrés": 23, "veinticuatro": 24,
    "veinticinco": 25, "veintiseis": 26, "veintiséis": 26, "veintisiete": 27,
    "veintiocho": 28, "veintinueve": 29,
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70,
    "ochenta": 80, "noventa": 90,
    "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300,
    "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600, "setecientos": 700,
    "ochocientos": 800, "novecientos": 900, "mil": 1000,
}

_DIGITS = {k: v for k, v in _NUMBER_TOKENS.items() if v < 10}
_TEENS = {
    "once", "doce", "trece", "catorce", "quince", "dieciseis", "dieciséis",
    "diecisiete", "dieciocho", "diecinueve",
}

_NUM_WORD = "|".join(sorted(_NUMBER_TOKENS, key=len, reverse=True))
_NUM_VALUE = rf"(?:\d+(?:[.,]\d+)?|(?:{_NUM_WORD})(?:\s+(?:{_NUM_WORD}|y|con|coma|punto)){{0,6}})"


# --------------------------------------------------------------------------- unidades

_PRESSURE_UNIT = r"(?:kilos|kilogramos|kilo|kg/?cm2|kgf/?cm2|kg|psi|libras?|lb|bar|bares)"


def normalize_unit(unit: str | None) -> str | None:
    """Normaliza la unidad dictada en campo a la unidad canónica del contrato."""
    if unit is None:
        return None
    normalized = _strip_accents(unit).strip().casefold()
    if normalized in {"kilo", "kilos", "kilogramos", "kilogramo", "kg", "kg/cm2", "kgcm2", "kgf/cm2", "kgfcm2"}:
        return "kg/cm2"
    if normalized in {"psi", "libras", "libra", "lb"}:
        return "psi"
    if normalized in {"bar", "bares"}:
        return "bar"
    if normalized in {"m", "metro", "metros"}:
        return "m"
    if normalized in {"grados", "c", "degc", "deg c"}:
        return "degC"
    if normalized in {"mm/s", "mms"}:
        return "mm/s"
    if normalized in {"gotas/min", "gotasmin"}:
        return "gotas/min"
    return normalized.replace("cm2", "cm2")


# --------------------------------------------------------------------------- extractor determinista


class VoicePartExtractor:
    """Extrae filas estructuradas de una transcripción, una por equipo y variable.

    Es determinista: no usa el índice de voces ni un LLM. Las ambigüedades (equipo
    genérico o un diferencial dicho ``dieciocho`` en lugar de ``uno ocho``) se
    reportan con :class:`AmbiguousInputError` para que el flujo pregunte.
    """

    _NORMAL_OBSERVATIONS = {"parada, en reserva", "parada por mantenimiento"}

    def __init__(self, equipment: list[Equipment]) -> None:
        self.equipment = equipment
        # Entradas (alias original, fragmento de regex flexible en género, equipo).
        self._entries: list[tuple[str, str, Equipment]] = []
        for item in equipment:
            for alias in item.aliases + [item.name, item.tag]:
                if not alias:
                    continue
                stripped = _strip_accents(alias).strip()
                self._entries.append((alias, self._fragment(stripped), item))
        self._entries.sort(key=lambda entry: len(entry[0]), reverse=True)

    @staticmethod
    def _fragment(alias_stripped: str) -> str:
        """Fragmento de regex que tolera el artículo el/la/los/las al inicio."""
        match = re.match(r"^(el|la|los|las|lo)\s+(.+)$", alias_stripped, re.IGNORECASE)
        if match:
            return r"(?:el|la|los|las|lo)\s+" + re.escape(match.group(2))
        return re.escape(alias_stripped)

    @staticmethod
    def _strip_article(name: str) -> str:
        return re.sub(r"^(?:el|la|los|las|lo)\s+", "", name.strip(), flags=re.IGNORECASE).strip()

    # -- helpers de parsing ---------------------------------------------------

    @classmethod
    def parse_words(cls, value: str) -> float:
        tokens = [
            token
            for token in re.findall(r"[a-záéíóúñü]+|\d+", _strip_accents(value))
            if token != "y"
        ]
        if not tokens:
            raise ValueError(f"Valor numérico irreconocible: {value!r}")
        return cls._parse_tokens(tokens)

    @classmethod
    def _parse_tokens(cls, tokens: list[str]) -> float:
        # "uno y medio" -> 1.5
        if "medio" in tokens:
            index = tokens.index("medio")
            return float(cls._parse_integer(tokens[:index])) + 0.5
        # Separador decimal explícito: "uno coma ocho", "uno con tres".
        for sep in ("coma", "con", "punto"):
            if sep in tokens:
                index = tokens.index(sep)
                integer = cls._parse_integer(tokens[:index])
                fraction = cls._parse_integer(tokens[index + 1:])
                digits = len(str(int(fraction)))
                return float(integer) + fraction / (10 ** digits)
        # Par de dígitos sin separador: "uno ocho" -> 1.8, "cero nueve" -> 0.9.
        if len(tokens) == 2 and all(token in _DIGITS for token in tokens):
            return float(_DIGITS[tokens[0]]) + float(_DIGITS[tokens[1]]) / 10.0
        return float(cls._parse_integer(tokens))

    @classmethod
    def _parse_integer(cls, tokens: list[str]) -> int:
        total = 0
        current = 0
        for token in tokens:
            if token not in _NUMBER_TOKENS:
                continue
            number = _NUMBER_TOKENS[token]
            if token == "mil":
                total += (current or 1) * 1000
                current = 0
            elif token in ("cien", "ciento") or number in (200, 300, 400, 500, 600, 700, 800, 900):
                current += number
            else:
                current += number
        return total + current

    def parse_value(self, raw: str) -> float | None:
        raw = (raw or "").strip()
        if not raw:
            return None
        if re.fullmatch(r"\d+(?:[.,]\d+)?", raw):
            return float(raw.replace(",", "."))
        return self.parse_words(raw)

    @classmethod
    def _is_teens_word(cls, raw: str) -> bool:
        tokens = re.findall(r"[a-záéíóúñü]+", _strip_accents(raw))
        return bool(tokens) and all(token in _TEENS for token in tokens)

    @classmethod
    def normalize_unit(cls, unit: str | None) -> str | None:
        return normalize_unit(unit)

    # -- resolución de equipo -------------------------------------------------

    def resolve_equipment(self, informal_name: str) -> Equipment:
        normalized = self._strip_article(_strip_accents(informal_name))
        matches = [
            item
            for item in self.equipment
            if normalized == self._strip_article(_strip_accents(item.name))
            or normalized in {self._strip_article(_strip_accents(alias)) for alias in item.aliases}
        ]
        if len(matches) != 1:
            raise AmbiguousInputError(
                f"Nombre de equipo ambiguo o inexistente: {informal_name}",
                options=sorted(item.tag for item in matches),
                note=informal_name,
            )
        return matches[0]

    def _find_lead(self, segment: str) -> Equipment | None:
        """Resuelve el equipo de un segmento; reporta ambigüedad si el nombre coincide con varios."""
        matches: dict[str, set[str]] = {}
        for alias, fragment, item in self._entries:
            if re.search(rf"\b{fragment}\b", segment, re.IGNORECASE):
                matches.setdefault(alias, set()).add(item.tag)
        if matches:
            best_alias = max(matches, key=len)
            tags = matches[best_alias]
            if len(tags) != 1:
                raise AmbiguousInputError(
                    f"Nombre de equipo ambiguo: {best_alias}",
                    options=sorted(tags),
                    note=best_alias,
                )
            tag = next(iter(tags))
            return next(item for item in self.equipment if item.tag == tag)
        if re.search(r"\b(?:la\s+bomba|bomba)\b", segment, re.IGNORECASE):
            pumps = [item for item in self.equipment if item.kind == "bomba"]
            if len(pumps) > 1:
                raise AmbiguousInputError(
                    "No distingo qué bomba es; elegí una.",
                    options=sorted(item.tag for item in pumps),
                    note="la bomba",
                )
            if pumps:
                return pumps[0]
        return None

    # -- extracción -----------------------------------------------------------

    def extract(self, note: VoiceNote, transcript: str) -> list[FilaParte]:
        normalized = _strip_accents(transcript)
        rows: list[tuple[int, FilaParte]] = []
        for segment in self._segments(normalized):
            self._parse_segment(note, segment, rows)
        return [row for _, row in sorted(rows, key=lambda pair: pair[0])]

    def _segments(self, normalized: str) -> list[str]:
        name_pattern = "|".join(fragment for _, fragment, _ in self._entries)
        split = re.compile(
            rf"[.!?;]\s+|\s*(?:,\s*)?(?:ah\s*,\s*)?(?:y|tambien|ademas|despues)\s+(?=(?:{name_pattern})\b)",
            re.IGNORECASE,
        )
        segments: list[str] = []
        for piece in split.split(normalized):
            piece = self._strip_fillers(piece.strip())
            if piece:
                segments.append(piece)
        return segments

    @staticmethod
    def _strip_fillers(text: str) -> str:
        result = text
        while True:
            match = re.match(
                r"^(?:bueno|eh|a\s+ver|listo|este|bien|ah|despues|tambien|ademas|y)\b[\s,]*",
                result,
                re.IGNORECASE,
            )
            if not match:
                break
            result = result[match.end():]
        return result.strip()

    def _parse_segment(self, note: VoiceNote, segment: str, rows: list[tuple[int, FilaParte]]) -> None:
        lead = self._find_lead(segment)
        if lead is None:
            return

        def add(position: int, variable: str, value: float | None, unit: str | None,
                observation: str | None) -> None:
            rows.append(
                (
                    position,
                    FilaParte(
                        equipment_tag=lead.tag,
                        variable=variable,
                        value=value,
                        unit=unit,
                        observed_at=note.observed_at,
                        observation=observation,
                        photo_ids=list(note.photo_urls),
                    ),
                )
            )

        # Estado: "está parada, en reserva" / "parada por mantenimiento" / "disparada, no arranca".
        for match in re.finditer(
            r"\besta\s+(parada\s*,?\s*en\s*reserva|parada\s*por\s*mantenimiento|disparada\s*,?\s*no\s*arranca)\b",
            segment,
            re.IGNORECASE,
        ):
            estado = re.sub(r"\s+", " ", match.group(1)).strip().replace(" ,", ",")
            add(match.start(), "estado", None, None, estado)

        # Nivel del tanque: "está en cinco coma dos metros".
        for match in re.finditer(
            rf"\besta(?:ba)?\s+en\s+(?P<value>{_NUM_VALUE})\s+(?:metros?|m)\b",
            segment,
            re.IGNORECASE,
        ):
            value = self.parse_value(match.group("value"))
            if value is None:
                continue
            observation = "rebalse a pileta" if re.search(r"\brebals", segment) else None
            add(match.start(), "nivel", value, "m", observation)

        # Presión de descarga local: "está en 112 kilos (de descarga)".
        for match in re.finditer(
            rf"\besta(?:ba)?\s+en\s+(?P<value>{_NUM_VALUE})\s*"
            rf"(?:(?P<unit>{_PRESSURE_UNIT})(?:\s+de\s+descarga)?|de\s+descarga)\b",
            segment,
            re.IGNORECASE,
        ):
            value = self.parse_value(match.group("value"))
            if value is None:
                continue
            unit = self.normalize_unit(match.group("unit"))
            if unit is None:
                unit = lead.local_gauge_unit or "kg/cm2"
            add(match.start(), "presion_descarga_local", value, unit, None)

        # Presión diferencial de filtro: "me dio uno ocho de diferencial" / "está en uno coma cinco de diferencial".
        for match in re.finditer(
            rf"\b(?:me\s+dio|esta(?:ba)?\s+en)\s+(?P<value>{_NUM_VALUE})\s+(?:de\s+)?diferencial\b",
            segment,
            re.IGNORECASE,
        ):
            value = self.parse_value(match.group("value"))
            if value is None:
                continue
            if self._is_teens_word(match.group("value")):
                raise AmbiguousInputError(
                    "El diferencial dicho en decenas es ambiguo; ¿fue 'uno X' o el número entero?",
                    options=[str(value), f"1.{int(value % 10)}"],
                    note=match.group("value"),
                )
            observation = "diferencial alto" if value >= 1.5 else None
            add(match.start(), "presion_diferencial", value, "kg/cm2", observation)

        # Temperatura de rodamiento por IR: "el rodamiento me dio 52 grados con la pistola".
        for match in re.finditer(
            rf"\brodamiento\s+(?:me\s+)?dio\s+(?P<value>{_NUM_VALUE})\s+(?:grados?|c)\b",
            segment,
            re.IGNORECASE,
        ):
            value = self.parse_value(match.group("value"))
            if value is None:
                continue
            observation = "rodamiento caliente" if value > 75 else None
            add(match.start(), "temperatura_rodamiento_ir", value, "degC", observation)

        # Temperatura de aceite: "ochenta grados de aceite".
        for match in re.finditer(
            rf"\b(?P<value>{_NUM_VALUE})\s+(?:grados?|c)\s+de\s+aceite\b",
            segment,
            re.IGNORECASE,
        ):
            value = self.parse_value(match.group("value"))
            if value is None:
                continue
            add(match.start(), "temperatura_aceite", value, "degC", None)

        # Presión de succión: "cero coma nueve de succión".
        for match in re.finditer(
            rf"\b(?P<value>{_NUM_VALUE})\s+(?:de\s+)?succion\b",
            segment,
            re.IGNORECASE,
        ):
            value = self.parse_value(match.group("value"))
            if value is None:
                continue
            add(match.start(), "presion_succion", value, "kg/cm2", None)

        # Vibración: "vibración de siete coma dos (mm/s)".
        for match in re.finditer(
            rf"\bvibracion\s+(?:es\s+)?(?:de\s+)?(?P<value>{_NUM_VALUE})\b",
            segment,
            re.IGNORECASE,
        ):
            value = self.parse_value(match.group("value"))
            if value is None:
                continue
            add(match.start(), "vibracion", value, "mm/s", None)

        # Goteo por empaquetadura (sin valor numérico dictado).
        for match in re.finditer(r"\b(gotea|goteando|chorrea|pierde)\b[^.]*?\bempaquetadura\b", segment, re.IGNORECASE):
            fuerte = bool(re.search(r"\b(chorrea|pierde\s+bastante)\b", match.group(0), re.IGNORECASE))
            observation = "pérdida importante por empaquetadura" if fuerte else "goteo por empaquetadura"
            add(match.start(), "goteo_empaquetadura", None, None, observation)

        # Goteo con valor (en correcciones): "estaba en cuarenta y cinco gotas por minuto".
        for match in re.finditer(
            rf"\b(?:esta(?:ba)?\s+en\s+)?(?P<value>{_NUM_VALUE})\s+gotas?\s+por\s+minuto\b",
            segment,
            re.IGNORECASE,
        ):
            value = self.parse_value(match.group("value"))
            if value is None:
                continue
            add(match.start(), "goteo_empaquetadura", value, "gotas/min", None)

        # Ruido: "hace un golpeteo metálico".
        for match in re.finditer(
            r"\b(golpeteo\s+metalico|ruido\s+raro\s+de\s+rodamiento|piedras\s+adentro)\b",
            segment,
            re.IGNORECASE,
        ):
            add(match.start(), "ruido", None, None, re.sub(r"\s+", " ", match.group(1)).strip())

        # Correas: "las correas están flojas, chillan".
        for match in re.finditer(r"\bcorreas?\s+(?:estan|esta)\s+([^,]+)", segment, re.IGNORECASE):
            add(match.start(), "estado_correas", None, None, "correas " + match.group(1).strip())

        # Nivel de aceite por visor.
        if re.search(r"\b(visor\s+de\s+aceite\s+(?:esta|están)\s+bajo|no\s+tiene\s+aceite\s+en\s+el\s+visor|casi\s+no\s+tiene\s+aceite)\b", segment, re.IGNORECASE):
            add(0, "nivel_aceite_visor", None, None, "nivel de aceite bajo")


class ClosureExtractor:
    """Extrae de la nota de cierre las tareas, repuestos, horas y prueba final.

    Devuelve ``None`` si la nota no trae evidencia interpretable, para que el
    flujo no invente un cierre.
    """

    def __init__(self, task_catalog: list[dict] | None = None, inventory_catalog: list[dict] | None = None) -> None:
        self.task_by_name = {
            self._key(task.get("nombre", "")): str(task["codigo"])
            for task in (task_catalog or [])
            if task.get("codigo")
        }
        self.part_names = sorted(
            {self._key(part.get("nombre", "")): part["codigo"] for part in (inventory_catalog or []) if part.get("codigo")}.items(),
            key=lambda pair: len(pair[0]),
            reverse=True,
        )

    @staticmethod
    def _key(text: str) -> str:
        normalized = _strip_accents(text)
        normalized = normalized.replace("µm", "micras").replace("μm", "micras")
        normalized = normalized.replace("µ", "u").replace("μ", "u")
        normalized = re.sub(r"\([^)]*\)", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip().casefold()
        return normalized

    def extract(self, transcript: str) -> dict | None:
        tasks: list[str] = []
        parts: list[str] = []
        hours: float = 0.0
        final_test = ""
        normalized = _strip_accents(transcript)
        for sentence in re.split(r"[.!?;]\s+|\n+", normalized):
            sentence = sentence.strip()
            if not sentence:
                continue
            if sentence.casefold().startswith("hice "):
                name = self._key(sentence[5:])
                code = self.task_by_name.get(name)
                if code and code not in tasks:
                    tasks.append(code)
            elif sentence.casefold().startswith("use "):
                for mention in sentence[4:].split(","):
                    code = self._resolve_part(mention)
                    if code and code not in parts:
                        parts.append(code)
            elif " horas" in sentence or sentence.casefold().endswith(" horas"):
                match = re.search(rf"\b(?P<value>{_NUM_VALUE})\s+horas?\b", sentence, re.IGNORECASE)
                if match:
                    hours = VoicePartExtractor.parse_words(match.group("value"))
            elif re.search(r"\bprobe\s+a\b", sentence, re.IGNORECASE) or "sin perdida" in sentence or "quedo en servicio" in sentence:
                final_test = re.sub(r"\s+", " ", sentence).strip()

        if not tasks or not final_test:
            return None
        return {
            "tasks_done": tasks,
            "parts_used": parts,
            "hours": hours,
            "final_test": final_test,
        }

    def _resolve_part(self, mention: str) -> str | None:
        key = self._key(mention)
        # La cantidad dictada ("un", "dos", ...) va al inicio; la quitamos para el nombre.
        key = re.sub(r"^(?:un|una|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|"
                     r"diez|once|doce|trece|catorce|quince|dieciseis|dieciocho|veinte)\s+", "", key)
        for name, code in self.part_names:
            if name and (name in key or key in name):
                return code
        return None


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
    """Reemplaza solo las filas identificadas en la corrección, sin perder las demás.

    La identidad de una fila es (equipo, variable), así una corrección de una
    variable no borra otras variables del mismo equipo.
    """
    if not corrected:
        raise ValueError("No pude identificar la fila corregida")
    keys = [(row.equipment_tag, row.variable) for row in corrected]
    if len(keys) != len(set(keys)):
        raise ValueError("La corrección identifica más de una lectura para la misma variable")
    result = list(rows)
    positions = {(row.equipment_tag, row.variable): index for index, row in enumerate(result)}
    for row in corrected:
        key = (row.equipment_tag, row.variable)
        if key not in positions:
            raise ValueError(
                f"La corrección refiere una lectura ausente: {row.equipment_tag}/{row.variable}"
            )
        result[positions[key]] = row
    return result
