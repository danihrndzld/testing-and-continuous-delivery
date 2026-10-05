# Diseño del reporte PDF de pruebas

Sistema de diseño del reporte que acompaña a toda prueba implementada con esta skill. Generaliza un documento formal en LaTeX (`article` 11pt A4, Helvetica, `titlesec`, `fancyhdr`, `mdframed`, `booktabs`) a **HTML + CSS impreso con Chrome headless**. Sin LaTeX. El contenido obligatorio de cada sección está en `reporte-contenido.md`; este archivo fija solo la forma.

Flujo: copiar el esqueleto de la sección 8 a `reporte.html`, reemplazar los `{{MARCADORES}}`, llenar las secciones y correr `scripts/html_a_pdf.sh reporte.html`.

## 1. Geometría y tipografía

| Elemento | Valor | Origen LaTeX |
|---|---|---|
| Página | A4, márgenes 2.5 cm arriba/abajo, 2.8 cm izquierda/derecha | `geometry` |
| Fuente base | Helvetica (fallback Arial), 11pt, interlineado 1.45 | `helvet` + `\sfdefault` |
| Monoespaciada | Courier New, 9pt | `courier` |
| Párrafos | sin sangría, 5pt entre párrafos | `parskip` 5pt |
| Tablas | 10pt; tablas largas (`.compacta`) 8.5pt | `\footnotesize` en `longtable` |
| Notas al pie de tabla | 8.5pt gris | `\footnotesize\color{bigray}` |

## 2. Paleta (tokens)

| Token | Hex | Uso |
|---|---|---|
| `--primario` | `#003865` | títulos de sección, fila de encabezado de tabla, regla del header, enlaces |
| `--secundario` | `#2D8C9E` | subsecciones, subtítulo de portada |
| `--digital` | `#00C1D4` | reservado para gráficas |
| `--acento` | `#FFB81C` | regla bajo cada `h2`, regla de portada, borde de caja dorada |
| `--acento-claro` | `#FDF3D6` | fila de totales, caja dorada, fila "condicional" del semáforo |
| `--primario-claro` | `#E6EEF5` | filas alternas, caja azul, fondo de `pre` |
| `--texto` | `#0D1B2A` | texto, `h4`, reglas superior/inferior de tabla |
| `--gris` | `#6B7280` | header/footer, etiquetas de portada, notas |
| `--linea` | `#D1D5DB` | separadores finos |
| `--verde` / `--verde-claro` | `#1A6B3A` / `#E6F4EC` | veredicto positivo, fila "aprobar" |
| `--rojo` / `--rojo-claro` | `#C0392B` / `#FDEDEC` | defectos, riesgo residual, fila "rechazar" |
| `--morado` / `--morado-claro` | `#6B3FA0` / `#F3EDF9` | justificación de la técnica elegida |

Para otra marca se cambian solo los hex de `:root`; ninguna regla usa colores literales fuera de `@page` (las cajas de margen no leen variables CSS, ver sección 7).

## 3. Página

- **Portada** (página 1): sin header ni footer. Centrada vertical y horizontalmente, en este orden: regla gris 0.5pt a todo el ancho; línea institucional gris 11pt (`ORGANIZACIÓN | Área`); título 22pt negrita `--primario` en dos líneas (tipo de documento / objeto); subtítulo 14pt `--secundario` en dos líneas; regla `--acento` de 1.5pt al 60% del ancho; ficha de portada (etiqueta gris alineada a la derecha, valor en negrita); regla gris 0.5pt.
- **Índice** (página 2): lista de secciones y subsecciones enlazadas a sus anclas, en página propia. La genera el `<script>` del esqueleto a partir de los `h2`/`h3`; no se escribe a mano.
- **Páginas de contenido**: header izquierdo `Organización | Tipo de documento`, header derecho título corto con año, ambos 9pt gris sobre una regla `--primario` de 0.4pt. Footer centrado con el número de página. Sin regla de footer.
- **Apéndices**: después del contenido, numerados con letra (A, B, …).

## 4. Jerarquía de títulos

