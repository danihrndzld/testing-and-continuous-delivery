# Contenido del reporte de pruebas

Qué va dentro del PDF y cómo se fundamenta cada decisión. La forma visual está en `reporte-diseno.md`. Las secciones del CTFL citadas aquí se verificaron contra el syllabus oficial **ISTQB CTFL v4.0.1 (2024-09-15)**; no hace falta volver a consultarlo.

## 1. Entregables obligatorios

Cada vez que la skill trabaja sobre un escenario concreto (código, función, endpoint, historia de usuario, spec), entrega **siempre** las dos piezas:

1. **Pruebas implementadas y ejecutadas** en el framework del proyecto (pytest, Jest/Vitest, JUnit, Go `testing`, etc.). Si el proyecto no tiene framework, usar el estándar del lenguaje (`uv run pytest` en Python, `node --test` o `bun test` en JS). Las pruebas se corren; un reporte con pruebas sin correr no se entrega.
2. **Reporte** en `reportes-pruebas/AAAA-MM-DD-<objeto>/` en la raíz del proyecto probado. El agente escribe solo `reporte.json` (el criterio: riesgos, por qué de cada técnica, derivaciones, defectos); `scripts/armar_reporte.py` lo combina con el JUnit XML y la cobertura que produjo el runner y genera `reporte.html` + `reporte.pdf`. Los conteos, resultados y porcentajes del PDF salen de esos artefactos, nunca se escriben a mano.

Las dos piezas se referencian entre sí mediante **IDs de caso de prueba**:

| Prefijo | Técnica |
|---|---|
| `EP` | Equivalence Partitioning |
| `BVA` | Boundary Value Analysis |
| `DT` | Decision Table (`DT-R3` = regla 3) |
| `ST` | State Transition (`ST-T4` = transición 4, `ST-I2` = inválida 2) |
| `PW` | Pairwise / combinatoria |
| `BR` | Branch testing (casos agregados para cerrar ramas) |
| `MCDC` | Modified Condition/Decision Coverage |
| `EG` | Error Guessing / fault attack |
| `CL` | Checklist-based |
| `AC` | Criterio de aceptación / ATDD |
| `PBT` | Property-based testing |

**Todo test lleva ID**; el script rechaza tests sin ID, IDs del JSON que no aparecen en el JUnit XML y `archivo:línea` cuya línea no contiene el ID. El ID va en el nombre o la descripción del test (`test_bva_03_peso_5_es_tarifa_base`, `it('BVA-03 peso 5 kg es tarifa base')`, o `pytest.param(..., id='BVA-03-peso-5')`). El reporte cita `archivo:línea` de cada caso: en tests parametrizados, la línea de la fila (`pytest.param`, elemento de `it.each`) donde están sus datos; la función que hace la aserción se cita una vez en la tabla de casos de la técnica.

## 2. Flujo de trabajo

Sigue las actividades de prueba del CTFL [ctfl, §1.4.1]: análisis → diseño → implementación → ejecución → cierre.

1. **Análisis.** Leer la base de prueba (spec, historia, código). Extraer las **condiciones de prueba**: cada regla, rango, combinación o estado que el objeto debe respetar, con su ubicación (`archivo:línea` o criterio de aceptación).
2. **Oráculo.** Decidir de dónde sale cada resultado esperado antes de escribir una sola prueba. Fuentes válidas: **spec** (requisito, historia, criterio de aceptación, docstring o comentario que describe la intención, documentación de API), **usuario** (se le preguntan los esperados) o **supuestos** declarados (S1, S2… con la lista de casos que dependen de cada uno). El código bajo prueba **nunca** es oráculo: un esperado deducido de la implementación solo confirma lo que el código ya hace, defecto incluido. Sin spec, preguntar al usuario los esperados de las condiciones de riesgo alto y declarar supuestos para el resto. Si hay spec pero es ambigua en un punto: riesgo alto → preguntar al usuario; riesgo bajo o medio → declarar un supuesto. El script exige `base_de_prueba.tipo`, rechaza `supuestos` sin lista y valida que los casos de cada supuesto existan.
3. **Riesgo de producto.** Para cada condición estimar probabilidad e impacto (1-3). Nivel = probabilidad × impacto [ctfl, §5.2.3]. El nivel decide el rigor:

   | Nivel | Riesgo | Rigor exigido |
   |---|---|---|
   | 1-2 | bajo | variante base (EP, BVA de 2 valores, valid transitions, statement) |
   | 3-4 | medio | variante base + error guessing sobre la condición + branch coverage |
   | 6-9 | alto | variante fuerte (BVA de 3 valores, tabla completa, all transitions, MC/DC en decisiones compuestas) |
