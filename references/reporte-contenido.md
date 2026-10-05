# Contenido del reporte de pruebas

Qué va dentro del PDF y cómo se fundamenta cada decisión. La forma visual está en `reporte-diseno.md`. Las secciones del CTFL citadas aquí se verificaron contra el syllabus oficial **ISTQB CTFL v4.0.1 (2024-09-15)**; no hace falta volver a consultarlo.

## 1. Entregables obligatorios

Cada vez que la skill trabaja sobre un escenario concreto (código, función, endpoint, historia de usuario, spec), entrega **siempre** las dos piezas:

1. **Pruebas implementadas y ejecutadas** en el framework del proyecto (pytest, Jest/Vitest, JUnit, Go `testing`, etc.). Si el proyecto no tiene framework, usar el estándar del lenguaje (`uv run pytest` en Python, `node --test` o `bun test` en JS). Las pruebas se corren; un reporte con pruebas sin correr no se entrega.
2. **Reporte** `reportes-pruebas/AAAA-MM-DD-<objeto>/reporte.html` + `reporte.pdf` en la raíz del proyecto probado. El HTML se conserva como fuente, igual que un `.tex` junto a su PDF.

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

El ID va en el nombre o la descripción del test (`test_bva_03_peso_5_es_tarifa_base`, `it('BVA-03 peso 5 kg es tarifa base')`, o `pytest.param(..., id='BVA-03-peso-5')`). El reporte cita `archivo:línea` de cada caso: en tests parametrizados, la línea de la fila (`pytest.param`, elemento de `it.each`) donde están sus datos; la función que hace la aserción se cita una vez en la tabla de casos de la técnica.

## 2. Flujo de trabajo

Sigue las actividades de prueba del CTFL [1, §1.4.1]: análisis → diseño → implementación → ejecución → cierre.

1. **Análisis.** Leer la base de prueba (spec, historia, código). Extraer las **condiciones de prueba**: cada regla, rango, combinación o estado que el objeto debe respetar, con su ubicación (`archivo:línea` o criterio de aceptación).
2. **Riesgo de producto.** Para cada condición estimar probabilidad e impacto (1-3). Nivel = probabilidad × impacto [1, §5.2.3]. El nivel decide el rigor:

   | Nivel | Riesgo | Rigor exigido |
   |---|---|---|
   | 1-2 | bajo | variante base (EP, BVA de 2 valores, valid transitions, statement) |
   | 3-4 | medio | variante base + error guessing sobre la condición + branch coverage |
   | 6-9 | alto | variante fuerte (BVA de 3 valores, tabla completa, all transitions, MC/DC en decisiones compuestas) |
3. **Selección de técnica.** Recorrer la matriz de la sección 3 por cada condición. Anotar también las técnicas descartadas y por qué.
4. **Diseño.** Derivar ítems de cobertura (particiones, fronteras, reglas, transiciones) en tablas. Asignar IDs.
5. **Implementación.** Escribir las pruebas con los IDs. Una aserción con resultado esperado concreto por caso; sin `assert True`, sin `try/except` que trague la falla. Casos de la misma técnica pueden ir parametrizados (`@pytest.mark.parametrize`, `it.each`) manteniendo el ID por fila.
6. **Ejecución.** Correr la suite completa y guardar la salida literal. Medir cobertura estructural con la herramienta del ecosistema (`pytest --cov --cov-branch`, `vitest --coverage`, `c8`, JaCoCo). Si no hay herramienta disponible, decirlo en el reporte en vez de estimar.
7. **Cierre.** Escribir el reporte, renderizar el PDF, revisar portada, una tabla y una caja.

Severidad de defectos: **alta** = resultado incorrecto en una regla de negocio, dinero, datos o seguridad, sin rodeo; **media** = resultado incorrecto con rodeo o en un caso poco frecuente; **baja** = mensaje, formato o comportamiento cosmético. Los umbrales del semáforo usan esta escala.

Una prueba que falla porque el código tiene un defecto **se queda fallando** y se documenta como defecto (sección 11 del reporte). No se ajusta el esperado para que pase.