| Nivel | Tag | Estilo | Numeración |
|---|---|---|---|
| Sección | `h2` | 14pt negrita `--primario`, regla `--acento` de 2pt debajo, 20pt arriba / 8pt abajo | `1.` |
| Subsección | `h3` | 11pt negrita `--secundario`, 12pt arriba / 4pt abajo | `1.1.` |
| Sub-subsección | `h4` | 10pt negrita `--texto`, 8pt arriba / 3pt abajo | `1.1.1.` |

La numeración la genera CSS (`counter`), no se escribe a mano. `h1` existe solo en la portada. Todo título lleva `id` para el índice.

## 5. Cajas (callouts)

Fondo claro, borde de 2pt del color fuerte, 8pt/10pt de padding, nunca se parten entre páginas. Cada color tiene un significado fijo en el reporte de pruebas:

| Clase | Significado | Equivalente LaTeX |
|---|---|---|
| `.caja.azul` | contexto, objeto de prueba, **definición citada** de una técnica | `bluebox` |
| `.caja.morada` | **por qué se eligió** la técnica en este escenario | `purplebox` |
| `.caja.dorada` | criterio de salida, horizonte de decisión, dato que el lector no debe perderse | `goldbox` |
| `.caja.verde` | objetivo de las pruebas, veredicto positivo, indicador clave | `greenbox` |
| `.caja.roja` | defecto encontrado, riesgo residual sin mitigar | `redbox` |

Una caja abre con una oración en negrita que resume su contenido.

## 6. Tablas

- `table.t`: ancho completo, regla de 1pt `--texto` arriba y abajo (booktabs `\toprule`/`\bottomrule`), encabezado con fondo `--primario` y texto blanco negrita (`\rowhead`), filas pares `--primario-claro` (`\rowalt`).
- `tr.total`: fondo `--acento-claro`, negrita, regla superior (`\rowgold`).
- `td.num` / `th.num`: alineación a la derecha para cifras.
- `table.t.compacta`: 8.5pt, para listados largos (casos de prueba, trazabilidad). El `thead` se repite en cada página (sustituye `longtable`).
- `<caption>`: arriba, 9pt gris, centrado.
- Nota al pie de tabla: `<p class="nota">` inmediatamente después, con `†` para remitir a una fila.
- Semáforo de decisión: filas `tr.ok` (verde), `tr.adv` (dorado), `tr.mal` (rojo); la primera celda toma el color fuerte en negrita.

## 7. Diferencias conocidas con la versión LaTeX

- **Índice sin números de página.** Chrome no implementa `target-counter()`. El índice es una lista de enlaces y el PDF trae marcadores (`--generate-pdf-document-outline`) para navegar.
- **Header y footer con texto literal.** Las cajas de margen de `@page` no resuelven `var()`; los marcadores `{{ORG}}`, `{{TIPO_DOC}}` y `{{TITULO_CORTO}}` se reemplazan en el CSS y los colores del header van en hex.
- **Sin partición silábica.** El texto va alineado a la izquierda (no justificado) para evitar ríos.

## 8. Esqueleto completo

Copiar tal cual y reemplazar cada `{{MARCADOR}}`. Los bloques de componentes de la sección 9 se insertan dentro de `<main>`.

