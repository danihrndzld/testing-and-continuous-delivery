# Testing estático y linting

## 7. Testing estático

### 7.1 Leerlo, no correrlo

El artefacto se examina sin ejecutarlo, de dos formas:

- **Por personas — reviews:** alguien lee el código o el requisito y dice qué está mal con él: reviews, walkthroughs, pull requests.
- **Por una máquina — static analysis:** una herramienta parsea el código fuente y reporta lo que coincide con una regla: código inalcanzable, un valor de retorno ignorado, esa concatenación SQL.

Ambos reportan **defectos**. Un **fallo** necesita ejecución, así que el testing estático nunca ve uno.

### 7.2 El techo del análisis estático

El análisis estático nunca ejecuta el programa: no tiene noción de lo que el código se suponía que hiciera. Solo un test con el resultado esperado correcto, o una revisión humana, atrapa una regla de negocio equivocada disfrazada de código funcionando.

**Ejemplo — qué atrapa y qué no un linter:**

| Caso | Herramienta / cubeta |
|---|---|
| Variable sin usar sentada en una función | Linter, cubeta *error* |
| Variable usada antes de asignarse | Linter, cubeta *bug* |
| Nombre de variable `camelCaseInAPythonFile` | Linter, cubeta *style* |
| Función cuyo docstring dice que retorna la orden más reciente, pero en realidad retorna lo último de un diccionario desordenado | **Ningún linter atrapa esto** |

**Caracterización de una herramienta concreta (ESLint):**

- **Lee:** JS y TS source. Parsea cada archivo en un árbol y compara reglas contra él, en el editor y de nuevo en CI.
- **Pro:** responde antes del commit. Subraya la línea segundos después de escribirla, y `--fix` reescribe muchos hallazgos.
- **Contra:** un archivo a la vez. Las reglas coinciden dentro de un archivo, así que un valor contaminado en otro lugar se escapa.
- **Nunca encuentra:** la regla equivocada. Un descuento codificado al 12% donde la spec dice 15%: regla equivocada, estilo limpio.

Herramientas comunes de análisis estático más allá del linting de estilo: SonarQube, CodeQL, Semgrep.

### 7.3 Linting

El mismo split static/dynamic aplicado al código fuente: examina y marca problemas sin ejecutar nunca el programa. La palabra "linter" traza a la herramienta original de Bell Labs de 1978, `lint`.

**Tres cubetas (todo linter mainstream las usa):**

1. **Bug:** un mal uso que cambia comportamiento de forma no deseada (p. ej. una variable usada antes de asignarse). Ejemplo Pylint: `used-before-assignment` (categoría E).
2. **Error:** un mal uso que no cambia comportamiento pero daña la mantenibilidad (p. ej. una variable sin usar). Ejemplo Pylint: `unused-variable` (categoría W).
3. **Style:** decisiones de formato inconsistentes y code smells (orden de imports, convención de nombres). Ejemplo Pylint: `bad-indentation`, `invalid-name` (categorías C/W).

Prioridad cuando el tiempo es limitado: **bugs primero, luego errors, style al final.**

**Dos maquinarias para la misma idea:**

- **Enterprise (p. ej. SonarQube):** un dashboard que revisa todo el equipo, no una terminal. Quality gates que bloquean un merge automáticamente. Un catálogo de reglas compartido, más de 30 lenguajes, un estándar en toda la empresa.
- **Startup (p. ej. Ruff, ESLint):** un archivo de config pequeño, comprometido al repo. Un puñado de reglas que el equipo realmente acordó. Suficientemente rápido para correr en cada guardado, nadie dedicado a mantenerlo.

**Panorama por lenguaje:**

- **Ruff:** Python.
- **ESLint:** TypeScript/JavaScript.
- **golangci-lint:** Go, un meta-linter que agrega docenas de linters en una sola corrida.
- **RuboCop:** Ruby.

**Ejemplo medido — default ruleset vs. todas las reglas.** Sobre Flask 0.1 (la primerísima release etiquetada del framework, de 2010, antes de que alguien le corriera un linter):

```
git clone --depth 1 --branch 0.1 https://github.com/pallets/flask.git
cd flask && uvx ruff check .              # ruleset por defecto
uvx ruff check --select ALL .             # todas las reglas
```

Resultado con Ruff 0.15.17: **22 issues** (default) vs. **1,023 issues** (`--select ALL`). El ruleset elegido, no el código, define la mitad de la respuesta.

**Adopción en legacy — "Configure, Baseline, Enforce, Divide"** (para escalas de decenas de miles de warnings):

1. Configurar el linter contra el estándar real de código del equipo.
2. Registrar el conteo de issues de hoy como baseline; no arreglarlo todavía.
3. Enforce en submission: cada PR reduce el conteo o lo mantiene, nunca lo sube.
4. Divide and conquer: aislar código que rara vez cambia y no tiene bugs abiertos de la exigencia de linting (p. ej. un directorio `frozen/`, excluido en config), en vez de forzar un fix.

¿Cuáles saltan la fila sin importar el baseline? Bugs, no style. "El ideal es cero issues de linting, siempre" solo aplica limpiamente a código nuevo o que cambia activamente.

### 7.4 Gestión reproducible de dependencias (`uv`)

- Instala paquetes, resuelve dependencias, construye ambientes virtuales y corre herramientas de línea de comandos.
- Reemplaza `pip`, `pip-tools`, `virtualenv` y buena parte del workflow diario de Poetry.
- Un solo binario, escrito en Rust por Astral (la misma empresa que hace Ruff), lanzado en febrero de 2024.
- `uvx <tool>` corre una herramienta en un ambiente desechable: nada que activar, nada que quede atrás.

**Cifras de velocidad (benchmarks de los propios proyectos, no independientes):**

- `uv`: 8-10× más rápido que `pip`/`pip-tools` sin caché; 80-115× más rápido con caché caliente; creación de virtual environment tan rápido como 4.1 ms, ~80× más rápido que `python -m venv`.
- `ruff`: "10-100× más rápido que linters existentes (como Flake8)" según su propio README. Reportes de terceros: Pylint ~2.5 min en 250k líneas vs. Ruff ~0.4 s en el mismo codebase (~375×); Ruff ~150-200× más rápido que Flake8 en otra máquina.

**Instalación:**

- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`, o `brew install uv`.
- Windows/PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`, o `winget install --id=astral-sh.uv -e`.
- Verificar con `uv --version`.

---

