# Tipos de prueba y pruebas relacionadas con cambios

## 3. Tipos de prueba

### 3.1 Funcional vs. no funcional

| | Funcional | No funcional |
|---|---|---|
| Pregunta | **Qué** hace | **Qué tan bien** lo hace |
| Referencia | El **requisito** | Un **umbral**, o juicio |
| Ejemplo | "¿Login acepta contraseña válida?" | "¿Login responde en menos de 2 segundos?" |

Defectos funcionales hacen la característica *incorrecta*. Defectos no funcionales la hacen *inaceptable*.

**Functional testing — definición:** *qué* hace el sistema, verificado **contra** los requisitos.

- Verifica cada función que el software se supone que realiza.
- La corrección la decide el **requisito**, no la opinión de alguien.
- Simula el uso real del sistema, con datos realistas.
- Automatizado *o* manual; el tipo no lo decide.

**Los cuatro pasos para correr una prueba funcional (el loop, cada vez):**

1. Preparar los datos de prueba.
2. Definir el resultado esperado — el paso que la gente se salta, y luego acepta lo que el sistema imprime.
3. Ejecutar la prueba.
4. Comparar el valor real con el valor esperado.

**Ejemplo trabajado — `checkout_total`:**

```python
# cart.py
def checkout_total(price, quantity, is_member):
    subtotal = price * quantity
    if subtotal > 100: subtotal *= 0.90
    if is_member: subtotal *= 0.95
    return round(subtotal, 2)
```

| Caso | Entrada | Esperado |
|---|---|---|
| Sin descuento | price=10, qty=5, member=False | 50.00 |
| Solo bulk | price=10, qty=11, member=False | 99.00 |
| Solo miembro | price=10, qty=5, member=True | 47.50 |
| Ambos descuentos | price=10, qty=11, member=True | 94.05 |
| Frontera (=100) | price=10, qty=10, member=False | 100.00 (a exactamente 100 el descuento bulk NO aplica) |

**Ejemplo trabajado — funcional sobre una API real:** `GET /track/v1/details/{trackingNumber}` retorna estado de entrega, ubicación y ETA. Casos: tracking válido en tránsito (200, status+location+ETA); paquete entregado (200, status=Delivered); tracking desconocido pero bien formado (404); tracking malformado (400); auth faltante o mala (401). Mismo requisito, cinco entradas distintas: happy path, un estado de borde, y tres formas en que el request mismo puede estar mal.

### 3.2 Caja negra, caja blanca y caja gris

- **Black box:** la especificación y el comportamiento. Nunca el código fuente. Los casos vienen del **requisito**, así se puede probar un sistema que no se escribió. Única opción para un sistema de terceros, y la honesta para un flujo de usuario. El catch: no se puede saber qué rutas nunca se ejercitaron. System, acceptance y la mayoría de API testing viven aquí.
- **White box:** el código fuente — rutas, ramas, estado interno. Los casos vienen de la **estructura** del código. Única perspectiva donde **cobertura** significa algo. El catch: se puede derivar hacia probar lo que el código *hace*, no lo que *debería* hacer. Unit testing vive aquí.
- **Gray box:** una vista parcial, y usualmente la realista. Sin código fuente, pero se conoce el esquema y el contrato de API. Suficiente para construir mejores datos y para atrapar efectos secundarios que un test black-box se salta. No suficiente para medir cobertura: aún no se ven las ramas. Integration y contract testing viven aquí.

**Clasificación de cinco escenarios:**

1. Manejar el formulario de login en un navegador, verificándolo contra la historia de usuario → **Black box.**
2. Agregar un test porque un reporte mostró que una rama `else` nunca corrió → **White box.**
3. Probar la API de un partner usando solo su contrato publicado → **Gray box.**
4. Leer el SQL que corre una función, luego construir la fila que la rompe → **White box** (el caso discutible).
5. Llamar la API, luego consultar la base de datos para confirmar qué escribió → **Gray box.**

### 3.3 Testing no funcional: cinco dimensiones

Mide **qué tan bien** se comporta el sistema, no qué hace. Aplica en *cada* nivel de prueba, no solo al final. Mayormente black-box, reusando las mismas técnicas. Necesita habilidades y tooling especiales. Encontrar estos defectos tarde es peligroso: usualmente son arquitectónicos, no un fix de una línea.