4. **Selección de técnica.** Recorrer la matriz de la sección 3 por cada condición. Anotar también las técnicas descartadas y por qué.
5. **Diseño.** Derivar ítems de cobertura (particiones, fronteras, reglas, transiciones) en tablas. Asignar IDs.
6. **Implementación.** Escribir las pruebas con los IDs. Se permite el mínimo de configuración para que las pruebas importen el código (por ejemplo `[tool.pytest.ini_options] pythonpath = ["src"]` y las dependencias de desarrollo); cualquier archivo del proyecto que se toque se lista en la ficha. Una aserción con resultado esperado concreto por caso; sin `assert True`, sin `try/except` que trague la falla. Casos de la misma técnica pueden ir parametrizados (`@pytest.mark.parametrize`, `it.each`) manteniendo el ID por fila.
7. **Ejecución.** Correr la suite completa emitiendo JUnit XML y cobertura en JSON dentro de la carpeta del reporte:

   | Ecosistema | Comando |
   |---|---|
   | Python | `uv run pytest --junitxml=$R/junit.xml --cov=src --cov-branch --cov-report=json:$R/coverage.json` |
   | Vitest | `npx vitest run --reporter=junit --outputFile=$R/junit.xml --coverage --coverage.reporter=json-summary` (copiar `coverage/coverage-summary.json` a `$R`) |
   | Jest | `npx jest --reporters=default --reporters=jest-junit --coverage --coverageReporters=json-summary` (`JEST_JUNIT_OUTPUT_FILE=$R/junit.xml`) |
   | Otros (JUnit, Go `gotestsum --junitfile`) | JUnit XML del runner; cobertura en coverage.py JSON o istanbul json-summary, o sin `--cobertura` |

   Si no hay herramienta de cobertura, se omite `--cobertura` y el reporte lo dice.
8. **Reporte.** Escribir `$R/reporte.json` (esquema en la sección 5) y correr:

   ```bash
   uv run <skill>/scripts/armar_reporte.py $R/reporte.json --junit $R/junit.xml --cobertura $R/coverage.json --raiz .
   ```

   Si la validación falla, corregir lo que lista (tests sin ID, IDs que no existen, defectos sin documentar) y volver a correr. `--solo-validar` revisa sin renderizar.
9. **Revisión visual.** `pdftoppm -png -r 60 -f 1 -l 2 $R/reporte.pdf <directorio-temporal>/pag` y abrir los PNG: portada sin header, índice con números de página, colores presentes.

Severidad de defectos: **alta** = resultado incorrecto en una regla de negocio, dinero, datos o seguridad, sin rodeo; **media** = resultado incorrecto con rodeo o en un caso poco frecuente; **baja** = mensaje, formato o comportamiento cosmético. Los umbrales del semáforo usan esta escala.

Una prueba que falla porque el código tiene un defecto **se queda fallando** y se documenta como defecto (sección 11 del reporte). No se ajusta el esperado para que pase.

## 3. Matriz de selección de técnica

La técnica la decide una **propiedad observable de la base de prueba**, no la costumbre. El CTFL clasifica las técnicas en black-box, white-box y experience-based, y establece que las experience-based complementan a las otras dos [ctfl, §4.1]. El análisis de riesgo de producto determina qué técnicas se emplean y qué cobertura se busca [ctfl, §5.2.3].

