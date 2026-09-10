# Fundamentos de la calidad y niveles de prueba

## 1. Fundamentos de la calidad

### 1.1 QA vs. QC vs. Testing

Relación de anidamiento: **QA ⊃ QC ⊃ Testing**. Tres círculos concéntricos — QA en el exterior, QC en el medio, Testing en el centro.

- **QA (Quality Assurance):** orientado a proceso y preventivo. "Un buen proceso, seguido correctamente, produce un buen producto." Aplica tanto al desarrollo como al testing. Responsabilidad de **todos**, no de un equipo. Mindset: *build quality in*, no inspeccionarla después.
- **QC (Quality Control):** más amplio que testing solo. Conjunto de actividades que verifican que el producto cumple sus requisitos de calidad — incluye métodos formales, simulación y prototipado, además de testing. Testing es la porción más grande de QC, pero no es todo.
- **Testing:** orientado a producto y correctivo. Ejercitar el producto para encontrar defectos y construir evidencia sobre su calidad. Es la forma más práctica de QC en el día a día, y la más estrecha de las tres.

### 1.2 Por qué se prueba

- Evaluar productos de trabajo (requisitos, diseños, código).
- Causar fallos y encontrar defectos.
- Asegurar la cobertura de pruebas requerida.
- Reducir el riesgo de calidad inadecuada.
- Verificar cumplimiento de requisitos, contratos y regulaciones.
- Proveer información para decisiones de stakeholders.
- Construir confianza en el software.
- Validar que el objeto cumple las expectativas de los stakeholders.

### 1.3 Error, Defecto (bug), Fallo

Cadena causal: **Error → Defecto → Fallo**.

- **Error:** acción o decisión humana que produce un resultado incorrecto (una equivocación). Ejemplo: un desarrollador malinterpreta la especificación y asume que un valor está en libras cuando debería estar en newtons.
- **Defecto (bug):** falla en un producto de trabajo (requisitos, diseño, código) que *puede* causar un fallo. Existe exista o no ejecución. Ejemplo: la suposición incorrecta de unidad ya quedó escrita en el código; el defecto existe corra o no alguien el código.
- **Fallo:** evento en que el sistema no realiza su función requerida dentro de límites especificados. Ocurre solo cuando el defecto es *ejecutado* bajo las condiciones correctas. Ejemplo: en vuelo, la navegación calcula mal y la nave se pierde.
- **Causa raíz (root cause):** la razón más profunda de por qué ocurrió el error — lo que busca el análisis de causa raíz.

**Caso — Ariane 5 Flight 501 (1996):** el cohete reutilizó software de referencia inercial de Ariane 4 sin testearlo bajo los parámetros de vuelo de Ariane 5. Un overflow en conversión de float de 64 bits a entero de 16 bits; tanto el computador primario como el de respaldo fallaron; el cohete se autodestruyó 37 segundos después del lanzamiento (~$370M perdidos).

- Error → asumir que el software de Ariane 4 era válido para Ariane 5 sin re-testear.
- Defecto → un overflow no manejado en el código de conversión de 64 a 16 bits.
- Fallo → ambos computadores de guía fallan; el cohete se autodestruye.
- Lección: código reutilizado sigue siendo código *nuevo* en un contexto nuevo — debe re-testearse contra las nuevas suposiciones.

**Caso — Mars Climate Orbiter (1999):** el software de tierra de un equipo producía datos de fuerza de empuje del propulsor en libras-fuerza-segundo, mientras el software de navegación esperaba newton-segundo. Ningún chequeo de conversión de unidades atrapó el desajuste. La sonda se acercó a Marte a la altitud incorrecta y fue destruida (~$327M perdidos).

- Error → una suposición de unidad no documentada ni verificada (libra-fuerza vs. newton).
- Defecto → un paso faltante de conversión/validación de unidades entre los dos sistemas.
- Fallo → trayectoria incorrecta; la nave se pierde al llegar.
- Lección: las interfaces entre equipos son donde se esconden las suposiciones — hacerlas explícitas y probarlas.

### 1.4 Los siete principios ISTQB