**1. Performance:** ¿se mantiene rápido bajo la carga esperada, y dónde se rompe?

- **Load testing:** modela el uso *esperado*, lo sostiene, y verifica que el sistema sigue respondiendo. Responde "¿cuántos usuarios podemos manejar?"
- **Stress testing:** empuja *más allá* del uso normal, por horas o días, para encontrar dónde se rompe y si se recupera.
- Graficado sobre ejes tiempo × usuarios concurrentes: la curva de LOAD sube y se sostiene en el pico esperado; la de STRESS sigue subiendo hasta un *breaking point*.
- **Performance monitoring (shift-right):** el testing termina, el monitoreo no. Propiedad de los dueños del sistema, corriendo continuamente en producción. Caza *degradación*: la página que se puso 200 ms más lenta cada release. Una prueba de carga prueba un umbral una vez; el monitoreo prueba que se mantiene verdadero.

**2. Usability:** evalúa la facilidad con la que los usuarios finales alcanzan su meta.

- ISO 9241-11, tres ejes: Effectiveness (¿pueden terminar?), Efficiency (¿a qué costo?), Satisfaction (¿cómo se sintió?).
- Qué observar: Visibility (¿el estado del sistema es obvio?), Match with the real world (¿habla el idioma del usuario?), Ease of learning (¿qué pasa la primerísima vez?).
- El feedback viene **directo de la audiencia objetivo.** Uno no es la audiencia objetivo.

**3. Security:** pasó de ser solo trabajo del admin de red a ser parte del mundo del tester de software. Objetivos: verificar los requisitos de seguridad, luego encontrar y cerrar vulnerabilidades. Corre en *cada* fase del SDLC, manual o automatizado. Ejemplos: restricciones de IP, puertos expuestos, penetration testing. El OWASP Top 10 existe porque las mismas fallas a nivel de aplicación siguen repitiéndose: broken access control ha sido el número uno desde 2021.

**4. Visual:** ¿renderiza correctamente entre navegadores, sistemas operativos y tamaños de pantalla? Layout responsivo, posiciones de elementos, nada superpuesto. Manual o automatizado.

**5. Resilience:** ¿aguanta bajo condiciones *reales*, y se recupera? Cumple el nivel de servicio que el negocio acordó. Chaos engineering rompe cosas deliberadamente en producción para probarlo.

Visual y resilience son fáciles de posponer y caros de retrofit — exactamente lo que los hace riesgos no funcionales que vale la pena planear.

**Ejemplo integrador (la caja de búsqueda de un sitio de video):**

- Funcional · smoke test: la búsqueda es lo único que el sitio no puede no tener. Si está rota, nada más vale la pena probar.
- No funcional · load test: la búsqueda debe mantenerse rápida con millones de personas consultando a la vez. El load testing simula usuarios concurrentes y verifica que el tiempo de respuesta se sostiene.
- Misma característica, dos preguntas: ¿funciona? y ¿sigue funcionando cuando todos llegan?

---

## 4. Pruebas relacionadas con cambios

### 4.1 Smoke testing — "¿Vale la pena probar este build?"

- Un pase delgado, amplio, deliberadamente barato sobre el **camino crítico**.
- Decide si vale la pena correr el resto de las pruebas.
- Usualmente a nivel de integración y sistema; manual o automatizado.
- Etimología, de la electrónica de hardware: *"The phrase smoke test comes from electronic hardware testing. You plug in a new board and turn on the power. If you see smoke coming from the board, turn off the power. You don't have to do any more testing."* — Kaner, Bach & Pettichord, *Lessons Learned in Software Testing*, p. 95.
- Vinculado al principio 5 (paradoja del pesticida): un smoke suite que nunca cambia deja de atrapar cosas.

**Ejemplo trabajado — smoke suite para una app de delivery de comida.** Restricciones: máximo 5 checks, toda la suite bajo 3 minutos; si algún check falla, el build se rechaza sin discusión.