| Si la base de prueba tiene… | Técnica | Referencia | Ítem de cobertura | Variante fuerte (riesgo alto) |
|---|---|---|---|---|
| Un dominio de entrada o salida que se procesa por clases (válidas e inválidas) | Equivalence Partitioning | [ctfl, §4.2.1]; [myers, cap. 4]; [copeland] | partición | Each Choice con varios parámetros [ammann] |
| Particiones **ordenadas** con frontera (rangos, montos, fechas, longitudes) | Boundary Value Analysis | [ctfl, §4.2.2]; [myers]; [koomen] | frontera (2 valores) o frontera + vecinos (3 valores) | 3 valores [koomen] |
| Varias condiciones que **combinadas** producen acciones distintas (reglas de negocio) | Decision Table Testing | [ctfl, §4.2.3]; [copeland]; [beizer] | columna (regla) factible | tabla completa sin minimizar |
| Comportamiento que depende de **lo que pasó antes** (estados, ciclo de vida, flujos) | State Transition Testing | [ctfl, §4.2.4]; [beizer] | estado / transición válida / toda transición | all transitions, una inválida por test |
| Muchos parámetros independientes con explosión combinatoria | Pairwise / combinatorial | [29119-4]; [kuhn] | par de valores | t-way con t = 3 |
| Código disponible y se necesita medir qué se ejecutó | Statement testing | [ctfl, §4.3.1] | sentencia ejecutable | — |
| Decisiones (`if`, `switch`, bucles) en el código | Branch testing | [ctfl, §4.3.2] | rama | MC/DC en decisiones compuestas críticas [ammann] |
| Historial de fallas conocido, errores típicos del lenguaje o dominio | Error Guessing / fault attacks | [ctfl, §4.4.1]; [whittaker] | error anticipado | lista de ataques documentada |
| Especificación delgada o presión de tiempo | Exploratory testing (con charter) | [ctfl, §4.4.2]; [hendrickson] | objetivo del charter | sesión con time box y debriefing |
| Estándar externo con criterios verificables (OWASP, accesibilidad, convenciones) | Checklist-based | [ctfl, §4.4.3]; [brykczynski] | ítem de checklist | checklist actualizado por análisis de defectos |
| Historia de usuario con criterios de aceptación | ATDD / Given-When-Then | [ctfl, §4.5.2, §4.5.3]; [adzic]; [gartner] | criterio de aceptación | un test por criterio + negativos |
| Invariante que debe valer para todo un dominio grande | Property-based testing | [claessen] | propiedad | generador con casos frontera sesgados |
| Duda sobre la fuerza de la suite misma | Mutation testing | [demillo] | mutante | mutation score por módulo |

Notas de aplicación, todas desde el syllabus salvo indicación:

