# Diseño de pipelines

## 13. Diseño de pipelines

### 13.1 El listado universal de tareas

Todo proyecto termina con la misma lista: linting, unit/integration/end-to-end tests, building, publishing, deploying. Cada tarea es un **gate** (verifica, puede bloquear el pipeline) o una **transformation** (cambia la forma del artefacto).

**CI y Release comparten tareas.** CI debería reusar las propias tareas de build y deploy del pipeline de release, no unas separadamente definidas y de apariencia similar, así lo que se prueba se mantiene lo más cerca posible de lo que realmente llega a producción.

**Señal más rápida vs. setup más lento.** El principio de ordenamiento es "obtener tanta señal como sea posible, tan rápido como se pueda". Un build check es casi instantáneo. Linting y unit tests cuestan más setup pero aún corren en minutos. Integration y end-to-end tests cuestan más de construir y corren más lento — exactamente por qué aparecen últimos.

### 13.2 Starter packs

**Definición:** el conjunto ordenado de tareas de automatización agregadas primero cuando un proyecto no tiene ninguna — no todo a la vez, el mínimo que ya obtiene señal útil corriendo.

La propiedad que decide si un starter kit es bueno o inútil es la misma que la de un kit de primeros auxilios: **listo antes de que se necesite**. El conjunto mínimo útil de ítems, no todo lo que pudiera concebiblemente ayudar. Un starter pack no es el kit completo que eventualmente se querría; es el más pequeño que ya funciona.

**Greenfield vs. legacy:**

- **Greenfield:** un proyecto nuevo, poco o nada de código todavía, libertad total de fijar estándares desde el día uno.
- **Legacy:** años de código, estándares inconsistentes, deuda técnica ya acumulada.
- Todo proyecto greenfield eventualmente se vuelve uno legacy, así que ambos starter packs vale la pena conocerlos.

#### Orden greenfield (nueve pasos)

1. Build check
2. Linting, tan pronto como sea posible
3. Arreglar violaciones de linting existentes
4-5. Unit tests, luego medir cobertura
6. Agregar tests para cumplir la meta de cobertura
7-8. Publish, luego deploy
9. Integration y end-to-end tests, al final

**El primer paso real es el build check, no linting ni tests.** Si el código ni siquiera se puede construir, nada río abajo (testing, linting, deploying) puede correr significativamente tampoco.

```yaml
name: build-check
on: [pull_request, merge_group, schedule]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build .
```

Un job, tres triggers: PR, merge queue, y programado. De no tener automatización CD a tener un primer pipeline CD.

**Por qué integration y E2E van deliberadamente al final:** toman más tiempo en configurarse. Posponerlos deja que cada señal más rápida (build, lint, unit tests, cobertura) empiece a pagar dividendos antes, en vez de esperar a que la pieza más lenta esté lista. Es una elección de ordenamiento deliberada: optimiza para que la señal llegue antes en general, al costo de que la cobertura end-to-end llegue después.

**Dos elecciones tempranas más:**

- **Meta de cobertura:** aproximadamente 80% para empezar — suficientemente indulgente para saltarse líneas de bajo valor, suficientemente alta para cubrir la mayoría de lo que importa. Un punto de partida a ajustar, no una ley.
- **Estrategia de despliegue:** canary continuo es "relativamente libre de riesgo" incluso el día uno, con espacio para reconsiderar después.

**Pipelines resultantes:**

```yaml
# ci.yml
jobs:
  lint:
  unit-test:
  coverage:
  integration-test:
  e2e-test:
```

```yaml
# release.yml
jobs:
  build:
  publish:
  deploy-canary:
```

#### Orden legacy

Mismo primer paso, orden distinto después:

1. **Build check**, igual que greenfield.
2. **Isolate:** encontrar la porción del codebase que vale la pena invertir en ella.
3. **Tests**, enfocados solo en ese código aislado.
4. **Automatización de despliegue**, solo una vez que esto se sienta seguro.

**Linting se deprioritiza a "si hay tiempo".** Es el paso que cambia de posición más dramáticamente: paso 2 en greenfield, casi opcional en legacy.

**Pain-first (regla de priorización en legacy):** *pain* = algo evitado porque lidiar con ello causa un problema real — trabajo bloqueado, esfuerzo fuera de horario, posposición repetida. Diagnóstico: ¿qué se hace inusualmente poco seguido? Ahí se esconde el dolor.

