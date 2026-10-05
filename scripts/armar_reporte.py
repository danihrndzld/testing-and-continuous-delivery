#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdf>=4"]
# ///
"""Arma reporte.html + reporte.pdf desde reporte.json, el JUnit XML del runner y la cobertura.

Uso:
  uv run armar_reporte.py reporte.json --junit junit.xml [--cobertura coverage.json] [--raiz .]

Los conteos, resultados y cobertura salen de los artefactos del runner, nunca del JSON.
Antes de renderizar valida la trazabilidad (IDs JSON <-> JUnit <-> archivo:línea) y aborta
con la lista de errores si algo no cuadra. El esquema de reporte.json está en
references/reporte-contenido.md §5.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
DISENO = SKILL / "references" / "reporte-diseno.md"
CONTENIDO = SKILL / "references" / "reporte-contenido.md"
A_PDF = SKILL / "scripts" / "html_a_pdf.sh"

PREFIJOS = "EP|BVA|DT|ST|PW|BR|MCDC|EG|CL|AC|PBT"
RE_ID = re.compile(rf"(?<![A-Za-z])({PREFIJOS})[-_]([RTI]?)(\d+)(?!\d)", re.I)
MESES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
TECNICA_POR_PREFIJO = {
    "EP": "Equivalence Partitioning", "BVA": "Boundary Value Analysis", "DT": "Decision Table",
    "ST": "State Transition", "PW": "Pairwise", "BR": "Branch testing", "MCDC": "MC/DC",
    "EG": "Error Guessing", "CL": "Checklist-based", "AC": "ATDD", "PBT": "Property-based",
}

esc = html.escape


def clave_id(texto: str) -> set[tuple[str, str, int]]:
    """IDs canónicos en un texto: ('BVA', '', 9) para 'BVA-09', 'bva_9' o 'test_bva_09_x'."""
    return {(p.upper(), l.upper(), int(n)) for p, l, n in RE_ID.findall(texto)}


# --------------------------------------------------------------------------- entradas

def leer_junit(rutas: list[Path]) -> list[dict]:
    casos = []
    for ruta in rutas:
        for tc in ET.parse(ruta).getroot().iter("testcase"):
            estado, detalle = "pasa", ""
            for etiqueta, nombre in (("failure", "falla"), ("error", "error"), ("skipped", "omitido")):
                nodo = tc.find(etiqueta)
                if nodo is not None:
                    estado = nombre
                    detalle = ((nodo.get("message") or "") + "\n" + (nodo.text or "")).strip()
                    break
            nombre = tc.get("name", "")
            casos.append({
                "nombre": f"{tc.get('classname', '')}::{nombre}".strip(":"),
                "claves": clave_id(nombre),
                "estado": estado, "detalle": detalle,
                "tiempo": float(tc.get("time") or 0),
            })
    return casos


def leer_cobertura(ruta: Path | None) -> dict | None:
    """Acepta coverage.py JSON (`--cov-report=json`) o istanbul json-summary (Jest/Vitest/c8)."""
    if not ruta:
        return None
    d = json.loads(ruta.read_text())
    if "totals" in d:  # coverage.py
        def fila(nombre, s):
            return [nombre, s["covered_lines"], s["num_statements"], s.get("covered_branches", 0), s.get("num_branches", 0)]
        archivos = [fila(n, f["summary"]) for n, f in sorted(d.get("files", {}).items())]
        return {"archivos": archivos, "total": fila("Total", d["totals"])}
    if "total" in d:  # istanbul
        def fila(nombre, s):
            return [nombre, s["statements"]["covered"], s["statements"]["total"], s["branches"]["covered"], s["branches"]["total"]]
        archivos = [fila(n, s) for n, s in sorted(d.items()) if n != "total"]
        return {"archivos": archivos, "total": fila("Total", d["total"])}
    raise SystemExit(f"Formato de cobertura no reconocido: {ruta}")


def leer_bibliografia() -> dict[str, str]:
    """Claves `[ctfl] texto…` de reporte-contenido.md §7 -> HTML de la referencia."""
    bib = {}
    for linea in CONTENIDO.read_text().splitlines():
        m = re.match(r"^\[([a-z0-9][a-z0-9-]*)\] (.+)$", linea)
        if m:
            texto = esc(m.group(2), quote=False)
            texto = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", texto)
            texto = re.sub(r" Secciones verificadas:.*$", "", texto)
            bib[m.group(1)] = texto
    return bib


def leer_esqueleto() -> tuple[str, str]:
    """<style> y <script> del esqueleto en reporte-diseno.md §8 (fuente única del diseño)."""
    md = DISENO.read_text()
    bloque = re.search(r"## 8\. Esqueleto completo.*?```html\n(.*?)```", md, re.S).group(1)
    estilo = re.search(r"<style>.*?</style>", bloque, re.S).group(0)
    script = re.search(r"<script>.*?</script>", bloque, re.S).group(0)
    return estilo, script


# --------------------------------------------------------------------------- validación

def validar(rep: dict, junit: list[dict], raiz: Path) -> tuple[list[str], dict]:
    errores = []
    base = rep.get("base_de_prueba") or {}
    if base.get("tipo") not in ("spec", "usuario", "supuestos"):
        errores.append("base_de_prueba.tipo debe ser 'spec', 'usuario' o 'supuestos'. Los esperados nunca salen "
                       "del código bajo prueba: pide los esperados al usuario o decláralos como supuestos.")
    if base.get("tipo") == "supuestos" and not rep.get("supuestos"):
        errores.append("base_de_prueba.tipo = 'supuestos' exige la lista 'supuestos' con los casos que dependen de cada uno.")

    ids_casos = {c["id"] for t in rep.get("tecnicas", []) for c in t.get("casos", [])}
    for s in rep.get("supuestos", []):
        for cid in s.get("casos", []):
            if cid not in ids_casos:
                errores.append(f"Supuesto {s.get('id')}: el caso {cid} no existe en tecnicas[].casos.")

    for r in rep.get("riesgos", []):
        if r.get("prob") not in (1, 2, 3) or r.get("impacto") not in (1, 2, 3):
            errores.append(f"Riesgo {r.get('id')}: prob e impacto van de 1 a 3.")

    resultado = {}  # id del JSON -> caso JUnit
    vistos = {}
    for t in rep.get("tecnicas", []):
        for c in t.get("casos", []):
            claves = clave_id(c["id"])
            if len(claves) != 1:
                errores.append(f"ID inválido '{c['id']}': usa {PREFIJOS.replace('|', ', ')} + número (BVA-09, DT-R3).")
                continue
            k = next(iter(claves))
            if k in vistos:
                errores.append(f"ID duplicado en reporte.json: {c['id']} y {vistos[k]}.")
            vistos[k] = c["id"]
            en_junit = [j for j in junit if k in j["claves"]]
            if not en_junit:
                errores.append(f"{c['id']} no aparece en el JUnit XML: el caso no existe o no se ejecutó.")
            elif len(en_junit) > 1:
                errores.append(f"{c['id']} aparece en {len(en_junit)} tests del JUnit XML.")
            else:
                resultado[c["id"]] = en_junit[0]
            ub = c.get("ubicacion", "")
            m = re.match(r"^(.+):(\d+)$", ub)
            if not m:
                errores.append(f"{c['id']}: ubicacion '{ub}' debe ser archivo:línea.")
                continue
            archivo = raiz / m.group(1)
            if not archivo.is_file():
                errores.append(f"{c['id']}: no existe {archivo}.")
                continue
            lineas = archivo.read_text(errors="replace").splitlines()
            n = int(m.group(2))
            if not (1 <= n <= len(lineas)) or k not in clave_id(lineas[n - 1]):
                errores.append(f"{c['id']}: la línea {ub} no contiene el ID.")

    for j in junit:
        if not j["claves"]:
            errores.append(f"Test sin ID de técnica: {j['nombre']}.")
        elif not any(k in vistos for k in j["claves"]):
            errores.append(f"Test {j['nombre']} no está documentado en reporte.json.")

    fallidos = {cid for cid, j in resultado.items() if j["estado"] in ("falla", "error")}
    documentados = set()
    for d in rep.get("defectos", []):
        documentados.add(d.get("caso"))
        if d.get("caso") not in fallidos:
            errores.append(f"Defecto {d.get('id')}: el caso {d.get('caso')} no falla en el JUnit XML.")
        mu = re.match(r"^(.+):(\d+)$", d.get("ubicacion", ""))
        if not mu or not (raiz / mu.group(1)).is_file() or not (
                1 <= int(mu.group(2)) <= len((raiz / mu.group(1)).read_text(errors="replace").splitlines())):
            errores.append(f"Defecto {d.get('id')}: ubicacion '{d.get('ubicacion', '')}' debe ser archivo:línea existente.")
        if d.get("severidad") not in ("alta", "media", "baja"):
            errores.append(f"Defecto {d.get('id')}: severidad debe ser alta, media o baja.")
    for cid in sorted(fallidos - documentados):
        errores.append(f"{cid} falla y no está en 'defectos': documéntalo (no se ajusta el esperado).")
    return errores, resultado


# --------------------------------------------------------------------------- HTML

class Doc:
    def __init__(self):
        self.partes: list[str] = []
        self.n = 0

    def h2(self, texto: str):
        self.n += 1
        self.partes.append(f'<h2 id="s{self.n}">{texto}</h2>')

    def h3(self, texto: str):
        self.n += 1
        self.partes.append(f'<h3 id="s{self.n}">{texto}</h3>')

    def h4(self, texto: str):
        self.partes.append(f"<h4>{texto}</h4>")

    def add(self, html_: str):
        if html_:
            self.partes.append(html_)

    def html(self) -> str:
        return "\n".join(self.partes)


def caja(color: str, contenido: str) -> str:
    return f'<div class="caja {color}">{contenido}</div>' if contenido else ""


def tabla(cabeza: list[str], filas: list[list], caption: str = "", clases: str = "t",
          clase_fila=None, num: set[int] = frozenset()) -> str:
    th = "".join(f'<th class="num">{c}</th>' if i in num else f"<th>{c}</th>" for i, c in enumerate(cabeza))
    cuerpo = []
    for fila in filas:
        cls = clase_fila(fila) if clase_fila else ""
        tds = "".join(f'<td class="num">{v}</td>' if i in num else f"<td>{v}</td>" for i, v in enumerate(fila))
        cuerpo.append(f'<tr class="{cls}">{tds}</tr>' if cls else f"<tr>{tds}</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f'<table class="{clases}">{cap}<thead><tr>{th}</tr></thead><tbody>{"".join(cuerpo)}</tbody></table>'


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.0f}%" if b else "n/a"


def fecha_larga(hoy: dt.date) -> str:
    return f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"


def construir(rep: dict, junit: list[dict], resultado: dict, cob: dict | None, bib: dict) -> tuple[str, list[str]]:
    por = rep.get("portada", {})
    riesgos = rep.get("riesgos", [])
    for r in riesgos:
        r["nivel"] = r["prob"] * r["impacto"]
    modo = rep.get("modo") or ("completo" if any(r["nivel"] >= 6 for r in riesgos) else "corto")
    tecnicas = rep.get("tecnicas", [])
    casos = [(t, c) for t in tecnicas for c in t.get("casos", [])]
    total = len(junit)
    cuenta = {e: sum(j["estado"] == e for j in junit) for e in ("pasa", "falla", "error", "omitido")}
    fallan = cuenta["falla"] + cuenta["error"]
    defectos = rep.get("defectos", [])
    estado_txt = {"pasa": "pasa", "falla": "<b>falla</b>", "error": "<b>error</b>", "omitido": "omitido"}

    d = Doc()

    # 1. Ficha
    d.h2("Ficha del reporte")
    ficha = list(rep.get("ficha", []))
    ficha += [["Base de prueba", f"{esc(rep['base_de_prueba']['tipo'])}: {rep['base_de_prueba'].get('fuente', '')}"],
              ["Comando", f"<code>{esc(rep.get('entorno', {}).get('comando', ''))}</code>"],
              ["Versiones con las que corrieron las pruebas", esc(rep.get("entorno", {}).get("versiones", ""))],
              ["Modo del reporte", "completo (hay condiciones de riesgo alto)" if modo == "completo" else "corto (riesgo bajo o medio)"]]
    d.add(tabla(["Campo", "Valor"], ficha))

    # 2. Resumen (números del JUnit, no del JSON)
    d.h2("Resumen")
    cob_txt = ""
    if cob:
        _, sc, st, bc, bt = cob["total"]
        cob_txt = f" Cobertura estructural: {sc} de {st} sentencias ({pct(sc, st)}) y {bc} de {bt} ramas ({pct(bc, bt)})."
    cifras = (f"<p><b>{cuenta['pasa']} de {total} pruebas pasan; {fallan} fallan; {cuenta['omitido']} omitidas. "
              f"{len(defectos)} defecto(s) documentado(s).</b> Técnicas: {len(tecnicas)}.{cob_txt}</p>")
    d.add(caja("verde" if fallan == 0 and not defectos else "roja", cifras))
    d.add(rep.get("resumen", ""))

    # 3. Objeto y base de prueba (+ supuestos)
    if modo == "completo" or rep.get("supuestos"):
        d.h2("Objeto y base de prueba")
        if modo == "completo":
            d.add(rep.get("objeto", ""))
        if rep.get("supuestos"):
            d.add(caja("dorada", "<p><b>Los esperados de estos casos dependen de supuestos; si un supuesto es falso, esos esperados también.</b></p>"))
            d.add(tabla(["ID", "Supuesto", "Casos que dependen"],
                        [[esc(s["id"]), s["texto"], ", ".join(map(esc, s.get("casos", [])))] for s in rep["supuestos"]]))

    # 4. Riesgo
    d.h2("Análisis de riesgo de producto")
    d.add("<p>Nivel = probabilidad × impacto, escala 1-3 cada uno [ctfl, §5.2.3]. Nivel 1-2 bajo, 3-4 medio, 6-9 alto.</p>")
    d.add(tabla(["ID", "Condición", "Riesgo", "Prob.", "Imp.", "Nivel", "Técnica y cobertura exigida"],
                [[esc(r["id"]), r["condicion"], r["riesgo"], r["prob"], r["impacto"], r["nivel"], r.get("exige", "")] for r in riesgos],
                num={3, 4, 5},
                clase_fila=lambda f: "mal" if f[5] >= 6 else ("adv" if f[5] >= 3 else "")))

    # 5. Estrategia
    if modo == "completo" or rep.get("criterios_salida"):
        d.h2("Estrategia y criterios de salida")
        if modo == "completo":
            d.add(rep.get("estrategia", ""))
        if rep.get("criterios_salida"):
            d.add(caja("dorada", "<p><b>Criterios de salida fijados antes de ejecutar [ctfl, §5.1.3].</b></p><ul>"
                       + "".join(f"<li>{c}</li>" for c in rep["criterios_salida"]) + "</ul>"))

    # 6. Técnicas
    d.h2("Técnicas aplicadas")
    if modo == "completo":
        for t in tecnicas:
            n_casos = len(t.get("casos", []))
            d.h3(f"{t['nombre']}: {n_casos} caso{'s' if n_casos != 1 else ''}")
            d.h4("Definición")
            d.add(caja("azul", t.get("definicion", "")))
            d.h4("Por qué aplica aquí")
            d.add(caja("morada", t.get("por_que", "")))
            d.h4("Derivación")
            d.add(t.get("derivacion", ""))
            d.h4("Casos")
            filas = []
            for c in t.get("casos", []):
                j = resultado.get(c["id"])
                filas.append([esc(c["id"]), c.get("entrada", ""), c.get("esperado", ""),
                              f"<code>{esc(c['ubicacion'])}</code>", estado_txt[j["estado"]] if j else "—"])
            d.add(tabla(["ID", "Entrada", "Esperado", "Ubicación", "Resultado"], filas, clases="t compacta",
                        clase_fila=lambda f: "mal" if "falla" in f[4] or "error" in f[4] else ""))
            d.h4("Cobertura y límites")
            d.add(t.get("cobertura", ""))
            d.add(caja("roja", t.get("limites", "")) if t.get("limites") else "")
    else:
        filas = []
        for t in tecnicas:
            ids = [c["id"] for c in t.get("casos", [])]
            pasan = sum(resultado.get(i, {}).get("estado") == "pasa" for i in ids)
            filas.append([f"<b>{t['nombre']}</b><br>{t.get('definicion', '')}", t.get("por_que", ""),
                          f"{len(ids)} casos ({pasan} pasan)<br>{esc(ids[0])} … {esc(ids[-1])}" if ids else "—",
                          t.get("cobertura", "")])
        d.add(tabla(["Técnica", "Por qué aplica aquí", "Casos", "Cobertura"], filas))

    # 7. Descartadas
    d.h2("Técnicas consideradas y descartadas")
    d.add(tabla(["Técnica", "Por qué no aplica o no compensa"], rep.get("descartadas", [])))

    # 8. Trazabilidad
    d.h2("Trazabilidad")
    d.add("<p>Condición → técnica → caso → ubicación → resultado [ctfl, §1.4.4]. Validada automáticamente contra el JUnit XML y el código de pruebas.</p>")
    d.add(tabla(["Condición", "Técnica", "ID", "Ubicación", "Resultado"],
                [[", ".join(map(esc, t.get("condiciones", []))), esc(t["nombre"]), esc(c["id"]),
                  f"<code>{esc(c['ubicacion'])}</code>", estado_txt[resultado[c["id"]]["estado"]]] for t, c in casos],
                clases="t compacta", clase_fila=lambda f: "mal" if "falla" in f[4] or "error" in f[4] else ""))

    # 9. Ejecución
    d.h2("Ejecución")
    ent = rep.get("entorno", {})
    d.add(f"<p>Comando: <code>{esc(ent.get('comando', ''))}</code>. Versiones: {esc(ent.get('versiones', ''))}. "
          f"Duración: {sum(j['tiempo'] for j in junit):.2f} s. Fuente de los conteos: JUnit XML del runner.</p>")
    por_prefijo: dict[str, list[int]] = {}
    for j in junit:
        for p, _, _ in j["claves"]:
            fila = por_prefijo.setdefault(p, [0, 0, 0, 0])
            fila[0] += 1
            fila[{"pasa": 1, "falla": 2, "error": 2, "omitido": 3}[j["estado"]]] += 1
    filas = [[f"{p} ({TECNICA_POR_PREFIJO[p]})", *v] for p, v in sorted(por_prefijo.items())]
    d.add(tabla(["Técnica", "Ejecutados", "Pasan", "Fallan", "Omitidos"],
                filas + [["Total", total, cuenta["pasa"], fallan, cuenta["omitido"]]], num={1, 2, 3, 4},
                clase_fila=lambda f: "total" if f[0] == "Total" else ""))
    for j in junit:
        if j["estado"] in ("falla", "error"):
            d.add(f"<p><b>{esc(j['nombre'])}</b></p><pre class=\"salida\">{esc(j['detalle'][:1500])}</pre>")

    # 10. Cobertura estructural
    d.h2("Cobertura estructural")
    if cob:
        d.add(tabla(["Archivo", "Sentencias", "Total", "%", "Ramas", "Total", "%"],
                    [[f"<code>{esc(a)}</code>", sc, st, pct(sc, st), bc, bt, pct(bc, bt)]
                     for a, sc, st, bc, bt in cob["archivos"] + [cob["total"]]],
                    num={1, 2, 3, 4, 5, 6}, clase_fila=lambda f: "total" if f[0] == "<code>Total</code>" else ""))
        d.add("<p>Branch coverage subsume statement coverage; ninguna de las dos detecta requisitos no implementados [ctfl, §4.3.2, §4.3.3].</p>")
    else:
        d.add(caja("dorada", "<p><b>No se midió cobertura estructural:</b> no se pasó <code>--cobertura</code>.</p>"))
    d.add(rep.get("cobertura_nota", ""))

    # 11. Defectos
    d.h2(f"Defectos encontrados: {len(defectos)}")
    if defectos:
        for df in defectos:
            d.add(caja("roja",
                       f"<p><b>{esc(df['id'])} (severidad {esc(df['severidad'])}), expuesto por {esc(df['caso'])}.</b></p>"
                       f"<p>Entrada: {df.get('entrada', '')}. Esperado: {df.get('esperado', '')}. Obtenido: {df.get('obtenido', '')}. "
                       f"Ubicación probable: <code>{esc(df.get('ubicacion', ''))}</code>.</p>{df.get('analisis', '')}"))
    else:
        d.add(f"<p>Ninguno en {total} casos. Las pruebas muestran la presencia de defectos, no su ausencia [ctfl, §1.3].</p>")

    # 12. Riesgo residual
    if modo == "completo" or rep.get("riesgo_residual"):
        d.h2("Riesgo residual y recomendaciones")
        d.add(rep.get("riesgo_residual", ""))

    # 13. Decisión
    dec = rep.get("decision", {})
    d.h2("Criterio de decisión")
    clases = ["ok", "adv", "mal"]
    d.add(tabla(["Resultado", "Criterio"], dec.get("semaforo", []),
                clase_fila=lambda f: clases[dec["semaforo"].index(f)] if f in dec.get("semaforo", []) else ""))
    d.add(caja({"ok": "verde", "adv": "dorada", "mal": "roja"}.get(dec.get("veredicto"), "azul"), dec.get("texto", "")))

    cuerpo = d.html()

    # Citas por clave -> número por orden de primera aparición
    orden: list[str] = []

    def citar(m):
        clave, resto = m.group(1), m.group(2) or ""
        if clave not in bib:
            return m.group(0)
        if clave not in orden:
            orden.append(clave)
        return f"[{orden.index(clave) + 1}{resto}]"

    re_cita = re.compile(r"\[([a-z0-9][a-z0-9-]*)((?:,\s*[^\]\[]+)?)\]")
    desconocidas = sorted({m.group(1) for m in re_cita.finditer(cuerpo) if m.group(1) not in bib and "§" in (m.group(2) or "")})
    cuerpo = re_cita.sub(citar, cuerpo)

    apend = Doc()
    apend.n = 1000
    apend.h2("Referencias")
    apend.add('<ol class="referencias">' + "".join(f"<li>{bib[k]}</li>" for k in orden) + "</ol>")
    if rep.get("reproduccion"):
        apend.h2("Reproducción")
        apend.add("<pre>" + esc("\n".join(rep["reproduccion"])) + "</pre>")

    hoy = dt.date.today()
    ficha_portada = [
        ("Objeto de prueba:", por.get("objeto_detalle", por.get("objeto", ""))),
        ("Versión probada:", por.get("version", "")),
        ("Técnicas:", ", ".join(esc(t["nombre"]) for t in tecnicas)),
        ("Resultado:", f"{cuenta['pasa']} de {total} pruebas pasan"),
        ("Fecha:", por.get("fecha") or fecha_larga(hoy)),
    ]
    sub = por.get("subtitulo", ["", ""]) + ["", ""]
    portada = f"""<section class="portada">
  <hr>
  <div class="org">{esc(por.get('org', '').upper())} | {esc(por.get('area', 'Aseguramiento de calidad'))}</div>
  <h1>{esc(por.get('tipo_doc', 'Reporte de Pruebas'))}<br>{esc(por.get('objeto', ''))}</h1>
  <div class="sub">{sub[0]}<br>{sub[1]}</div>
  <div class="regla-acento"></div>
  <table class="ficha-portada">{''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in ficha_portada if b)}</table>
  <hr>