```html
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{{TIPO_DOC}} — {{OBJETO}}</title>
<style>
:root {
  --primario: #003865; --secundario: #2D8C9E; --digital: #00C1D4;
  --acento: #FFB81C; --acento-claro: #FDF3D6; --primario-claro: #E6EEF5;
  --texto: #0D1B2A; --gris: #6B7280; --linea: #D1D5DB;
  --verde: #1A6B3A; --verde-claro: #E6F4EC;
  --rojo: #C0392B; --rojo-claro: #FDEDEC;
  --morado: #6B3FA0; --morado-claro: #F3EDF9;
}
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
@page {
  size: A4; margin: 2.5cm 2.8cm;
  @top-left  { content: "{{ORG}}  |  {{TIPO_DOC}}"; font: 9pt Helvetica, Arial, sans-serif; color: #6B7280; vertical-align: bottom; padding-bottom: 4pt; border-bottom: 0.4pt solid #003865; }
  @top-right { content: "{{TITULO_CORTO}}"; font: 9pt Helvetica, Arial, sans-serif; color: #6B7280; vertical-align: bottom; padding-bottom: 4pt; border-bottom: 0.4pt solid #003865; }
  @bottom-center { content: counter(page); font: 9pt Helvetica, Arial, sans-serif; color: #6B7280; }
}
@page :first { @top-left { content: none; border: 0; } @top-right { content: none; border: 0; } @bottom-center { content: none; } }
html { font: 11pt/1.45 Helvetica, Arial, sans-serif; color: var(--texto); }
body { margin: 0; background: #fff; counter-reset: sec; }
p { margin: 0 0 5pt; }
ul, ol { margin: 0 0 6pt; padding-left: 1.5em; }
li { margin-bottom: 4pt; }
code, pre { font-family: "Courier New", Courier, monospace; font-size: 9pt; }
pre { background: var(--primario-claro); padding: 8pt 10pt; white-space: pre-wrap; word-break: break-word; break-inside: avoid; }
pre.salida { break-inside: auto; font-size: 7.5pt; line-height: 1.3; }
a { color: var(--primario); text-decoration: none; }
sup.cita { color: var(--secundario); }

.portada { height: 24.7cm; display: flex; flex-direction: column; justify-content: center; text-align: center; break-after: page; }
.portada hr { border: 0; border-top: 0.5pt solid var(--gris); width: 100%; margin: 0; }
.portada .org { font-size: 11pt; color: var(--gris); margin: 10pt 0 8pt; }
.portada h1 { font-size: 22pt; line-height: 28pt; color: var(--primario); margin: 0 0 14pt; }
.portada .sub { font-size: 14pt; line-height: 18pt; color: var(--secundario); margin-bottom: 11pt; }
.portada .regla-acento { width: 60%; height: 1.5pt; background: var(--acento); margin: 0 auto 28pt; }
.ficha-portada { margin: 0 auto 42pt; border-collapse: collapse; text-align: left; }
.ficha-portada td { padding: 2pt 6pt; vertical-align: top; }
.ficha-portada td:first-child { color: var(--gris); text-align: right; white-space: nowrap; }
.ficha-portada td:last-child { font-weight: bold; }

nav.indice { break-after: page; }
nav.indice h2 { counter-increment: none; }
nav.indice h2::before { content: none; }
nav.indice ol { list-style: none; padding: 0; margin: 0; }
nav.indice li { margin: 3pt 0; }
nav.indice li li { margin-left: 1.6em; }
nav.indice > ol > li > a { font-weight: bold; }

h2 { counter-increment: sec; counter-reset: sub; font-size: 14pt; color: var(--primario); margin: 20pt 0 8pt; padding-bottom: 3pt; border-bottom: 2pt solid var(--acento); break-after: avoid; }
h2::before { content: counter(sec) ".\00a0\00a0"; }
h3 { counter-increment: sub; counter-reset: subsub; font-size: 11pt; color: var(--secundario); margin: 12pt 0 4pt; break-after: avoid; }
h3::before { content: counter(sec) "." counter(sub) ".\00a0"; }
h4 { counter-increment: subsub; font-size: 10pt; color: var(--texto); margin: 8pt 0 3pt; break-after: avoid; }
h4::before { content: counter(sec) "." counter(sub) "." counter(subsub) ".\00a0"; }
.apendices { counter-reset: sec; }
.apendices h2::before { content: counter(sec, upper-alpha) ".\00a0\00a0"; }
.apendices h3::before { content: counter(sec, upper-alpha) "." counter(sub) ".\00a0"; }

.caja { padding: 8pt 10pt; margin: 8pt 0; border: 2pt solid; break-inside: avoid; }
.caja > :last-child { margin-bottom: 0; }
.caja.azul   { background: var(--primario-claro); border-color: var(--primario); }
.caja.dorada { background: var(--acento-claro);   border-color: var(--acento); }
.caja.verde  { background: var(--verde-claro);    border-color: var(--verde); }
.caja.roja   { background: var(--rojo-claro);     border-color: var(--rojo); }
.caja.morada { background: var(--morado-claro);   border-color: var(--morado); }

table.t { width: 100%; border-collapse: collapse; margin: 8pt 0; font-size: 10pt; border-top: 1pt solid var(--texto); border-bottom: 1pt solid var(--texto); }
table.t.compacta { font-size: 8.5pt; }
table.t caption { caption-side: top; font-size: 9pt; color: var(--gris); padding-bottom: 3pt; }
table.t th { background: var(--primario); color: #fff; text-align: left; padding: 4pt 6pt; border-bottom: 0.6pt solid var(--texto); }
table.t td { padding: 3pt 6pt; vertical-align: top; }
table.t tbody tr:nth-child(even) td { background: var(--primario-claro); }
table.t tr { break-inside: avoid; }
table.t tr.total td { background: var(--acento-claro); font-weight: bold; border-top: 0.6pt solid var(--texto); }
table.t .num { text-align: right; white-space: nowrap; }
table.t td code { font-size: 8.5pt; }
tr.ok td  { background: var(--verde-claro) !important; }  tr.ok td:first-child  { color: var(--verde); font-weight: bold; }
tr.adv td { background: var(--acento-claro) !important; } tr.adv td:first-child { color: #9A6B00; font-weight: bold; }
tr.mal td { background: var(--rojo-claro) !important; }   tr.mal td:first-child  { color: var(--rojo); font-weight: bold; }
.nota { font-size: 8.5pt; color: var(--gris); }
.referencias li { font-size: 9.5pt; margin-bottom: 3pt; }
</style>
</head>
<body>

<section class="portada">
  <hr>
  <div class="org">{{ORG_MAYUSCULAS}} | {{AREA}}</div>
  <h1>{{TIPO_DOC}}<br>{{OBJETO}}</h1>
  <div class="sub">{{SUBTITULO_LINEA_1}}<br>{{SUBTITULO_LINEA_2}}</div>
  <div class="regla-acento"></div>
  <table class="ficha-portada">
    <tr><td>Objeto de prueba:</td><td>{{ARCHIVO_Y_FUNCION}}</td></tr>
    <tr><td>Versión probada:</td><td>{{COMMIT_O_VERSION}}</td></tr>
    <tr><td>Nivel / tipo:</td><td>{{NIVEL}} — {{TIPO}}</td></tr>
    <tr><td>Técnicas:</td><td>{{LISTA_CORTA_DE_TECNICAS}}</td></tr>
    <tr><td>Resultado:</td><td>{{N_PASAN}} de {{N_TOTAL}} pruebas pasan</td></tr>
    <tr><td>Fecha:</td><td>{{FECHA_LARGA}}</td></tr>
  </table>
  <hr>
</section>

<nav class="indice">
  <h2>Índice</h2>
  <ol id="indice"><!-- lo llena el script al final del body --></ol>
</nav>

<main>
  <h2 id="ficha">Ficha del reporte</h2>
  <!-- secciones según reporte-contenido.md -->
</main>

<section class="apendices">
  <h2 id="referencias">Referencias</h2>
  <ol class="referencias">
    <li>ISTQB, <i>Certified Tester Foundation Level Syllabus</i>, v4.0.1, 2024.</li>
  </ol>
</section>

<script>
/* Índice generado desde los h2/h3 para que nunca se desfase de la numeración CSS. Chrome lo ejecuta antes de imprimir. */
(() => {
  const toc = document.getElementById('indice'); let n = 0, k = 0, ap = false, sub = null;
  document.querySelectorAll('main h2, main h3, .apendices h2').forEach((h, i) => {
    if (!h.id) h.id = 'sec-' + i;
    if (h.closest('.apendices') && !ap) { ap = true; n = 0; }
    const li = document.createElement('li'), a = document.createElement('a');
    a.href = '#' + h.id;
    if (h.tagName === 'H2') {
      n++; k = 0;
      a.textContent = (ap ? String.fromCharCode(64 + n) : n) + '. ' + h.textContent;
      li.append(a); toc.append(li); sub = document.createElement('ol'); li.append(sub);
    } else {
      k++; a.textContent = n + '.' + k + ' ' + h.textContent; li.append(a); sub.append(li);
    }
  });
})();
</script>
</body>
</html>
```