1. **Testing muestra la presencia de defectos, no su ausencia.** El testing reduce la probabilidad de que queden defectos sin descubrir, pero incluso si no se encuentra ningún defecto, no puede probar que el software es correcto.
2. **Las pruebas exhaustivas son imposibles.** Probar cada entrada, ruta y combinación solo es viable en casos triviales. Usar técnicas de prueba, priorización y testing basado en riesgo para enfocar el esfuerzo donde más importa.
3. **Las pruebas tempranas ahorran tiempo y dinero.** Los defectos encontrados temprano en el ciclo de vida son más baratos de corregir que los defectos encontrados después del release, cuando aparecen como fallos costosos en producción.
4. **Los defectos se agrupan.** Un número pequeño de módulos usualmente contiene la mayoría de los defectos encontrados — una distribución tipo Pareto. Esta observación es lo que hace efectivo el testing basado en riesgo.
5. **Cuidado con la paradoja del pesticida.** Correr las mismas pruebas repetidamente eventualmente deja de encontrar defectos nuevos — el software se vuelve "inmune" a ellas. Las pruebas necesitan revisarse y actualizarse regularmente.
6. **El testing depende del contexto.** No hay un enfoque único que sirva para todo. Un sitio de e-commerce, un sistema crítico de seguridad y una herramienta interna requieren cada uno una estrategia de testing diferente.
7. **La ausencia de defectos es una falacia.** Un sistema que técnicamente no tiene defectos puede seguir fallando si no cumple las necesidades reales de los usuarios. La validación importa tanto como la verificación.

### 1.5 Verificación vs. validación

- **Verificación** pregunta si el sistema coincide con la especificación.
- **Validación** pregunta si cumple la necesidad detrás de ella.

Unit, integration y system testing mayormente verifican; el acceptance testing es donde ocurre la validación. Por eso un cliente puede rechazar un release que pasó cada nivel anterior, y tener razón. También explica por qué una pila de defectos encontrados en acceptance es un riesgo de proyecto: la pregunta de validación se hizo demasiado tarde.

### 1.6 Modelos de balance: Pirámide, Trofeo y Cuadrantes

- **Pirámide de Pruebas (Mike Cohn):** base ancha de **Unit** (rápido, barato, numeroso), capa media **Integration** (verifica que los componentes funcionan juntos), punta angosta **E2E/UI** (chequeos de sistema completo, mantenidos deliberadamente pocos). Rápida, barata y numerosa en la base; lenta, cara y escasa en la punta.
- **Testing Trophy (Kent C. Dodds):** capas de abajo hacia arriba: static (base, más angosta) → unit → **Integration** (la "copa" — capa más ancha, mayor inversión) → E2E (aro delgado arriba). Cita guía: *"The more your tests resemble the way your software is used, the more confidence they can give you."*
- **Pirámide vs. Trofeo:** la Pirámide optimiza alrededor de unit tests como mayor inversión, construida para stacks donde las unidades son baratas de aislar. El Trofeo desplaza el centro de gravedad a integration tests, el mejor tradeoff confianza-por-costo para stacks modernos, especialmente frontend/JS.
- **Cuadrantes de Testing Ágil (Brian Marick / Crispin & Gregory):** matriz 2×2 — eje horizontal *business-facing* (arriba) vs. *technology-facing* (abajo); eje vertical *supporting the team* (izquierda) vs. *critiquing the product* (derecha).
  - **Q1** (tech-facing, supporting team, AUTOMATED): unit tests, component tests.
  - **Q2** (business-facing, supporting team, AUTOMATED + MANUAL): functional tests, story tests, examples.
  - **Q3** (business-facing, critiquing product, MANUAL): exploratory testing, usability testing, UAT.
  - **Q4** (tech-facing, critiquing product, TOOL-DRIVEN): performance, load, security, pruebas "-ility".

### 1.7 Shift-Left y Shift-Right

Ciclo de vida en cadena: Requirements → Design → Code → **Test** → Deploy → Monitor.

- **Shift-Left:** static testing, revisiones y diseño temprano de pruebas durante Requirements/Design/Code — atrapar defectos cuando es más barato corregirlos.
- **Shift-Right:** monitoreo, observabilidad, canary releases, feature flags y feedback de usuarios reales una vez el sistema está en producción.
- La estrategia moderna de calidad corre todo el ancho del ciclo de vida, no solo la caja "Test".

### 1.8 Puntos clave

- Una preocupación compartida de proceso-y-producto: QA ⊃ QC ⊃ Testing.
- Error → Defecto → Fallo: una equivocación, su rastro en el código, su efecto visible.
- Fundamentado en los siete principios de ISTQB.
- Balanceado (Pirámide vs. Trofeo, Cuadrantes) y de ciclo de vida completo (Shift-Left/Right).

---

## 2. Niveles de prueba

Marco general: **los niveles se apilan (Unit → Integration → System → Acceptance) y los tipos los cruzan (Funcional / No funcional).** Cada nivel se prueba en ambos sentidos. Smoke, sanity y regresión son *selecciones*, no niveles.