- **EP.** Las particiones no se solapan y no son vacías; se identifican para entradas, salidas, configuración, valores internos, tiempo e interfaces. Cobertura = particiones ejercitadas ÷ identificadas, **incluidas las inválidas**. Con varios parámetros, el criterio mínimo es *Each Choice* (cada partición de cada parámetro al menos una vez), que no cubre combinaciones [ctfl, §4.2.1].
- **BVA.** Solo aplica a particiones ordenadas. Con 2 valores se prueba la frontera y su vecino en la partición adyacente (Craig 2002, Myers 2011); con 3 valores, la frontera y ambos vecinos (Koomen 2006). El ejemplo del syllabus: `if (x ≤ 10)` implementado como `if (x = 10)` no lo detecta 2-value BVA (10, 11) y sí lo detecta 3-value BVA con x = 9 [ctfl, §4.2.2]. Elegir 3 valores cuando la frontera toca dinero, permisos o seguridad. Entre particiones adyacentes los vecinos se repiten (el vecino superior de 12 es la frontera 13): se prueba cada **valor** una sola vez y la cobertura se reporta como ítems de cobertura ejercitados ÷ identificados, aclarando cuántos valores distintos los cubrieron.
- **Tabla de decisión.** Notación: T, F, "–" (irrelevante), N/A (infactible); en acciones, X ocurre y vacío no. Cobertura = columnas factibles ejercitadas ÷ factibles. Su fuerza es exponer combinaciones olvidadas y contradicciones en los requisitos; con muchas condiciones el número de reglas crece exponencialmente y se usa tabla minimizada o enfoque basado en riesgo [ctfl, §4.2.3].
- **Transición de estados.** Tres criterios de fuerza creciente: all states < valid transitions (0-switch) < all transitions. All transitions incluye intentar cada transición inválida, **una inválida por caso** para evitar enmascaramiento de defectos, y es el mínimo para software de misión o seguridad crítica [ctfl, §4.2.4]. La tabla de estados del reporte muestra las celdas vacías (inválidas) explícitamente.
- **Statement / branch.** 100% de sentencias no garantiza probar la lógica de decisión; branch coverage subsume statement coverage, nunca al revés [ctfl, §4.3.1, §4.3.2]. Ninguna técnica white-box detecta **omisiones**: si el código no implementa un requisito, no hay rama que ejecutar (Watson 1996) [ctfl, §4.3.3]. Por eso white-box se usa para medir y cerrar huecos de las black-box, no para reemplazarlas.
- **MC/DC.** Cada condición atómica de una decisión debe mostrar que afecta el resultado de forma independiente [ammann]. Aplica a decisiones compuestas (`a and (b or c)`) con nivel de riesgo ≥ 6; está fuera del CTFL Foundation [ctfl, §4.3].
- **Error guessing.** Categorías del syllabus para construir la lista de ataques: entrada (valor correcto rechazado, parámetro faltante), salida (formato, resultado), lógica (caso faltante, operador equivocado), cálculo (operando incorrecto), interfaces (tipos incompatibles), datos (inicialización, tipo) [ctfl, §4.4.1]. Frontera con EP: el representante de cada partición inválida cuenta como EP (un valor por partición); los valores adicionales de esa misma partición elegidos por ser fallas típicas del lenguaje (`None`, `True` como entero, `"30"` como texto) cuentan como EG. Ataques típicos: `None`/`null`, cadena vacía, Unicode, cero como divisor, negativos, overflow, zona horaria, redondeo de moneda, concurrencia.
- **Exploratorio.** Sesión con time box guiada por un charter con objetivos; útil con especificación pobre y como complemento de técnicas formales [ctfl, §4.4.2]. En este entregable, cada hallazgo exploratorio se convierte en un test automatizado `EG-n` y el charter se documenta en el reporte.
- **Checklist.** Los ítems se formulan como preguntas verificables por separado; no deben contener lo que ya se chequea automáticamente ni criterios de entrada/salida (Brykczynski 1999) [ctfl, §4.4.3].
- **Pairwise.** La mayoría de las fallas en los sistemas estudiados se disparan por la interacción de uno o dos parámetros [kuhn]; por eso cubrir todos los pares reduce combinaciones de forma drástica con poca pérdida. Técnica de ISO/IEC/IEEE 29119-4 [29119-4], fuera del CTFL Foundation.
- **Property-based y mutation.** Fuera del syllabus CTFL. Property-based genera entradas aleatorias contra una propiedad (QuickCheck [claessen]); mutation testing inserta defectos pequeños para medir si la suite los detecta [demillo]. Se reportan como técnicas complementarias, nunca como sustituto de EP/BVA.

**Nivel y tipo.** Declarar el nivel (componente, integración de componentes, sistema, integración de sistemas, aceptación) [ctfl, §2.2.1] y el tipo (funcional, no funcional, caja negra, caja blanca) [ctfl, §2.2.2]. Justificar la ubicación en la pirámide de pruebas [ctfl, §5.1.6] y el cuadrante [ctfl, §5.1.7].

## 4. Estructura obligatoria del reporte

Basada en el contenido de un *test completion report* [ctfl, §5.3.2] y en las plantillas de ISO/IEC/IEEE 29119-3 [29119-3]. El script genera estas secciones en este orden a partir de `reporte.json`; esta lista dice qué debe aportar el agente en cada una.

**Tamaño según riesgo.** Si alguna condición tiene nivel ≥ 6, el reporte sale en modo **completo** (las 13 secciones, una subsección de 5 partes por técnica). Si todas son de nivel ≤ 4, sale en modo **corto** (3-6 páginas): las técnicas van en una sola tabla y se omiten objeto, estrategia y riesgo residual salvo que el JSON los traiga. `"modo"` en el JSON fuerza uno u otro.

**Portada.** Objeto, versión (commit corto), nivel y tipo, técnicas, resultado `N de M pasan`, fecha.