1. La app abre; login con cuenta conocida funciona.
2. La lista de restaurantes carga con al menos un resultado.
3. Agregar un ítem al carrito; el total se actualiza.
4. Pagar con la tarjeta sandbox; se crea una orden.
5. La orden aparece en la página de estado.

Solo el camino del dinero, barato, y un veredicto sí/no sin interpretación.

### 4.2 Sanity testing — "¿Ya lo arreglaron?"

- Re-verifica los bugs reportados en el build anterior.
- Verifica que el fix no rompió funcionalidad vecina.
- Angosto y profundo: solo el área que cambió.
- Usualmente no scripted y time-boxed. Si pasa, el build se gana un ciclo completo de pruebas.

**Smoke vs. sanity:**

- Smoke: **amplio y superficial.** Cada característica crítica, un nivel de profundidad. Corre en *cada* build, antes que cualquier otra cosa.
- Sanity: **angosto y profundo.** Solo lo que cambió. Corre en un build que reclama fixes específicos.
- Ambos son *gates*, no suites de prueba: deciden si el testing costoso debería empezar. Ninguno reemplaza el regression testing.

**Cómo se decide, con cuatro notas de release:**

- "Fixed: checkout crasheó cuando el carrito tenía 0 ítems." → **sanity** (un fix reclamado: re-verificarlo a él y a sus vecinos).
- "New build, 40 archivos cambiados en login, search y checkout." → **smoke** (demasiadas áreas tocadas para confiar en algo).
- "Hotfix: fotos de perfil se suben de nuevo." → **sanity** (un hotfix nombra exactamente qué spot-check hacer).
- "Primer build tras cambiar de proveedor de pagos." → **smoke** (un build nuevo de todo; el camino de pago también se gana regresión profunda después).

### 4.3 Regression testing

- Re-correr pruebas que **ya pasaron**, para probar que un cambio no rompió comportamiento que ya funcionaba.
- Origen del nombre: latín *regredi*, "retroceder" — no solo falló, fue *hacia atrás*.
- Visualización típica: una grilla releases × características, donde una celda previamente verde se pone roja después de un cambio en otro lugar.

**Caso — CrowdStrike, julio 2024.** Un update defectuoso del sensor Falcon crasheó millones de máquinas Windows en todo el mundo: tableros de aerolíneas, hospitales y terminales de punto de venta entre ellos. Había pasado algo de testing, pero no el pase de regresión que hubiera atrapado un crash a nivel de driver en el arranque.

**El costo de la regresión:** *"Every fix can quietly break something else. In theory you re-run every test after every change; in practice you have to come close, and it is costly."* — parafraseado de Fred Brooks, *The Mythical Man-Month*, p. 122.

**Tres estrategias para manejar ese costo:**

1. **Retest all:** todo, cada vez.
2. **Test selection:** solo lo que el cambio puede alcanzar.
3. **Prioritization:** lo más riesgoso primero.

En la práctica se combinan: la lista por-push es *selection*, el orden nocturno es *prioritization*, la corrida completa del fin de semana es *retest all*.

### 4.4 Ejemplo de smoke testing sobre una API pública

Sobre `https://deckofcardsapi.com/api` (sin cuenta, llave ni token):

- `GET /deck/new/shuffle/?deck_count=1` → 200, `deck_id` y `remaining: 52`.
- `GET /deck/<deck_id>/draw/?count=5` → 200, cinco cartas con `value` y `suit`, `remaining: 47`.
- `GET /deck/badid/draw/?count=1` → 404 y `success: false`.

El deck carga estado (52 → 47 → 42 entre draws). Pedir 60 cartas de un deck de 47 responde **200**, con `success: false` en el body — el argumento más limpio para no detenerse en la línea de estado y verificar siempre el cuerpo de la respuesta. Herramientas típicas: Bruno, Postman, curl.

### 4.5 Puntos clave

- Distinguir niveles de prueba (unit, integration, system, acceptance) de tipos de prueba.
- Diseñar un smoke suite de cinco checks para una app de uso diario.
- Usar smoke y sanity como gates, y saber por qué regression se ganó su nombre.
- Escribir una política de regresión que quepa en un presupuesto de tiempo real.
- Detectar un par de integración: dos partes que cada una funciona sola y fallan juntas.

---