## 9. Componentes

**Ficha (tabla de dos columnas, primera sección):**

```html
<table class="t">
  <thead><tr><th style="width:30%">Campo</th><th>Valor</th></tr></thead>
  <tbody>
    <tr><td>Objeto de prueba</td><td><code>src/envios.py</code> — <code>costo_envio(peso_kg, express)</code></td></tr>
    <tr><td>Base de prueba</td><td>Historia US-310, criterios de aceptación 1-5</td></tr>
  </tbody>
</table>
```

**Definición citada + justificación (par obligatorio por técnica):**

```html
<div class="caja azul">
  <p><b>Boundary Value Analysis (BVA), 3 valores.</b> Técnica que ejercita los bordes de particiones ordenadas; en la variante de 3 valores cada frontera aporta tres ítems de cobertura: la frontera y sus dos vecinos [1, §4.2.2].</p>
</div>
<div class="caja morada">
  <p><b>Se eligió porque la regla <code>peso_kg &lt;= 5</code> (envios.py:22) define una frontera de cobro.</b> Un operador mal escrito (<code>==</code> en lugar de <code>&lt;=</code>) pasa con 2 valores (5, 5.01) y falla con el vecino 4.99 [1, §4.2.2].</p>
</div>
```

**Tabla de derivación con total:**