### 2.1 Unit testing (nivel 1 de 4)

- El nivel más básico de testing.
- Bloques de construcción más pequeños del sistema, en aislamiento.
- Escrito y corrido por **desarrolladores**.
- Siempre automatizado.

```python
# app.py
def to_upper(text): return text.upper()
def to_lower(text): return text.lower()

# test_app.py
def test_upper(): assert to_upper("a") == "A"
def test_lower(): assert to_lower("A") == "a"
```

- **Caso verde:** `$ pytest -q` → `..` → `2 passed in 0.01s`. Dos puntos, dos pruebas pasando. Esto dice que las dos funciones se comportan como se especificó *para las entradas elegidas*, nada más (principio 1: testing muestra la presencia de defectos, no su ausencia).
- **Caso rojo:** si `to_lower` accidentalmente se copia-pega de `to_upper` (usa `.upper()` en vez de `.lower()`): `$ pytest -q` → `.F` → `AssertionError: 'A' == 'a'` → `1 failed, 1 passed`.
  - Error → copió-pegó `to_upper`, olvidó el cuerpo.
  - Defecto → `.upper()` sentado dentro de `to_lower`.
  - Fallo → la aserción que acaba de ponerse en rojo.
- Un unit test convierte defectos en fallos temprano, mientras aún cuestan minutos, no millones.

### 2.2 Integration testing (nivel 2 de 4)

- ¿Las unidades todas funcionan? ¿Funcionan **juntas**?
- Corre después de unit testing; desarrolladores y testers combinan unidades.
- Apunta a las **interfaces** y a los datos que las cruzan.
- Dos niveles:
  - **Component integration:** interfaz entre dos módulos propios.
  - **System integration:** interfaz con un sistema o API de un tercero — p. ej. un servicio propio llama `getUserData(user)` a una API de partner, que responde `200 · data (JSON)`.
- Analogía del cajón y la puerta de cocina: el cajón pasó su inspección; la puerta del gabinete pasó su inspección. Una semana después de instalados, la cocina tiene un problema que el carpintero nunca vio: nadie abrió el cajón y la puerta al mismo tiempo.
- El contract testing (p. ej. Pact) vive en este nivel, fijando lo que cada lado promete.

### 2.3 System testing (nivel 3 de 4)

- El comportamiento y las capacidades del sistema **completo**.
- Corre después de integration, en un ambiente de prueba dedicado.
- End-to-end: el flujo completo que tomaría un usuario real.
- Propiedad de testers; produce la información detrás de las **decisiones de release**.
- Analogía "partes, ensamble, carro": volante, puertas, ruedas, motor (UNIT) → chasis ensamblado (INTEGRATION) → carro terminado (SYSTEM). Cada rueda pasando su propia inspección no dice que el carro maneja — ese es el argumento completo para probar en más de un nivel.
- Es la punta de la pirámide: mantenerlo delgado.

### 2.4 Acceptance testing (nivel 4 de 4)

- No "¿funciona?" sino "¿lo aceptamos?"
- Requiere criterios de aceptación acordados de antemano.
- Foco en el comportamiento del sistema completo, desde el lado del usuario.
- Construye confianza en que el sistema está completo y funciona como se espera.
- Encontrar un número significativo de defectos aquí es un **riesgo mayor de proyecto**: significa que los niveles anteriores no hicieron su trabajo.
- Ligado al principio 7 (la ausencia de defectos es una falacia).

**Cuatro formas de acceptance testing:**

| Forma | Quién prueba | Ambiente | ¿Público? |
|---|---|---|---|
| UAT | Usuarios reales o un equipo separado | ≈ producción | no |
| Alpha | Equipo de testing interno | ≈ producción | no |
| Beta | Usuarios reales, condiciones propias | = producción | **sí** |
| Contractual | Testers independientes, reguladores | varía | no |

Técnicas de UAT: error guessing, exploratory testing, checklist-based testing. Solo **beta** encuentra defectos ligados a ambientes que no se pueden reproducir en laboratorio.

### 2.5 Perspectiva por nivel

Entre más abajo se va en la pirámide, más se puede ver del sistema. Es una tendencia, no una regla: un unit test escrito solo contra un docstring es black box, y un test E2E que verifica la base de datos después es gray box.

| Nivel | Perspectiva predominante |
|---|---|
| Unit | White box |
| Integration | Gray box |
| System | Black box |
| Acceptance | Black box |

---