## 3. Matriz de selección de técnica

La técnica la decide una **propiedad observable de la base de prueba**, no la costumbre. El CTFL clasifica las técnicas en black-box, white-box y experience-based, y establece que las experience-based complementan a las otras dos [1, §4.1]. El análisis de riesgo de producto determina qué técnicas se emplean y qué cobertura se busca [1, §5.2.3].

| Si la base de prueba tiene… | Técnica | Referencia | Ítem de cobertura | Variante fuerte (riesgo alto) |
|---|---|---|---|---|
| Un dominio de entrada o salida que se procesa por clases (válidas e inválidas) | Equivalence Partitioning | [1, §4.2.1]; [3, cap. 4]; [5] | partición | Each Choice con varios parámetros [8] |
| Particiones **ordenadas** con frontera (rangos, montos, fechas, longitudes) | Boundary Value Analysis | [1, §4.2.2]; [3]; [6] | frontera (2 valores) o frontera + vecinos (3 valores) | 3 valores [6] |
| Varias condiciones que **combinadas** producen acciones distintas (reglas de negocio) | Decision Table Testing | [1, §4.2.3]; [5]; [4] | columna (regla) factible | tabla completa sin minimizar |
| Comportamiento que depende de **lo que pasó antes** (estados, ciclo de vida, flujos) | State Transition Testing | [1, §4.2.4]; [4] | estado / transición válida / toda transición | all transitions, una inválida por test |
| Muchos parámetros independientes con explosión combinatoria | Pairwise / combinatorial | [2]; [18] | par de valores | t-way con t = 3 |
| Código disponible y se necesita medir qué se ejecutó | Statement testing | [1, §4.3.1] | sentencia ejecutable | — |
| Decisiones (`if`, `switch`, bucles) en el código | Branch testing | [1, §4.3.2] | rama | MC/DC en decisiones compuestas críticas [8] |
| Historial de fallas conocido, errores típicos del lenguaje o dominio | Error Guessing / fault attacks | [1, §4.4.1]; [12] | error anticipado | lista de ataques documentada |
| Especificación delgada o presión de tiempo | Exploratory testing (con charter) | [1, §4.4.2]; [13] | objetivo del charter | sesión con time box y debriefing |
| Estándar externo con criterios verificables (OWASP, accesibilidad, convenciones) | Checklist-based | [1, §4.4.3]; [17] | ítem de checklist | checklist actualizado por análisis de defectos |
| Historia de usuario con criterios de aceptación | ATDD / Given-When-Then | [1, §4.5.2, §4.5.3]; [14]; [15] | criterio de aceptación | un test por criterio + negativos |
| Invariante que debe valer para todo un dominio grande | Property-based testing | [19] | propiedad | generador con casos frontera sesgados |
| Duda sobre la fuerza de la suite misma | Mutation testing | [20] | mutante | mutation score por módulo |

Notas de aplicación, todas desde el syllabus salvo indicación:

- **EP.** Las particiones no se solapan y no son vacías; se identifican para entradas, salidas, configuración, valores internos, tiempo e interfaces. Cobertura = particiones ejercitadas ÷ identificadas, **incluidas las inválidas**. Con varios parámetros, el criterio mínimo es *Each Choice* (cada partición de cada parámetro al menos una vez), que no cubre combinaciones [1, §4.2.1].
- **BVA.** Solo aplica a particiones ordenadas. Con 2 valores se prueba la frontera y su vecino en la partición adyacente (Craig 2002, Myers 2011); con 3 valores, la frontera y ambos vecinos (Koomen 2006). El ejemplo del syllabus: `if (x ≤ 10)` implementado como `if (x = 10)` no lo detecta 2-value BVA (10, 11) y sí lo detecta 3-value BVA con x = 9 [1, §4.2.2]. Elegir 3 valores cuando la frontera toca dinero, permisos o seguridad. Entre particiones adyacentes los vecinos se repiten (el vecino superior de 12 es la frontera 13): se prueba cada **valor** una sola vez y la cobertura se reporta como ítems de cobertura ejercitados ÷ identificados, aclarando cuántos valores distintos los cubrieron.
- **Tabla de decisión.** Notación: T, F, "–" (irrelevante), N/A (infactible); en acciones, X ocurre y vacío no. Cobertura = columnas factibles ejercitadas ÷ factibles. Su fuerza es exponer combinaciones olvidadas y contradicciones en los requisitos; con muchas condiciones el número de reglas crece exponencialmente y se usa tabla minimizada o enfoque basado en riesgo [1, §4.2.3].
- **Transición de estados.** Tres criterios de fuerza creciente: all states < valid transitions (0-switch) < all transitions. All transitions incluye intentar cada transición inválida, **una inválida por caso** para evitar enmascaramiento de defectos, y es el mínimo para software de misión o seguridad crítica [1, §4.2.4]. La tabla de estados del reporte muestra las celdas vacías (inválidas) explícitamente.
- **Statement / branch.** 100% de sentencias no garantiza probar la lógica de decisión; branch coverage subsume statement coverage, nunca al revés [1, §4.3.1, §4.3.2]. Ninguna técnica white-box detecta **omisiones**: si el código no implementa un requisito, no hay rama que ejecutar (Watson 1996) [1, §4.3.3]. Por eso white-box se usa para medir y cerrar huecos de las black-box, no para reemplazarlas.
- **MC/DC.** Cada condición atómica de una decisión debe mostrar que afecta el resultado de forma independiente [8]. Aplica a decisiones compuestas (`a and (b or c)`) con nivel de riesgo ≥ 6; está fuera del CTFL Foundation [1, §4.3].
- **Error guessing.** Categorías del syllabus para construir la lista de ataques: entrada (valor correcto rechazado, parámetro faltante), salida (formato, resultado), lógica (caso faltante, operador equivocado), cálculo (operando incorrecto), interfaces (tipos incompatibles), datos (inicialización, tipo) [1, §4.4.1]. Frontera con EP: el representante de cada partición inválida cuenta como EP (un valor por partición); los valores adicionales de esa misma partición elegidos por ser fallas típicas del lenguaje (`None`, `True` como entero, `"30"` como texto) cuentan como EG. Ataques típicos: `None`/`null`, cadena vacía, Unicode, cero como divisor, negativos, overflow, zona horaria, redondeo de moneda, concurrencia.
- **Exploratorio.** Sesión con time box guiada por un charter con objetivos; útil con especificación pobre y como complemento de técnicas formales [1, §4.4.2]. En este entregable, cada hallazgo exploratorio se convierte en un test automatizado `EG-n` y el charter se documenta en el reporte.
- **Checklist.** Los ítems se formulan como preguntas verificables por separado; no deben contener lo que ya se chequea automáticamente ni criterios de entrada/salida (Brykczynski 1999) [1, §4.4.3].
- **Pairwise.** La mayoría de las fallas en los sistemas estudiados se disparan por la interacción de uno o dos parámetros [18]; por eso cubrir todos los pares reduce combinaciones de forma drástica con poca pérdida. Técnica de ISO/IEC/IEEE 29119-4 [2], fuera del CTFL Foundation.
- **Property-based y mutation.** Fuera del syllabus CTFL. Property-based genera entradas aleatorias contra una propiedad (QuickCheck [19]); mutation testing inserta defectos pequeños para medir si la suite los detecta [20]. Se reportan como técnicas complementarias, nunca como sustituto de EP/BVA.

**Nivel y tipo.** Declarar el nivel (componente, integración de componentes, sistema, integración de sistemas, aceptación) [1, §2.2.1] y el tipo (funcional, no funcional, caja negra, caja blanca) [1, §2.2.2]. Justificar la ubicación en la pirámide de pruebas [1, §5.1.6] y el cuadrante [1, §5.1.7].

## 4. Estructura obligatoria del reporte

Basada en el contenido de un *test completion report* [1, §5.3.2] y en las plantillas de ISO/IEC/IEEE 29119-3 [24]. Cada sección es un `h2` con este nombre o uno equivalente con dato.