Ejemplo: despliegues cada tres meses en el mejor caso, todos los servicios a la vez, una fase de staging manual con todo el equipo, bugs encontrados solo después del despliegue. Causa raíz: el estado del código que se despliega, no la mecánica del despliegue. La cobertura empezó por repo desde 0% hasta más de 60%; la regla nunca fue una meta uniforme, solo **nunca dejarla bajar**.

**De manual a automatizado, cuatro pasos:**

1. Documentar lo que actualmente se hace manualmente.
2. Convertir esa documentación en uno o más scripts.
3. Comprometer esos scripts a control de versiones.
4. Agregar disparo automatizado para el proceso ya scripteado.

**La reversión que vale la pena nombrar — E2E antes que unit tests en legacy:** el orden greenfield pone unit tests bien antes de integration y end-to-end. Para un codebase legacy grande, un test end-to-end temprano puede superar en rango a los unit tests. Por qué: los unit tests necesitan más esfuerzo de refactorización en un codebase ya grande, y un test end-to-end puede atrapar si servicios ya separados realmente funcionan juntos — algo que nada más en el pipeline estaba verificando.

### 13.3 Task boundaries: una tarea por señal

**El problema del script gigante.** Si el pipeline entero es una sola tarea corriendo un script bash gigante, pasar o fallar es la única señal que produce: un fallo no dice qué se rompió.

**La regla:** "usar una tarea separada para cada señal discreta que se quiera que el pipeline produzca." Nueve funciones en un script se vuelven nueve tareas separadas, individualmente reportables.

**Tareas bien diseñadas leen como funciones bien diseñadas:** altamente cohesivas, débilmente acopladas, entradas/salidas claras, haciendo justo lo suficiente.

Dos señales de alarma de una tarea que hace demasiado:

- Lógica duplicada entre tareas.
- Orquestación (loops, polling) horneada dentro de una tarea en vez de dejarla al pipeline.

**Caso — sin tests, sin forma de saber.** Una librería bash compartida, `e2e_tests.sh`, gana una línea nueva: hace `unset` de una variable de entorno "para garantizar un estado limpio" para un caso de uso nuevo. El cambio se revisa y aprueba. Se libera, luego rompe silenciosamente el pipeline de otro equipo, uno que dependía de que esa variable estuviera puesta.

¿Hizo mal su trabajo el revisor? No: no existían tests que demostraran el comportamiento esperado de la librería, así que ni el autor ni el revisor tenían forma de verificar el impacto más amplio del cambio. El fix son **tests para la librería compartida** — específicamente un test que aserta qué estado de ambiente existe después de importarla — no un proceso de revisión más estricto.

### 13.4 Cuándo bash se queda corto

Bash es realmente una interfaz al sistema operativo: constructos de bash, built-ins de bash, y lo que sea que esté en `PATH`. Genial para mover cosas por tuberías. Pero las funciones bash no pueden retornar datos reales, solo exit codes, y no hay buena forma de versionar o compartir una librería bash.

**Cuatro señales de que bash es la herramienta equivocada:**

1. Scripts de más de unas pocas líneas.
2. Múltiples condiciones y loops.
3. Lógica suficientemente compleja para sentirse digna de testear.
4. Lógica que un equipo quiere compartir entre scripts vía librerías.

**Incidente real:** en abril de 2021, un atacante modificó el script bash compartido de subida de Codecov, exfiltrando secretos de variables de entorno de cada pipeline que lo importaba.

**Tres caminos para salir de bash:**

1. Convertir en herramienta standalone en un lenguaje de propósito general.
2. Convertir en librería de lenguaje de propósito general.
3. Convertir en tarea CD reusable y versionada.

Una rutina compleja y stateful se vuelve una librería testeada y versionada; chequeos de linting de pocas líneas no necesitan moverse del todo. Ejemplo del tercer camino, referenciado por tag:

```yaml
jobs:
  lint:
    steps:
      - uses: miorg/cd/.github/actions/python-lint@v0.1.0
```

### 13.5 Diagnóstico: errors, speed, signal

Tres categorías de problema de pipeline:

- **Errors:** el pipeline hace lo incorrecto.
- **Speed:** toma demasiado tiempo en correr cuando realmente se necesita.
- **Signal:** reporta la información correcta, demasiado tarde para actuar barato.

**El orden de arreglo es errors → speed → signal.** Un pipeline lento no puede correr más seguido sin importar qué tan limpio sea su manejo de errores. Un pipeline que no puede correr más seguido tampoco puede arreglar su problema de señal. Arreglar velocidad empieza a arreglar señal también, gratis.