1. **Ficha del reporte.** Tabla campo/valor: objeto de prueba (`archivo` + función/endpoint), base de prueba, versión/commit, lenguaje y framework con la versión **con la que corrieron las pruebas** (la que imprime el runner, no la del sistema), comando de ejecución, nivel, tipo, autor, fecha.

   Marcadores de portada y header sin dato del proyecto: `{{ORG}}` = nombre del repositorio o del paquete; `{{AREA}}` = "Aseguramiento de calidad"; `{{TIPO_DOC}}` = "Reporte de Pruebas"; `{{TITULO_CORTO}}` = objeto y año; autor = el usuario de `git config user.name` o "Claude Code".
2. **Resumen.** Caja verde (todo pasa y criterios de salida cumplidos) o roja (defectos o criterios incumplidos) con: casos diseñados, casos que pasan/fallan, defectos encontrados, cobertura de cada técnica y cobertura estructural. Después, un párrafo de 3-5 oraciones con datos.
3. **Objeto y base de prueba.** Qué hace el objeto, de dónde salen los esperados (cita literal de la spec o de la línea de código), supuestos tomados donde la spec calla. Cada supuesto queda numerado (S1, S2…) porque un supuesto equivocado invalida los esperados que dependen de él.
4. **Análisis de riesgo de producto.** Tabla: condición, riesgo, probabilidad (1-3), impacto (1-3), nivel, técnica y cobertura que exige [ctfl, §5.2.3].
5. **Estrategia.** Nivel, tipo, ubicación en pirámide/cuadrante, criterios de salida en caja dorada (por ejemplo: 100% de particiones, 100% de fronteras con 3 valores, ≥ 90% de ramas, 0 defectos de severidad alta abiertos) [ctfl, §5.1.3].
6. **Técnicas aplicadas.** Un `h3` por técnica de diseño que produjo casos, con cinco partes fijas en este orden; cada parte puede ser un `h4` o un párrafo con su nombre en negrita. Statement y branch coverage van aquí solo si se agregaron casos `BR-n` para cerrar ramas; si solo se midieron, van en la sección 10.
   1. *Definición* — caja azul, cita textual parafraseada con `[n, §x.y.z]`.
   2. *Por qué aplica aquí* — caja morada: la propiedad concreta del escenario que disparó la técnica, con `archivo:línea` o criterio citado, y el nivel de riesgo que fijó la variante.
   3. *Derivación* — tabla de particiones, fronteras, reglas (columnas R1…Rn con T/F/–) o estados (tabla de estados con celdas inválidas vacías). Para estados se agrega el diagrama como tabla o SVG inline.
   4. *Casos* — tabla ID, entrada, esperado, `archivo:línea`, resultado (pasa/falla).
   5. *Cobertura y límites* — fórmula con números (`6 de 6 particiones = 100%`) y qué defecto **no** puede encontrar esta técnica en este escenario.
7. **Técnicas consideradas y descartadas.** Tabla: técnica, por qué no aplica o no compensa aquí (por ejemplo: "State Transition: `costo_envio` es pura, no guarda estado entre llamadas"). Esta sección demuestra que la selección fue deliberada.
8. **Trazabilidad.** Tabla compacta: condición/requisito → riesgo → técnica → IDs → `archivo:línea` → resultado. Permite verificar que cada requisito tiene casos y evaluar el riesgo residual [ctfl, §1.4.4].
9. **Ejecución.** Generada por el script desde el JUnit XML: comando, versiones, duración, conteos por técnica y el mensaje de cada caso que falla.
10. **Cobertura estructural.** Generada desde el JSON de cobertura: sentencias y ramas por archivo. El agente agrega en `cobertura_nota` para cada rama no cubierta: si es alcanzable, un caso `BR-n` que la cubra; si no, por qué.
11. **Defectos encontrados.** Una caja roja por defecto: ID del caso que lo expuso, entrada, esperado vs. obtenido, ubicación probable, severidad. Distinguir error (acción humana), defecto (en el código) y falla (lo observado) [ctfl, §1.2.3]. Si no hubo, decirlo con el número de casos que lo respaldan, recordando que las pruebas muestran presencia de defectos, no su ausencia [ctfl, §1.3].
12. **Riesgo residual y recomendaciones.** Lo que quedó sin probar y por qué (fuera de alcance, sin herramienta, no determinista), riesgos no mitigados, siguientes pruebas recomendadas con técnica y nivel.
13. **Criterio de decisión.** Semáforo (liberar / liberar con condiciones / no liberar) con umbrales numéricos y una caja verde o roja con la recomendación.