**Portada.** Objeto, versión (commit corto), nivel y tipo, técnicas, resultado `N de M pasan`, fecha.

1. **Ficha del reporte.** Tabla campo/valor: objeto de prueba (`archivo` + función/endpoint), base de prueba, versión/commit, lenguaje y framework con la versión **con la que corrieron las pruebas** (la que imprime el runner, no la del sistema), comando de ejecución, nivel, tipo, autor, fecha.

   Marcadores de portada y header sin dato del proyecto: `{{ORG}}` = nombre del repositorio o del paquete; `{{AREA}}` = "Aseguramiento de calidad"; `{{TIPO_DOC}}` = "Reporte de Pruebas"; `{{TITULO_CORTO}}` = objeto y año; autor = el usuario de `git config user.name` o "Claude Code".
2. **Resumen.** Caja verde (todo pasa y criterios de salida cumplidos) o roja (defectos o criterios incumplidos) con: casos diseñados, casos que pasan/fallan, defectos encontrados, cobertura de cada técnica y cobertura estructural. Después, un párrafo de 3-5 oraciones con datos.
3. **Objeto y base de prueba.** Qué hace el objeto, de dónde salen los esperados (cita literal de la spec o de la línea de código), supuestos tomados donde la spec calla. Cada supuesto queda numerado (S1, S2…) porque un supuesto equivocado invalida los esperados que dependen de él.
4. **Análisis de riesgo de producto.** Tabla: condición, riesgo, probabilidad (1-3), impacto (1-3), nivel, técnica y cobertura que exige [1, §5.2.3].
5. **Estrategia.** Nivel, tipo, ubicación en pirámide/cuadrante, criterios de salida en caja dorada (por ejemplo: 100% de particiones, 100% de fronteras con 3 valores, ≥ 90% de ramas, 0 defectos de severidad alta abiertos) [1, §5.1.3].
6. **Técnicas aplicadas.** Un `h3` por técnica de diseño que produjo casos, con cinco partes fijas en este orden; cada parte puede ser un `h4` o un párrafo con su nombre en negrita. Statement y branch coverage van aquí solo si se agregaron casos `BR-n` para cerrar ramas; si solo se midieron, van en la sección 10.
   1. *Definición* — caja azul, cita textual parafraseada con `[n, §x.y.z]`.
   2. *Por qué aplica aquí* — caja morada: la propiedad concreta del escenario que disparó la técnica, con `archivo:línea` o criterio citado, y el nivel de riesgo que fijó la variante.
   3. *Derivación* — tabla de particiones, fronteras, reglas (columnas R1…Rn con T/F/–) o estados (tabla de estados con celdas inválidas vacías). Para estados se agrega el diagrama como tabla o SVG inline.
   4. *Casos* — tabla ID, entrada, esperado, `archivo:línea`, resultado (pasa/falla).
   5. *Cobertura y límites* — fórmula con números (`6 de 6 particiones = 100%`) y qué defecto **no** puede encontrar esta técnica en este escenario.
7. **Técnicas consideradas y descartadas.** Tabla: técnica, por qué no aplica o no compensa aquí (por ejemplo: "State Transition: `costo_envio` es pura, no guarda estado entre llamadas"). Esta sección demuestra que la selección fue deliberada.
8. **Trazabilidad.** Tabla compacta: condición/requisito → riesgo → técnica → IDs → `archivo:línea` → resultado. Permite verificar que cada requisito tiene casos y evaluar el riesgo residual [1, §1.4.4].
9. **Ejecución.** Entorno (SO, versión del lenguaje, del framework), comando exacto, salida literal del runner en `<pre>`, tabla de conteos por técnica (diseñados, pasan, fallan, omitidos). Nunca se inventan conteos: salen de la salida pegada.
10. **Cobertura estructural.** Sentencias y ramas por archivo, desde la herramienta. Para cada rama no cubierta: si es alcanzable, un caso `BR-n` que la cubra; si no, por qué.
11. **Defectos encontrados.** Una caja roja por defecto: ID del caso que lo expuso, entrada, esperado vs. obtenido, ubicación probable, severidad. Distinguir error (acción humana), defecto (en el código) y falla (lo observado) [1, §1.2.3]. Si no hubo, decirlo con el número de casos que lo respaldan, recordando que las pruebas muestran presencia de defectos, no su ausencia [1, §1.3].
12. **Riesgo residual y recomendaciones.** Lo que quedó sin probar y por qué (fuera de alcance, sin herramienta, no determinista), riesgos no mitigados, siguientes pruebas recomendadas con técnica y nivel.
13. **Criterio de decisión.** Semáforo (liberar / liberar con condiciones / no liberar) con umbrales numéricos y una caja verde o roja con la recomendación.

