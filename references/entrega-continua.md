# Control de versiones, build seguro, despliegue y DORA

## 10. Control de versiones y fuente única de verdad

### 10.1 Version control no es opcional

La propia definición de CI asume un lugar donde hacer check in: *continuous integration* significa combinar cambios de código frecuentemente, cada uno verificado en el check-in. Ese verbo, *check in*, presupone un lugar compartido y versionado *a donde* hacer check in. "To be doing continuous delivery, you must use version control" — establecido de forma directa, no como preferencia suave.

### 10.2 Fuente única de verdad

**Analogía de los dos relojes.** Una estación de tren tiene un reloj en cada andén; uno marca 3:04, el otro 3:11, y un boleto dice que el tren sale a las 3:10. Una red de relojes no promedia lecturas ni vota: un reloj se designa la autoridad, y cada otro reloj del edificio se resetea para coincidir con él.

**Definición técnica:** un **source of truth** es el único lugar designado como autoritativo para una pieza de información dada — una pieza de configuración, digamos. Cada otra copia es un espejo: si discrepa de la fuente, la copia está mal, no la fuente.

**El modo de fallo nunca es "no tenemos fuente de verdad". Es tener dos sistemas que cada uno cree que la tiene.**

**Caso — el mismo outage, dos veces en una noche.** Un servicio cae: su configuración de base de datos apunta a una base de datos que ya no existe. Un ingeniero lo arregla directamente en la consola del proveedor cloud. La alerta se limpia. Esa noche, el mismo outage ocurre de nuevo, mismo síntoma.

- **Diagnóstico:** la consola cloud y la herramienta de despliegue tenían cada una su propia copia de la configuración. La herramienta de despliegue reconcilia periódicamente el servicio corriendo contra *su propia* copia guardada, sobreescribiendo silenciosamente el fix manual horas después.
- **Fix:** el control de versiones se vuelve la única fuente de verdad; la herramienta de despliegue lee de ahí, no de su propio estado guardado por separado. Agregar el repo como una *tercera* copia independiente empeoraría las cosas.
- **Matiz importante:** si el equipo nunca hubiera automatizado el despliegue del todo, este bug específico no hubiera pasado — se necesitan *dos* sistemas que cada uno crea que tiene la verdad. El fix es una fuente de verdad, no menos automatización.

### 10.3 Config as code y manejo de secretos

Configuración de despliegue, ajustes de conexión, definiciones de infraestructura: cada archivo de texto plano que define cómo corre el software, guardado en control de versiones como el código fuente mismo. La práctica de tratar los datos de texto plano que definen el software como código fuente data de al menos los años 1970 bajo otros nombres.

**Los secretos nunca se comprometen:** el acceso al repo es más amplio de lo que debería ser el acceso a secretos. Se compromete un archivo de config que *referencia* un secreto por nombre, y la herramienta de despliegue lo resuelve desde un almacén con control de acceso al momento de desplegar:

```
--db-username=randomCloud:watchMeWatch:userServiceDBUser
```

### 10.4 Joint rollout: software y configuración juntos

Cuando un cambio de código depende de un cambio de configuración, ambos se despliegan como una **unidad atómica**.

Ejemplo: dividir una base de datos en dos, de modo que `--db-name` se vuelve `--db-users-name` más `--db-movies-name`.

- **Antes:** construir la imagen nueva, luego una ventana frágil donde el código y la config guardada discrepan.
- **Después:** ambos cambios comprometidos juntos, desplegados como una unidad.

Si el código se desplegara primero y el cambio de config siguiera un día después, durante esa ventana el código pediría dos parámetros que la config no le da.

### 10.5 Trunk-based development

Un árbol tiene un tronco grueso enraizado en el suelo y docenas de ramas creciendo desde él. Si una rama crece larga antes de reconectarse con el nuevo crecimiento del resto del árbol, se separa de lo que el árbol se volvió.