</section>"""
    body = (portada + '\n<nav class="indice"><h2>Índice</h2><ol id="indice"></ol></nav>\n<main>\n'
            + cuerpo + '\n</main>\n<section class="apendices">\n' + apend.html() + "\n</section>")
    return body, desconocidas


def documento(body: str, rep: dict, paginas: list[str]) -> str:
    estilo, script = leer_esqueleto()
    por = rep.get("portada", {})
    hoy = dt.date.today()
    for marca, valor in {"{{ORG}}": por.get("org", ""), "{{TIPO_DOC}}": por.get("tipo_doc", "Reporte de Pruebas"),
                         "{{TITULO_CORTO}}": por.get("titulo_corto", f"{por.get('objeto', '')} {hoy.year}")}.items():
        estilo = estilo.replace(marca, valor.replace('"', "'"))
    titulo = esc(f"{por.get('tipo_doc', 'Reporte de Pruebas')} — {por.get('objeto', '')}")
    return (f'<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<title>{titulo}</title>\n{estilo}\n</head>\n'
            f"<body>\n{body}\n<script>window.PAGINAS = {json.dumps(paginas)};</script>\n{script}\n</body>\n</html>\n")


def titulos_indice(body: str) -> list[str]:
    """Textos de los títulos que lista el índice, en el mismo orden que el script del esqueleto."""
    main = re.search(r"<main>(.*)</main>", body, re.S).group(1)
    apend = re.search(r'<section class="apendices">(.*)</section>', body, re.S).group(1)
    limpiar = lambda s: " ".join(html.unescape(re.sub(r"<[^>]+>", "", s)).split())
    return ([limpiar(t) for t in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", main, re.S)]
            + [limpiar(t) for t in re.findall(r"<h2[^>]*>(.*?)</h2>", apend, re.S)])


def paginas_del_pdf(pdf: Path, titulos: list[str]) -> list[str]:
    from pypdf import PdfReader
    r = PdfReader(pdf)
    plano = []

    def recorrer(nodos):
        for x in nodos:
            if isinstance(x, list):
                recorrer(x)
            else:
                plano.append((" ".join(x.title.split()), r.get_destination_page_number(x) + 1))
    recorrer(r.outline)
    paginas, i = [], 0
    for t in titulos:
        while i < len(plano) and plano[i][0] != t:
            i += 1
        paginas.append(str(plano[i][1]) if i < len(plano) else "")
        i += 1 if i < len(plano) else 0
    return paginas


def renderizar(html_path: Path) -> Path:
    pdf = html_path.with_suffix(".pdf")
    subprocess.run(["bash", str(A_PDF), str(html_path), str(pdf)], check=True, stdout=subprocess.DEVNULL)
    return pdf


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reporte", type=Path, help="reporte.json")
    ap.add_argument("--junit", type=Path, nargs="+", required=True, help="JUnit XML del runner")
    ap.add_argument("--cobertura", type=Path, help="coverage.py JSON o istanbul coverage-summary.json")
    ap.add_argument("--raiz", type=Path, default=Path.cwd(), help="raíz del proyecto para resolver archivo:línea")
    ap.add_argument("--solo-validar", action="store_true", help="valida y sale sin generar archivos")
    a = ap.parse_args(argv)

    rep = json.loads(a.reporte.read_text())
    junit = leer_junit(a.junit)
    errores, resultado = validar(rep, junit, a.raiz)
    if errores:
        print(f"reporte.json no pasa la validación ({len(errores)} errores):", file=sys.stderr)
        for e in errores:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if a.solo_validar:
        print("Validación OK")
        return 0

    body, desconocidas = construir(rep, junit, resultado, leer_cobertura(a.cobertura), leer_bibliografia())
    for k in desconocidas:
        print(f"aviso: cita [{k}, …] sin entrada en la bibliografía de reporte-contenido.md §7", file=sys.stderr)

    salida = a.reporte.parent / "reporte.html"
    titulos = titulos_indice(body)
    salida.write_text(documento(body, rep, ["00"] * len(titulos)))   # pasada 1: reserva el ancho del número
    paginas = paginas_del_pdf(renderizar(salida), titulos)
    salida.write_text(documento(body, rep, paginas))                 # pasada 2: índice con páginas reales
    pdf = renderizar(salida)
    print(salida)
    print(pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