**Apéndice A — Referencias.** Lista numerada estilo IEEE solo con las fuentes citadas en el reporte, tomadas de la sección 6 de este archivo.

**Apéndice B — Reproducción.** Comandos para instalar dependencias, correr la suite, medir cobertura y regenerar el PDF.

## 5. Reglas de redacción

- Español. Los nombres de técnicas y de criterios de cobertura van en inglés como en el glosario ISTQB (Equivalence Partitioning, branch coverage), con traducción la primera vez si ayuda.
- Cada oración lleva un dato verificable: un número, un ID, un `archivo:línea`, una sección citada. Una oración que se puede borrar sin perder información se borra.
- Títulos de sección con dato cuando el contenido lo permite ("BVA de 3 valores: 12 casos sobre 4 fronteras").
- Pasado para lo que ya se hizo: "Se ejecutaron 31 casos; 30 pasan y BVA-07 falla en `envios.py:22`".
- Nada de relleno: sin "es importante destacar", sin adjetivos de valor ("robusto", "exhaustivo"), sin conclusiones genéricas, sin emoji.
- Citas: `[n, §x.y.z]` solo con las secciones listadas en este archivo. Libros sin capítulo verificado se citan sin capítulo. Nunca se inventan páginas.
- Profundidad: la sección 6 es el núcleo del reporte. Un escenario con 3 técnicas produce al menos 3 subsecciones completas con sus 5 partes; no se resume en una tabla.

## 6. Bibliografía disponible para el reporte

Numeración de referencia para esta skill. En el reporte se listan solo las fuentes citadas, numeradas por orden de primera cita; conviene escribir el reporte completo con estos números y renumerar al final con un solo reemplazo.