**Apéndice A — Referencias.** Generada por el script: solo las fuentes citadas, numeradas por orden de primera cita, desde la sección 7 de este archivo.

**Apéndice B — Reproducción.** Comandos para instalar dependencias, correr la suite, medir cobertura y regenerar el PDF.

## 5. Esquema de `reporte.json`

`<skill>` en los comandos = ruta absoluta del directorio que contiene `SKILL.md` (por ejemplo `~/.claude/skills/testing-and-continuous-delivery`); en `reproduccion` se escribe la ruta real, no el marcador. `"modo"` es opcional (`"corto"` o `"completo"`); sin él, el script decide por riesgo. `portada.org`, `portada.titulo_corto` y `portada.tipo_doc` llenan el header de cada página. El script agrega solo a la ficha las filas Base de prueba, Comando, Versiones y Modo: no repetirlas en `ficha`. `criterios_salida` se imprime tal cual; cumplirlos lo juzga el agente en `decision`.

Los campos de texto aceptan HTML (`<p>`, `<b>`, `<code>`, `<ul>`, tablas `<table class="t">` para derivaciones). Las citas se escriben con clave: `[ctfl, §4.2.2]`, `[myers]`, `[kuhn]`; el script las numera. Claves disponibles en la sección 7.

```json
{
  "portada": {
    "org": "demo-envios", "area": "Aseguramiento de calidad", "tipo_doc": "Reporte de Pruebas",
    "objeto": "costo_envio", "objeto_detalle": "src/envios.py — costo_envio()",
    "version": "a1b2c3d", "titulo_corto": "costo_envio — 2026",
    "subtitulo": ["BVA de 3 valores expuso un defecto en 5 kg", "17 de 18 pruebas pasan"],
    "fecha": "5 de octubre de 2026"
  },
  "ficha": [["Objeto de prueba", "<code>src/envios.py</code> — <code>costo_envio(peso_kg, express)</code>"],
            ["Nivel / tipo", "Componente — funcional, caja negra"], ["Autor", "…"]],
  "base_de_prueba": {"tipo": "spec", "fuente": "Historia US-310, criterios 1-5"},
  "supuestos": [{"id": "S1", "texto": "El peso se redondea hacia arriba al décimo", "casos": ["BVA-04"]}],
  "resumen": "<p>3-5 oraciones con datos.</p>",
  "objeto": "<p>Qué hace el objeto y de dónde salen los esperados.</p>",
  "riesgos": [{"id": "C1", "condicion": "Tarifa por tramo de peso (<code>envios.py:22</code>)",
               "riesgo": "Cobro incorrecto en la frontera", "prob": 2, "impacto": 3,
               "exige": "BVA de 3 valores, 100%"}],
  "estrategia": "<p>Nivel, tipo, pirámide y cuadrante con citas.</p>",
  "criterios_salida": ["100% de particiones EP", "0 defectos de severidad alta abiertos"],
  "tecnicas": [{
    "nombre": "Boundary Value Analysis (3 valores)", "condiciones": ["C1"],
    "definicion": "<p><b>…</b> [ctfl, §4.2.2]</p>",
    "por_que": "<p><b>La regla <code>peso_kg &lt;= 5</code> (envios.py:22) …</b></p>",
    "derivacion": "<table class=\"t\">…</table>",
    "casos": [{"id": "BVA-01", "entrada": "4.9", "esperado": "Q35.00", "ubicacion": "tests/test_envios.py:14"}],
    "cobertura": "<p>Ítems: 6 de 6 = 100%, cubiertos con 5 valores distintos.</p>",
    "limites": "<p>No detecta …</p>"
  }],
  "descartadas": [["State Transition", "<code>costo_envio</code> es pura, no guarda estado entre llamadas"]],
  "cobertura_nota": "<p>Opcional: ramas no cubiertas y por qué.</p>",
  "defectos": [{"id": "D-01", "caso": "BVA-03", "entrada": "5.0", "esperado": "Q35.00", "obtenido": "Q50.00",
                "ubicacion": "src/envios.py:22", "severidad": "alta", "analisis": "<p>Error → defecto → falla …</p>"}],
  "riesgo_residual": "<p>Lo no probado y por qué; siguientes pruebas.</p>",
  "decision": {"veredicto": "mal", "texto": "<p><b>No liberar: …</b></p>",
               "semaforo": [["Liberar", "…"], ["Liberar con condiciones", "…"], ["No liberar", "…"]]},
  "entorno": {"comando": "uv run pytest --junitxml=… --cov=src --cov-branch", "versiones": "Python 3.13.13, pytest 9.1.1"},
  "reproduccion": ["uv sync", "uv run pytest …", "uv run <skill>/scripts/armar_reporte.py …"]
}
```

