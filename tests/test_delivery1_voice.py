"""Tests de la Entrega 1: extracción de parte por voz (P0).

No usan rutas absolutas: cargan los datos oficiales locales desde ``datos/``.
"""

from datetime import datetime

import pytest

from app.integrations import AmbiguousInputError, VoicePartExtractor, normalize_unit
from app.official_data import load_equipment
from app.models import VoiceNote


@pytest.fixture(scope="module")
def equipment():
    return load_equipment("datos/planta.yaml")


@pytest.fixture()
def note():
    return VoiceNote(note_id="VIVO-TEST", observed_at=datetime(2026, 11, 5, 10, 0))


def _rows(equipment, note, transcript):
    return VoicePartExtractor(equipment).extract(note, transcript)


def test_filtro_b_diferencial(equipment, note):
    rows = _rows(equipment, note, "El filtro B me dio uno coma ocho de diferencial.")
    assert len(rows) == 1
    assert rows[0].equipment_tag == "F-201B"
    assert rows[0].variable == "presion_diferencial"
    assert rows[0].value == 1.8
    assert rows[0].unit == "kg/cm2"


def test_temperatura_aceite(equipment, note):
    rows = _rows(equipment, note, "La uno tiene ochenta grados de aceite.")
    assert rows[0].equipment_tag == "B-101"
    assert rows[0].variable == "temperatura_aceite"
    assert rows[0].value == 80
    assert rows[0].unit == "degC"


def test_vibracion(equipment, note):
    rows = _rows(equipment, note, "La dos tiene una vibración de siete coma dos.")
    assert rows[0].equipment_tag == "B-102"
    assert rows[0].variable == "vibracion"
    assert rows[0].value == 7.2
    assert rows[0].unit == "mm/s"


def test_presion_succion(equipment, note):
    rows = _rows(equipment, note, "La tres está en cero coma nueve de succión.")
    assert rows[0].equipment_tag == "B-103"
    assert rows[0].variable == "presion_succion"
    assert rows[0].value == 0.9
    assert rows[0].unit == "kg/cm2"


def test_uno_coma_ocho_y_uno_ocho(equipment, note):
    coma = _rows(equipment, note, "El filtro B me dio uno coma ocho de diferencial.")[0]
    junto = _rows(equipment, note, "El filtro B me dio uno ocho de diferencial.")[0]
    assert coma.value == 1.8
    assert junto.value == 1.8


def test_unidad_kg_cm2(equipment, note):
    rows = _rows(equipment, note, "La uno está en ciento doce kg/cm² de descarga.")
    assert rows[0].value == 112
    assert rows[0].unit == "kg/cm2"


def test_normalize_unit_superindice():
    assert normalize_unit("kg/cm²") == "kg/cm2"
    assert normalize_unit("kgf/cm2") == "kg/cm2"
    assert normalize_unit("kilos") == "kg/cm2"
    assert normalize_unit("libras") == "psi"
    assert normalize_unit("bares") == "bar"


def test_nota_varios_equipos_y_variables(equipment, note):
    transcript = (
        "La dos está en ciento doce de descarga. "
        "El filtro B me dio uno ocho de diferencial. "
        "El pulmón está en cinco coma dos metros."
    )
    rows = _rows(equipment, note, transcript)
    assert {(r.equipment_tag, r.variable, r.value) for r in rows} == {
        ("B-102", "presion_descarga_local", 112),
        ("F-201B", "presion_diferencial", 1.8),
        ("TK-301", "nivel", 5.2),
    }


def test_diferencial_en_decenas_pregunta(equipment, note):
    with pytest.raises(AmbiguousInputError):
        _rows(equipment, note, "El filtro A me dio catorce de diferencial.")


def test_la_bomba_generica_pregunta(equipment, note):
    with pytest.raises(AmbiguousInputError) as exc:
        _rows(equipment, note, "La bomba está en mil seiscientos de descarga.")
    assert set(exc.value.options) == {"B-101", "B-102", "B-103"}


def test_observacion_goteo_y_estado(equipment, note):
    rows = _rows(
        equipment,
        note,
        "La dos está en mil seiscientos de descarga, sigue goteando por la empaquetadura, "
        "el rodamiento me dio cincuenta y dos grados con la pistola.",
    )
    by_var = {(r.variable): r for r in rows}
    assert "presion_descarga_local" in by_var
    assert by_var["goteo_empaquetadura"].observation == "goteo por empaquetadura"
    assert by_var["temperatura_rodamiento_ir"].value == 52