[1] ISTQB, *Certified Tester Foundation Level Syllabus*, v4.0.1, International Software Testing Qualifications Board, 2024. Secciones verificadas: §1.2.3 errores, defectos, fallas; §1.3 principios; §1.4.1 actividades; §1.4.4 trazabilidad; §2.2.1 niveles; §2.2.2 tipos; §2.2.3 confirmación y regresión; §4.1 panorama de técnicas; §4.2.1 EP; §4.2.2 BVA; §4.2.3 tablas de decisión; §4.2.4 transición de estados; §4.3.1 statement; §4.3.2 branch; §4.3.3 valor del white-box; §4.4.1 error guessing; §4.4.2 exploratorio; §4.4.3 checklist; §4.5.2 criterios de aceptación; §4.5.3 ATDD; §5.1.3 criterios de entrada y salida; §5.1.5 priorización; §5.1.6 pirámide; §5.1.7 cuadrantes; §5.2.3 análisis de riesgo de producto; §5.3.2 reportes de prueba.
[2] ISO/IEC/IEEE 29119-4:2021, *Software and systems engineering — Software testing — Part 4: Test techniques*.
[3] G. J. Myers, C. Sandler, and T. Badgett, *The Art of Software Testing*, 3rd ed. Hoboken, NJ, USA: John Wiley & Sons, 2011.
[4] B. Beizer, *Software Testing Techniques*, 2nd ed. New York, NY, USA: Van Nostrand Reinhold, 1990.
[5] L. Copeland, *A Practitioner's Guide to Software Test Design*. Norwood, MA, USA: Artech House, 2004.
[6] T. Koomen, L. van der Aalst, B. Broekman, and M. Vroon, *TMap Next for Result-Driven Testing*. 's-Hertogenbosch, The Netherlands: UTN Publishers, 2006.
[7] R. D. Craig and S. P. Jaskiel, *Systematic Software Testing*. Norwood, MA, USA: Artech House, 2002.
[8] P. Ammann and J. Offutt, *Introduction to Software Testing*, 2nd ed. Cambridge, UK: Cambridge University Press, 2016.
[9] P. C. Jorgensen, *Software Testing: A Craftsman's Approach*, 4th ed. Boca Raton, FL, USA: CRC Press, 2014.
[10] I. Forgács and A. Kovács, *Practical Test Design*. Swindon, UK: BCS, 2019.
[11] A. H. Watson, D. R. Wallace, and T. J. McCabe, *Structured Testing: A Testing Methodology Using the Cyclomatic Complexity Metric*, NIST Special Publication 500-235, 1996.
[12] J. A. Whittaker, *How to Break Software: A Practical Guide to Testing*. Boston, MA, USA: Addison-Wesley, 2002.
[13] E. Hendrickson, *Explore It!: Reduce Risk and Increase Confidence with Exploratory Testing*. Raleigh, NC, USA: The Pragmatic Programmers, 2013.
[14] G. Adzic, *Bridging the Communication Gap: Specification by Example and Agile Acceptance Testing*. London, UK: Neuri, 2009.
[15] M. Gärtner, *ATDD by Example: A Practical Guide to Acceptance Test-Driven Development*. Boston, MA, USA: Addison-Wesley, 2012.
[16] E. van Veenendaal, Ed., *Practical Risk-Based Testing: The PRISMA Approach*. The Netherlands: UTN Publishers, 2012.
[17] B. Brykczynski, "A survey of software inspection checklists," *ACM SIGSOFT Software Engineering Notes*, vol. 24, no. 1, pp. 82–89, 1999.
[18] D. R. Kuhn, D. R. Wallace, and A. M. Gallo, "Software fault interactions and implications for software testing," *IEEE Transactions on Software Engineering*, vol. 30, no. 6, pp. 418–421, 2004.
[19] K. Claessen and J. Hughes, "QuickCheck: A lightweight tool for random testing of Haskell programs," in *Proc. ACM SIGPLAN International Conference on Functional Programming (ICFP)*, 2000, pp. 268–279.
[20] R. A. DeMillo, R. J. Lipton, and F. G. Sayward, "Hints on test data selection: Help for the practicing programmer," *Computer*, vol. 11, no. 4, pp. 34–41, 1978.
[21] L. Crispin and J. Gregory, *Agile Testing: A Practical Guide for Testers and Agile Teams*. Boston, MA, USA: Addison-Wesley, 2009.
[22] K. Beck, *Test-Driven Development: By Example*. Boston, MA, USA: Addison-Wesley, 2002.
[23] OWASP Foundation, *OWASP Top 10*, 2021.
[24] ISO/IEC/IEEE 29119-3:2021, *Software and systems engineering — Software testing — Part 3: Test documentation*.

## 7. Checklist antes de entregar

- [ ] Las pruebas corren con un solo comando y la salida pegada en el reporte coincide con la última corrida.
- [ ] Cada ID de la tabla de trazabilidad existe en el código de pruebas y cada test tiene ID.
- [ ] Cada técnica aplicada tiene sus 5 partes y al menos una cita `[n, §…]`.
- [ ] La sección de técnicas descartadas tiene al menos 2 filas.
- [ ] Los porcentajes de cobertura tienen numerador y denominador.
- [ ] Los defectos son pruebas que fallan, no esperados modificados.
- [ ] El PDF abre, la portada no tiene header, el índice enlaza y las tablas largas repiten encabezado.
- [ ] No se hizo commit de los entregables ni de archivos generados (`.coverage`, `__pycache__`, `salida.txt`) salvo que el usuario lo pida.