Ejemplo de los tres a la vez: un pipeline que no limpia ambientes de test al fallar (error), toma más de una hora así que solo corre nocturno (speed), y para cuando falla, el cambio que rompió algo se mergeó un día entero antes (signal).

### 13.6 `finally`, ejecución en paralelo y sharding

**`finally`:** limpieza que corre sin importar qué, por analogía a una cláusula `finally` de código, que corre incluso tras una excepción previa. En GitHub Actions: `if: ${{ always() }}` en el job que debe correr siempre.

**Ejecución paralela:** correr tareas independientes en paralelo reduce el tiempo total a aproximadamente la duración de la más lenta, en vez de la suma de todas. En GitHub Actions, jobs sin una línea `needs:` nombrando otro job arrancan al mismo tiempo, automáticamente.

```yaml
jobs:
  build-image:
    runs-on: ubuntu-latest
  setup-sut:
    runs-on: ubuntu-latest
```

**Sharding — el origen de la palabra:** un *shard* es un fragmento cortado del todo, suficientemente chico para manejarlo solo — como los fragmentos con los que los arqueólogos rearman una vasija.

**Sharding en software:** la misma idea que la ejecución en paralelo, repartida entre múltiples máquinas en vez de múltiples cores. El sharding de tests divide una suite larga en fragmentos más chicos y los corre lado a lado.

```yaml
jobs:
  e2e:
    strategy:
      matrix: {shard: [1, 2, 3, 4, 5, 6]}
    steps:
      - run: pytest --shard-id=${{ matrix.shard }} --num-shards=6
```

**Lo que la velocidad habilita.** Un pipeline end-to-end que corría nocturno porque tomaba más de una hora, shardeado a menos de 20 minutos, ya es suficientemente rápido para correr en **cada PR**. Se fusiona entonces en un pipeline CI combinado — linting, unit, integration y end-to-end, todos empezando en paralelo desde el inicio:

```yaml
jobs:
  gate:
    needs: [lint, unit, integration, e2e]
```

Un job nombrando los cuatro en `needs:` es el punto de fusión (fan-in): exactamente el pago que la velocidad habilita para señal.

### 13.7 Combinar pipelines y parametrización

**El problema del desvío.** Si la lógica de build/deploy de CI y la del pipeline de release son dos implementaciones *diferentes*, pasar CI nunca verifica realmente lo que el pipeline de release hará. Duplicar las tareas del pipeline de release dentro de CI es lo que dejó a los dos desviarse.

**El fix: llamar al mismo pipeline, no duplicarlo** — con inputs distintos.

```yaml
jobs:
  release:
    uses: ./.github/workflows/release.yml
    with: {image-registry: test-registry, deploy-target: test-env}
```

**Parametrización con `workflow_call`:**

```yaml
on:
  workflow_call:
    inputs: {image-registry, image-name, version-from-tag, deploy-target}
```

La definición idéntica de pipeline construye, empuja y despliega a producción cuando se llama con parámetros de producción, o a un sistema de test desechable cuando se llama con parámetros de test.

**Qué necesita volverse parámetro** cuando un pipeline de release hardcodeado debe servir también a CI:

1. `image-registry`: registro de producción vs. registro de test desechable.
2. `image-name`: qué imagen construye y empuja el pipeline.
3. `version-from-tag`: de dónde viene el número de versión.
4. `deploy-target`: IP de producción fija vs. ambiente de test recién provisionado.

**Un valor que merece mención aparte: secretos y credenciales.** Un ambiente de test probablemente necesita credenciales distintas a producción, y parametrizarlas de forma segura importa igual.

### 13.8 Puntos clave

- Reconocer el listado de tareas universal en el pipeline de cualquier proyecto, y nombrar qué falta de él.
- Ordenar las tareas CD de un proyecto greenfield por cuánta señal agrega cada una, y qué tan rápido.
- Ordenar las tareas CD de un proyecto legacy aislando y priorizando el dolor, no copiando el checklist de greenfield.
- Explicar por qué linting y end-to-end testing intercambian prioridad entre greenfield y legacy.
- Reconocer cuándo un script CD se ha quedado corto para bash, y los tres caminos para migrarlo.
- Diagnosticar los problemas de un pipeline como errors, speed y/o signal, y arreglarlos en ese orden.
- Expresar `finally`, ejecución en paralelo y sharding de tests en sintaxis de GitHub Actions.
- Parametrizar un pipeline para servir tanto un contexto de release como uno de CI.

---