**Definición técnica:** en control de versiones, el **trunk** (usualmente la rama llamada `main`) es la única línea compartida de historia. **Trunk-based development** significa mergear cambios pequeños de vuelta a él frecuentemente — en días, no semanas — en vez de dejar que una rama de característica crezca larga y separada antes de reconectarse.

Incluso trabajo incompleto (tests deshabilitados, esqueletos de método vacíos) se mergea, rastreado con una referencia clara a un issue, en vez de vivir en una rama. Resultado documentado: el lead time promedio de cambios de un equipo bajó **de 45 a 18 días** tras adoptar esto.

**Redefiniendo "completo" para un PR incremental (cuatro condiciones):**

1. Todo el código cumple los chequeos de linting.
2. Los docstrings para funciones incompletas explican por qué están incompletas.
3. Cada cambio de código está soportado por tests y documentación.
4. Los tests deshabilitados incluyen una explicación y refieren a un issue de tracking.

```python
@unittest.skip("(#2387) AllCatsAllTheTime integration WIP")
```

**Ejemplo de aplicación.** Un PR agrega un esqueleto de clase vacío, un unit test que falla (etiquetado con un issue de tracking) y varios unit tests que actualmente no hacen nada pero siempre pasan; ninguna característica es usable todavía. Contra la definición de cuatro ítems, el único vacío es la **documentación**: los docs de integración no mencionaban el trabajo en progreso. Una vez agregados, el PR se aprueba.

**Qué compra realmente mergear temprano:** un segundo ingeniero puede construir sobre la clase en progreso sin coordinar directamente, porque el código ya está en main. Código muerto es malo solo si su presencia causa tiempo de mantenimiento desperdiciado; código incompleto-pero-mergeado no es "muerto" en ese sentido: se está construyendo activamente hacia su uso.

**Alternativa:** para equipos cuyas políticas prohíben código muerto o deshabilitado en la rama principal, las **feature flags** y **build flags** son las herramientas estándar. El principio subyacente — mergear chico y seguido — sigue aplicando sin literalmente comprometer tests deshabilitados.

### 10.6 Puntos clave

- Nombrar la fuente única de verdad para una pieza de configuración, y explicar por qué una segunda copia en cualquier lugar es un bug esperando pasar.
- Desplegar un cambio de software y su cambio de configuración dependiente juntos, atómicamente, en vez de en dos fases frágiles.
- Aplicar la definición de "PR completo" de cuatro ítems para juzgar un PR incremental.

---

## 11. Build y release seguros

### 11.1 SLSA — Supply Chain Levels for Software Artifacts

Framework de niveles incrementales de seguridad de build, inspirado en las prácticas internas de seguridad de producción de Google.

**Cinco requisitos (SLSA v0.1, nivel 3):**

| # | Requisito | Significa |
|---|---|---|
| 01 | Always releasable | El codebase puede producir un build en cualquier momento; realmente el trabajo de CI |
| 02 | Automated builds | Cada paso vive en un script, disparado por automatización, no corrido a mano |
| 03 | Build as code | Los propios scripts y config del build también viven en control de versiones |
| 04 | Use a CD service | Un servicio dedicado, consistentemente configurado, no la laptop de alguien |
| 05 | Ephemeral environments | Frescos por cada build, destruidos después, nada persiste |

Más allá del nivel 3: **hermetic builds** (sin acceso a red durante el build) y **reproducible builds** (mismos inputs, output idéntico byte a byte) — el tooling actual tiene soporte limitado para cualquiera de los dos.

**Sobre procesos manuales previos:** un proceso de build que era un documento que una persona leía y ejecutaba manualmente, y que funcionó sin incidente mayor por años, no era "malo". Revisarlo una vez que se vuelve prioridad es el ciclo de vida normal de la automatización CD, no una señal de negligencia pasada. "Don't let the perfect be the enemy of the good": evaluar contra los cinco requisitos, luego mejorar incrementalmente.

### 11.2 Semantic Versioning

**SemVer — MAJOR.MINOR.PATCH:** un número de versión es una promesa sobre *qué tipo* de cambio ocurrió.

