# Fundamentos de CI/CD y calidad de las pruebas como gate

## 8. Fundamentos de CI/CD

### 8.1 Pipeline, gate y transformation

**Pipeline:** una secuencia automatizada de pasos que corre cada vez que el código cambia. Un **step** es una tarea (linting es un ejemplo). "Automatizado" significa que nadie escribe el comando a mano: arranca solo.

- **Gate:** verifica código y puede bloquear el pipeline, cerrado hasta que el código sea suficientemente bueno: linting, testing.
- **Transformation:** cambia la forma del código y lo mueve adelante, sin verificar: building, publishing, deploying.
- Linting corre primero: no hay razón para correr un suite de tests más lento contra código que ya falla un chequeo rápido.

**Pipelines hechos de tareas:** una tarea es como una función — una unidad discreta de trabajo, lo mismo que es un step. Un pipeline secuencia tareas en orden, la forma en que un programa llama funciones. Ejemplo: lint → test → build image → push to registry → update running service.

**Dos caminos a un pipeline:** hacer clic para armarlo en una GUI, o comprometerlo como *config as code*. El segundo es el que sobrevive a la rotación de personal.

### 8.2 Anatomía de un archivo real (GitHub Actions)

```yaml
# .github/workflows/lint.yml
on: push
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ruff check .
```

- **Workflow:** todo el archivo.
- **Trigger:** `on: push`.
- **Job:** `lint`, el trabajo de una máquina.
- **Step:** cada línea `-`, en orden.

### 8.3 Webhooks

El disparo manual (alguien recuerda correr el pipeline) se rompe en cuanto un equipo crece más allá de una persona. Un webhook permite que el control de versiones llame al pipeline automáticamente cada vez que se hace push de un cambio — el mismo trigger `on: push`. La regla que esto desbloquea: **cuando el pipeline se rompe, dejar de hacer push de cambios.**

### 8.4 Vocabulario e historia

- **1994:** "continuous integration" acuñado (Booch et al.).
- **1999, 2007:** CI formalizado como práctica (Beck; Duvall et al., quien también acuñó "continuous deployment" ese mismo año).
- **2010:** "continuous delivery" nombrado como su propia práctica (Humble & Farley), 16 años después de CI.
- **2014-2016:** "CI/CD" entra en uso común como catch-all informal, sin un momento único de acuñación.

CI/CD es el término más nuevo y más flojo del conjunto — exactamente por qué la gente lo usa inconsistentemente.

**Continuous Integration (CI):** "el proceso de combinar cambios de código frecuentemente, con cada cambio verificado en el check-in." *Combining*: mergeando los cambios de múltiples personas. *Verified*: los gates corren sobre el resultado. En términos gate/transformation, CI es específicamente los gates.

**Continuous Delivery (CD):** múltiples ingenieros pueden seguir cambiando el mismo software y aun así confiar en que hace lo que pretenden. Dos garantías: se puede entregar cambios de forma segura en cualquier momento, y entregar es tan simple como apretar un botón. La integración continua es cómo se obtiene la primera garantía; el release automatizado es cómo se obtiene la segunda.

### 8.5 Puntos clave

- Linting se ordena en tres cubetas (bugs, errors, style), y los bugs van primero cuando el tiempo es corto.
- Los codebases legacy se lintean vía baseline-luego-enforce, no todo-de-una-vez.
- Un pipeline es una secuencia automatizada de pasos; un gate (linting, testing) puede bloquearlo; una transformation (build, publish, deploy) lo mueve adelante.
- CI son los gates; CD agrega release automatizado, siempre-seguro.

---

## 9. Calidad de las pruebas como gate de CI

**Caso gancho:** el día más ocupado del año, órdenes pico, y un servicio cae por más de una hora. La causa raíz traza a un fallo de test que llevaba tiempo pasando y era rutinariamente ignorado. Una suite verde no vale nada si el equipo dejó de creerle a los rojos.

### 9.1 Señal vs. ruido