Reglas que el script valida: `base_de_prueba.tipo` ∈ {spec, usuario, supuestos}; `prob` e `impacto` de 1 a 3; cada ID de `casos` existe una sola vez en el JUnit XML y en su `ubicacion`; cada test del JUnit tiene ID documentado; cada caso que falla está en `defectos` y cada defecto apunta a un caso que falla; `severidad` ∈ {alta, media, baja}. `semaforo` va en orden verde, dorado, rojo; `veredicto` ∈ {ok, adv, mal}.

## 6. Reglas de redacción

- Español. Los nombres de técnicas y de criterios de cobertura van en inglés como en el glosario ISTQB (Equivalence Partitioning, branch coverage), con traducción la primera vez si ayuda.
- Cada oración lleva un dato verificable: un número, un ID, un `archivo:línea`, una sección citada. Una oración que se puede borrar sin perder información se borra.
- Títulos de sección con dato cuando el contenido lo permite ("BVA de 3 valores: 12 casos sobre 4 fronteras").
- Pasado para lo que ya se hizo: "Se ejecutaron 31 casos; 30 pasan y BVA-07 falla en `envios.py:22`".
- Nada de relleno: sin "es importante destacar", sin adjetivos de valor ("robusto", "exhaustivo"), sin conclusiones genéricas, sin emoji.
- Citas: `[clave, §x.y.z]` solo con las secciones listadas en la sección 7. Libros sin capítulo verificado se citan sin capítulo. Nunca se inventan páginas.
- Profundidad: en modo completo la sección de técnicas es el núcleo del reporte. Un escenario con 3 técnicas produce al menos 3 subsecciones completas con sus 5 partes; no se resume en una tabla.

## 7. Bibliografía disponible para el reporte

El script lee esta lista: cada línea `[clave] referencia`. En el reporte aparecen solo las citadas, numeradas por orden de primera cita.