- **MAJOR:** cambios incompatibles hacia atrás.
- **MINOR:** características nuevas compatibles hacia atrás.
- **PATCH:** fixes compatibles hacia atrás.

**Por qué importa.** Un servicio sobreescribía silenciosamente su imagen "latest" en cada release: sin distinción de versión, nunca. El equipo consumidor no podía elegir qué versión correr, no podía distinguir releases entre sí, y no tenía forma de saber qué cambió. Un método cambió su interfaz sin avisar y el build del consumidor se rompió en producción sin ninguna advertencia. Semantic versioning, más dejar que el consumidor elija su versión, arregla los tres problemas a la vez.

### 11.3 Pinning por versión vs. por hash

Pinear a una versión exacta (`querytosql == 1.3.2`) detiene sorpresas de "siempre lo último". Pero **no es una garantía dura**: la mayoría de registros de paquetes dejan que un mantenedor republique el mismo tag de versión con contenido distinto.

Solo un **hash de contenido** es verdaderamente inequívoco: mismo hash, garantiza mismos bytes; si el contenido alguna vez cambia, el build falla ruidosamente en vez de silenciosamente usar código distinto.

**El tradeoff:** el hash-pinning también bloquea fixes bien intencionados de la misma versión de un mantenedor — hay que re-pinear explícitamente para obtenerlos. No es un upgrade gratis, es un costo real por su estabilidad.

---

## 12. Despliegue y métricas DORA

### 12.1 Las cuatro métricas, en dos pares

| Categoría | Métrica | Elite |
|---|---|---|
| **Velocity** | Deployment frequency | Múltiples veces al día |
| **Velocity** | Lead time for changes | Menos de una hora |
| **Stability** | Time to restore service | Menos de una hora |
| **Stability** | Change failure rate | 0-15% |

Casi una década de investigación DORA agrupó a los equipos en desempeño elite/high/medium/low en cada métrica.

**Definiciones:**

- **Deployment frequency:** qué tan seguido una organización libera exitosamente a producción.
- **Lead time for changes:** cuánto tiempo toma un commit en llegar a producción.
- **Time to restore service:** cuánto tarda el servicio en recuperarse tras una falla en producción.
- **Change failure rate:** qué porcentaje de despliegues causa una degradación que requiere remediación.

La velocidad, en cualquier dominio, siempre es una tasa: alguna cantidad de algo, por alguna cantidad de tiempo. Ambas métricas de velocity son exactamente eso.

**Tabla completa de bandas (métricas de velocidad):**

| Banda | Deployment frequency | Lead time for changes |
|---|---|---|
| Elite | múltiples veces al día | menos de una hora |
| High | una vez/semana a una vez/mes | un día a una semana |
| Medium | una vez/mes a una vez/6 meses | un mes a seis meses |
| Low | menos de una vez/6 meses | más de seis meses |

### 12.2 Desplegar más seguido, no menos

Un equipo que sufre outages frecuentes post-despliegue puede sentir la tentación de desplegar *menos* seguido, mensualmente en vez de semanalmente, para reducir riesgo. Es lo contrario de lo que funciona: **cada despliegue carga menos cambios, así que cualquiera individualmente es menos probable de contener el cambio que rompe algo.**

Matemática trabajada, mismos outages, re-atribuidos a deploys diarios en vez de semanales: **37.5%** de change failure rate (3 de 8 deploys semanales fallaron) vs. **10%** (4 de 40 deploys diarios-equivalentes).

### 12.3 Code freeze y deployment windows

- **Code freeze:** un periodo durante el cual no se mergean ni liberan cambios nuevos, pensado para dejar que un build se asiente y se estabilice antes de salir.
- **Deployment window:** un slot fijo y angosto cuando se permiten releases del todo. Afuera de él, nada se despliega, sin importar qué tan listo esté.

**Caso trabajado — congelar no hace los despliegues más seguros.** Una empresa de 50+ empleados fija sus despliegues a ventanas cada dos meses, con una semana completa de code freeze antes. Cada despliegue se sigue sintiendo riesgoso, y las características toman cada vez más tiempo en salir. Los números: deployment frequency una vez cada dos meses, lead time promedio 45 días — **medium performer** en ambas métricas de velocidad.

