"""Regresión de scripts/armar_reporte.py sobre el fixture de envíos (defecto sembrado en envios.py:12).

Correr desde la raíz del repo:  uv run --no-project --with pytest --with pypdf pytest evals/test_armar_reporte.py -q
"""
import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).resolve().parent / "fixture-envios"
spec = importlib.util.spec_from_file_location("armar_reporte", RAIZ / "scripts" / "armar_reporte.py")
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)


@pytest.fixture
def proyecto(tmp_path):
    destino = tmp_path / "p"
    shutil.copytree(FIXTURE, destino, ignore=shutil.ignore_patterns("reporte.html", "reporte.pdf", "__pycache__"))
    return destino


def correr(p, *extra, mutar=None):
    if mutar:
        rep = json.loads((p / "reporte.json").read_text())
        mutar(rep)
        (p / "reporte.json").write_text(json.dumps(rep))
    return ar.main([str(p / "reporte.json"), "--junit", str(p / "junit.xml"),
                    "--cobertura", str(p / "coverage.json"), "--raiz", str(p), *extra])


def test_genera_html_y_pdf_con_indice_paginado(proyecto):
    assert correr(proyecto) == 0
    html = (proyecto / "reporte.html").read_text()
    assert (proyecto / "reporte.pdf").stat().st_size > 10_000
    assert "8 de 9 pruebas pasan" in html                      # conteo desde el JUnit, no del JSON
    paginas = json.loads(re.search(r"window.PAGINAS = (\[.*?\]);", html).group(1))
    assert paginas and all(p.isdigit() for p in paginas)      # índice con número de página real
    assert "D-01 (severidad alta), expuesto por BVA-04" in html
    assert "[ctfl" not in html and "[1, §4.2.1]" in html       # citas por clave numeradas


def test_modo_corto_si_ningun_riesgo_es_alto(proyecto):
    def bajar(rep):
        for r in rep["riesgos"]:
            r["prob"], r["impacto"] = 1, 2
    assert correr(proyecto, mutar=bajar) == 0
    html = (proyecto / "reporte.html").read_text()
    assert "corto (riesgo bajo o medio)" in html
    assert "<h4>Definición</h4>" not in html


@pytest.mark.parametrize("mutar, mensaje", [
    (lambda r: r["tecnicas"][2]["casos"].clear(), "no está documentado en reporte.json"),
    (lambda r: r["defectos"].clear(), "BVA-04 falla y no está en 'defectos'"),
    (lambda r: r["base_de_prueba"].update(tipo="codigo"), "nunca salen"),
    (lambda r: r["tecnicas"][0]["casos"][0].update(ubicacion="tests/test_envios.py:7"), "no contiene el ID"),
    (lambda r: r["tecnicas"][0]["casos"].append({"id": "EP-09", "ubicacion": "tests/test_envios.py:6"}), "EP-09 no aparece en el JUnit"),
    (lambda r: r["defectos"][0].update(caso="BVA-01"), "no falla en el JUnit"),
    (lambda r: r.update(base_de_prueba={"tipo": "supuestos"}), "exige la lista 'supuestos'"),
    (lambda r: r.update(supuestos=[{"id": "S1", "texto": "x", "casos": ["BVA-77"]}]), "el caso BVA-77 no existe"),
    (lambda r: r["defectos"][0].update(ubicacion="src/envios.py:99"), "debe ser archivo:línea existente"),
])
def test_validacion_rechaza(proyecto, capsys, mutar, mensaje):
    assert correr(proyecto, "--solo-validar", mutar=mutar) == 1
    assert mensaje in capsys.readouterr().err