[ctfl] ISTQB, *Certified Tester Foundation Level Syllabus*, v4.0.1, International Software Testing Qualifications Board, 2024. Secciones verificadas: §1.2.3 errores, defectos, fallas; §1.3 principios; §1.4.1 actividades; §1.4.4 trazabilidad; §2.2.1 niveles; §2.2.2 tipos; §2.2.3 confirmación y regresión; §4.1 panorama de técnicas; §4.2.1 EP; §4.2.2 BVA; §4.2.3 tablas de decisión; §4.2.4 transición de estados; §4.3.1 statement; §4.3.2 branch; §4.3.3 valor del white-box; §4.4.1 error guessing; §4.4.2 exploratorio; §4.4.3 checklist; §4.5.2 criterios de aceptación; §4.5.3 ATDD; §5.1.3 criterios de entrada y salida; §5.1.5 priorización; §5.1.6 pirámide; §5.1.7 cuadrantes; §5.2.3 análisis de riesgo de producto; §5.3.2 reportes de prueba.
[29119-4] ISO/IEC/IEEE 29119-4:2021, *Software and systems engineering — Software testing — Part 4: Test techniques*.
[myers] G. J. Myers, C. Sandler, and T. Badgett, *The Art of Software Testing*, 3rd ed. Hoboken, NJ, USA: John Wiley & Sons, 2011.
[beizer] B. Beizer, *Software Testing Techniques*, 2nd ed. New York, NY, USA: Van Nostrand Reinhold, 1990.
[copeland] L. Copeland, *A Practitioner's Guide to Software Test Design*. Norwood, MA, USA: Artech House, 2004.
[koomen] T. Koomen, L. van der Aalst, B. Broekman, and M. Vroon, *TMap Next for Result-Driven Testing*. 's-Hertogenbosch, The Netherlands: UTN Publishers, 2006.
[craig] R. D. Craig and S. P. Jaskiel, *Systematic Software Testing*. Norwood, MA, USA: Artech House, 2002.
[ammann] P. Ammann and J. Offutt, *Introduction to Software Testing*, 2nd ed. Cambridge, UK: Cambridge University Press, 2016.
[jorgensen] P. C. Jorgensen, *Software Testing: A Craftsman's Approach*, 4th ed. Boca Raton, FL, USA: CRC Press, 2014.
[forgacs] I. Forgács and A. Kovács, *Practical Test Design*. Swindon, UK: BCS, 2019.
[watson] A. H. Watson, D. R. Wallace, and T. J. McCabe, *Structured Testing: A Testing Methodology Using the Cyclomatic Complexity Metric*, NIST Special Publication 500-235, 1996.
[whittaker] J. A. Whittaker, *How to Break Software: A Practical Guide to Testing*. Boston, MA, USA: Addison-Wesley, 2002.
[hendrickson] E. Hendrickson, *Explore It!: Reduce Risk and Increase Confidence with Exploratory Testing*. Raleigh, NC, USA: The Pragmatic Programmers, 2013.
[adzic] G. Adzic, *Bridging the Communication Gap: Specification by Example and Agile Acceptance Testing*. London, UK: Neuri, 2009.
[gartner] M. Gärtner, *ATDD by Example: A Practical Guide to Acceptance Test-Driven Development*. Boston, MA, USA: Addison-Wesley, 2012.
[veenendaal] E. van Veenendaal, Ed., *Practical Risk-Based Testing: The PRISMA Approach*. The Netherlands: UTN Publishers, 2012.
[brykczynski] B. Brykczynski, "A survey of software inspection checklists," *ACM SIGSOFT Software Engineering Notes*, vol. 24, no. 1, pp. 82–89, 1999.
[kuhn] D. R. Kuhn, D. R. Wallace, and A. M. Gallo, "Software fault interactions and implications for software testing," *IEEE Transactions on Software Engineering*, vol. 30, no. 6, pp. 418–421, 2004.
[claessen] K. Claessen and J. Hughes, "QuickCheck: A lightweight tool for random testing of Haskell programs," in *Proc. ACM SIGPLAN International Conference on Functional Programming (ICFP)*, 2000, pp. 268–279.
[demillo] R. A. DeMillo, R. J. Lipton, and F. G. Sayward, "Hints on test data selection: Help for the practicing programmer," *Computer*, vol. 11, no. 4, pp. 34–41, 1978.
[crispin] L. Crispin and J. Gregory, *Agile Testing: A Practical Guide for Testers and Agile Teams*. Boston, MA, USA: Addison-Wesley, 2009.
[beck] K. Beck, *Test-Driven Development: By Example*. Boston, MA, USA: Addison-Wesley, 2002.
[owasp] OWASP Foundation, *OWASP Top 10*, 2021.
[29119-3] ISO/IEC/IEEE 29119-3:2021, *Software and systems engineering — Software testing — Part 3: Test documentation*.

## 8. Checklist antes de entregar

El script ya verifica IDs, trazabilidad, conteos y defectos. Queda para el agente:

- [ ] Los esperados salen de la spec, del usuario o de supuestos declarados, nunca del código bajo prueba.
- [ ] Cada técnica tiene definición, por qué, derivación, cobertura y límites, con al menos una cita `[clave, §…]`.
- [ ] La sección de técnicas descartadas tiene al menos 2 filas.
- [ ] Los porcentajes de cobertura por técnica tienen numerador y denominador.
- [ ] Los defectos son pruebas que fallan, no esperados modificados.
- [ ] El PDF abre, la portada no tiene header y el índice tiene números de página.
- [ ] No se hizo commit de los entregables ni de archivos generados (`.coverage`, `__pycache__`) salvo que el usuario lo pida; `.coverage` se borra al terminar.