**El arreglo, en dos pasos:**

| Paso | Palanca | Resultado |
|---|---|---|
| 1 | Trunk-based development + entrega incremental | Lead time 45 → 18 días; deployment frequency sin cambio |
| 2 | Remover ventanas fijas y code freeze | Lead time 18 → 4 días; deployment frequency mensual → semanal |

Tras el paso 2: algunos cambios desplegados un día después del merge, máximo companywide de ocho días. Esto alcanza **DORA high performance** en ambas métricas de velocidad.

**El orden importa:** la disciplina de CI vino primero, la cadencia de despliegue segundo, no al revés. Después del paso 1 el deployment frequency no se había movido nada — las ventanas fijas eran la única palanca restante, y no requerían ninguna herramienta nueva ni más gente.

### 12.4 Rollback first, investigate second

Cuando un despliegue rompe algo, revertir a la última versión conocida-buena de inmediato. No esperar un forward-fix bajo la presión de un outage activo: el bug subyacente sigue arreglándose, solo calmadamente después.

Ejemplo documentado: adoptar "rollback first" como política sola bajó el time-to-restore-service de múltiples **días** a **13-40 minutos**. Sin tooling nuevo requerido.

### 12.5 Estrategias de despliegue

**Rolling update:** una instancia actualizada a la vez, in place.

**Blue-green deployment:** dos ambientes completos, un switch de tráfico. En el mismo ejemplo trabajado, bajó el time-to-restore a aproximadamente **5-12 minutos**. Es la estrategia que necesita más **hardware extra**: duplica momentáneamente la capacidad.

**Canary — el origen de la palabra:** los mineros llevaban canarios bajo tierra. Los canarios son mucho más sensibles al monóxido de carbono que las personas: colapsan mucho antes de que un humano note el gas. Un canario callándose significaba evacuar, antes de que el gas se volviera letal.

**Canary en software, mismo concepto:** exponer un cambio a una porción pequeña de tráfico real primero. Si las métricas se mantienen sanas el rollout continúa; si no, todo el tráfico revierte de inmediato.

**Requisitos del canary (tres cosas, no solo un porcentaje):**

1. La habilidad de dividir tráfico entre versiones: un load balancer configurable.
2. Una forma automatizada de juzgar la salud: los *four golden signals* (latency, traffic, errors, saturation) de *Site Reliability Engineering*.
3. Una instancia baseline, así el canary y la comparación están en igualdad de condiciones.

**Canary con baseline** es la variante que necesita más **sofisticación de automatización**: división de tráfico, comparación automatizada de salud, y una instancia de comparación justa, todo a la vez. No es la misma respuesta que "cuál necesita más hardware".

### 12.6 Continuous deployment no es para todos

Liberar automáticamente en cada commit es el punto más agresivo del espectro de CD, no un requisito para "hacer CD bien".

**Saltárselo si aplica cualquiera de:**

- Cualquier request fallido es inaceptable.
- Hay bloqueadores regulatorios.
- Existe gating QA/exploratorio obligatorio.
- Se requiere sign-off humano.
- Los releases necesitan cambios de hardware.

Combinado con canary deployments y respuesta rollback-first, un ejemplo trabajado alcanzó desempeño elite en las cuatro métricas DORA: múltiples deploys/día, menos de una hora de lead time, ~7 minutos para restaurar, 12.5% de change failure rate.

### 12.7 Puntos clave

- Control de versiones, config as code: secretos referenciados, nunca comprometidos.
- Un build seguro: automatizado, scripteado, en un servicio dedicado, fresco cada vez.
- Cada release identificado: una versión semántica, dependencias pineadas a un hash.
- Desplegar más seguido, no menos, y hacer rollback primero cuando algo se rompe.
- Blue-green y canary hacen el rollback casi instantáneo, de bajo radio de explosión.

---