- *Signal* es la información; *noise* es cualquier cosa que distraiga de ella.
- Passing y failing **no son** automáticamente signal y noise, respectivamente.
- Un test que pasa puede esconder un problema real (un "noisy success"); un test que falla y no enseña nada nuevo es ruido.
- **Passing ≠ signal. Failing ≠ noise.** Ese es todo el reencuadre.

**Cuatro casos, clasificados:**

- Un test de UI falla porque el cambio de un ingeniero movió un botón. → **Signal.** El fallo le dijo algo cierto y nuevo sobre su propio cambio.
- Un test de integración falla una vez, nadie puede explicar por qué, se re-corre, pasa. → **Signal.** Algo causó el fallo, aunque la causa aún no se entienda.
- Ese mismo test falla de nuevo en un PR distinto, semanas después; se re-corre de nuevo, pasa, se mergea. → **Noise.** Ignorar el mismo flake sin resolver dos veces convierte información real en papel tapiz.
- Alguien refactorizando nota que un test de paginación espera 3 ítems cuando el número correcto es 2, y el test actualmente pasa. → **Noise.** El test que *pasa* es el ruidoso aquí: está cubriendo un bug real.

**Tratar cada fallo como un bug:**

- Cada fallo es un desajuste entre lo que el test espera y lo que el sistema hace.
- Dos causas posibles: el test se escribió mal, o el sistema genuinamente tiene un bug. Ambas necesitan investigarse, ninguna debe asumirse.
- La forma más común en que se introduce el ruido: asumir "el test debe estar mal" sin verificar.

### 9.2 Flakes y retries

- Un flake falla inconsistentemente: mismo test, condiciones aparentemente iguales, resultado distinto.
- Los flakes son la fuente más común de una suite ruidosa, precisamente porque "solo re-córrelo" se siente inofensivo.
- Tratar un flake exactamente como cualquier otro fallo: un bug a investigar, no una rareza a evitar.

**El retry mal puesto.** Un test se integra con un servicio de terceros conocido por conexión inestable; falla aproximadamente 1 de 20 corridas, puramente por timeouts. Un ingeniero envuelve **todo el cuerpo del test** en un decorador de retry, así que se re-corre automáticamente hasta tres veces.

El problema: el retry esconde silenciosamente cualquier otro bug del test, no solo el flake de red. En el caso documentado, un bug real de facturación (montos de cobro incorrectos) quedó enmascarado por esa misma lógica de retry, y causó un outage en producción. **Fix más seguro:** reintentar solo la pieza aislada y no determinista (la llamada de conexión misma), nunca las aserciones o la lógica de negocio alrededor.

**Get to green, y quedarse ahí:** "llegar a verde" significa llevar la suite a un estado donde consistentemente pasa. Necesario, pero no suficiente: una suite que está verde porque los fallos fueron silenciados sigue siendo ruidosa. La meta real: cada fallo, cuando ocurre, es señal confiable que vale la pena atender de inmediato.

### 9.3 Velocidad de la suite

**Usar la pirámide activamente.** No basta con conocer la forma: la medición de cobertura sirve para **rebalancear** la pirámide, con presupuestos de tiempo concretos por capa. Un presupuesto ejemplo: unit tests bajo 1 minuto, integration bajo 5 minutos, la suite completa bajo 30 minutos.

**Dividir por tipo antes de que todo sea rápido.** Con cientos de unit tests que terminan en menos de un minuto combinados, y un lote más pequeño de integration tests que toman cuatro horas, dividir la suite por tipo permite que la capa más rápida corra antes del merge — incluso antes de que toda la suite sea rápida. Mecanismos simples: una convención de carpetas, o una feature del lenguaje (p. ej. pytest markers) para seleccionar solo una capa. Una victoria parcial ahora vence esperar una suite perfecta después. Principio: "correr las pruebas más rápidas primero" (Duvall, *Continuous Integration*, 2007).

**Coverage como mapa, no como número de vanidad.** Statement coverage dice qué líneas del código bajo prueba realmente corren durante un test. Ejemplo: una función de cinco líneas, tres cubiertas por el unit test existente, dos líneas de ruta de error sin cubrir por nada. La cobertura es el mapa para decidir exactamente dónde agregar o quitar tests.

**Moviendo tests hacia abajo en la pirámide:**