```html
<table class="t">
  <caption>Particiones de <code>peso_kg</code></caption>
  <thead><tr><th>ID</th><th>Partición</th><th>Valor</th><th>Esperado</th><th>Test</th></tr></thead>
  <tbody>
    <tr><td>EP-01</td><td>inválida: peso_kg &lt;= 0</td><td class="num">-1</td><td>ValueError</td><td><code>test_envios.py:14</code></td></tr>
    <tr class="total"><td colspan="4">Cobertura EP: 6 de 6 particiones</td><td class="num">100%</td></tr>
  </tbody>
</table>
```

**Semáforo de decisión:**

```html
<table class="t">
  <thead><tr><th style="width:28%">Resultado</th><th>Criterio</th></tr></thead>
  <tbody>
    <tr class="ok"><td>Liberar</td><td>…</td></tr>
    <tr class="adv"><td>Liberar con condiciones</td><td>…</td></tr>
    <tr class="mal"><td>No liberar</td><td>…</td></tr>
  </tbody>
</table>
```

**Salida real del runner:** `<pre class="salida">` (puede partirse entre páginas, 7.5pt). Correr con el modo verboso del runner y rutas relativas (`uv run pytest -v --tb=short`, `npx vitest run --reporter=verbose`) y guardar en archivo (`… | tee salida.txt`). Insertar con escape, nunca a mano: `python3 -c "import html,sys;print(html.escape(open(sys.argv[1]).read()))" salida.txt` y pegar el resultado en el `<pre>`.

**Cita en el texto:** `[n, §x.y.z]` con `n` = número en la lista de referencias del apéndice. Solo se cita sección cuando está verificada en `reporte-contenido.md`.

## 10. Render

```bash
bash <ruta-de-la-skill>/scripts/html_a_pdf.sh reportes-pruebas/AAAA-MM-DD-<objeto>/reporte.html
```

Genera `reporte.pdf` junto al HTML. El script busca Chrome, Chromium, Edge o Brave (o la ruta en `$CHROME`) y aborta con mensaje si no encuentra ninguno. Verificación mínima después de renderizar:

```bash
pdfinfo reporte.pdf | grep Pages                                  # número de páginas
pdftoppm -png -r 60 -f 1 -l 1 -singlefile reporte.pdf /tmp/portada  # → /tmp/portada.png
pdftoppm -png -r 60 -f 3 -l 3 -singlefile reporte.pdf /tmp/pag3     # una página con tabla o caja
```

Abrir los PNG con la herramienta de lectura de imágenes y confirmar: portada sin header, colores de encabezado de tabla y cajas presentes, índice lleno. Para una tabla larga, renderizar la segunda página que ocupa y confirmar que repite el encabezado.