1. Encontrar un vacío de cobertura en unit test, agregar el unit test faltante.
2. Buscar un test de integración/end-to-end más lento que cubra exactamente la misma lógica.
3. Si el unit test ahora lo cubre, borrar el test duplicado más lento con confianza.

**Ejemplo — invertir la razón.** Un método tiene baja cobertura de unit test. Existen cinco integration tests, cada uno aparentando cubrir un caso distinto alrededor de él; un unit test cubre solo el caso más simple del camino feliz. La corrección: reemplazar los cinco integration tests por uno, cubriendo solo que los componentes están correctamente conectados, y agregar unit tests para cada caso (no-cache, cached, error, empty-results) que los integration tests solían cargar solos. Resultado: menos tests lentos, más tests rápidos, la misma confianza.

**Parallel execution (mismo equipo, más cores):** requisitos — los tests no pueden depender entre sí, no pueden requerir un orden específico, no pueden interferir vía estado compartido. En una máquina, la ejecución en paralelo reparte los tests entre cores de CPU. Si los tests *unit* son suficientemente lentos para necesitar esto, es un smell: probablemente no son realmente unit tests.

**Sharding (más máquinas):** la misma idea que la ejecución en paralelo, repartida en múltiples máquinas en vez de múltiples cores.

```
pytest --shard-id=$SHARD_ID --num-shards=$NUM_SHARDS
```

Matemática trabajada: 50 tests de navegador a ~2.5 min cada uno, objetivo 25 minutos → 5 shards mínimo, 7 elegidos por margen de maniobra.

**Diagnóstico de una suite mal balanceada.** Una suite corre en ~3 horas, una vez por PR. Distribución: 10% unit tests, 0% integration tests, 90% end-to-end tests. Los tests "unit" toman 20 minutos y cubren 34% del código.

- 20 minutos para tests "unit" es un smell: los unit tests reales corren en segundos. Son casi con certeza integration tests disfrazados.
- Casi cero integration tests más 90% end-to-end tests significa que la suite se apoya completamente en la capa más lenta y más cara.
- Orden del fix: separar los tests genuinamente rápidos para correr primero, medir la cobertura real de unit tests, luego usar la cobertura para encontrar end-to-end tests seguros de degradar.

### 9.4 El vacío entre merges

**CI no es suficiente:** incluso un pipeline CI disparado-por-PR, rápido y confiable, puede seguir perdiendo bugs introducidos *entre* merges. Caso: dos ingenieros cada uno cambia la lógica de defaulting de la misma función, en líneas distintas. Ambos PRs pasan CI independientemente. Mergeados juntos, la combinación rompe producción.

**Tres opciones para cerrar el vacío:**

| Opción | Cómo funciona | Costo |
|---|---|---|
| **Periodic CI** | Corre en `main` en intervalos fijos | Atrapa después del hecho; necesita un dueño de monitoreo; deja main romperse temporalmente |
| **Up-to-date branch** | Requerido antes del merge | Bloquea cada otro PR abierto cada vez que uno hace merge; todos se resincronizan antes de mergear |
| **Merge queue** | Re-corre CI con el último `main` antes de mergear | Una corrida extra de CI ralentiza el merge; complejo de implementar sin soporte nativo |

GitHub y sistemas de control de versiones hosted similares ofrecen cada vez más merge queues como feature nativa, no algo que la mayoría de equipos construye.

El periodic CI sigue valiendo la pena aun con merge queue: un flake que aparece 1 en 500 corridas es mucho más probable de ser realmente investigado vía periodic CI cada hora que enterrado en el PR de otra persona.

### 9.5 Puntos clave

- Distinguir señal de ruido: los tests que pasan y que fallan pueden ser cualquiera de los dos.
- Investigar cada fallo, incluyendo flakes, en vez de silenciarlo con un retry amplio.
- Usar la pirámide de pruebas más cobertura para mantener una suite rápida sin perder confianza.
- Explicar cómo la paralelización y el sharding intercambian hardware por velocidad, no confianza.
- Nombrar el vacío que deja el CI disparado-por-PR, y qué lo cierra.

---

