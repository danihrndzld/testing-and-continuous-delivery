# Técnicas de diseño de pruebas y TDD

## 5. Técnicas de diseño de pruebas

**Por qué existen las técnicas:** el testing exhaustivo es imposible (principio 2). Un campo de texto de 8 caracteres, letras y dígitos, da 36⁸ ≈ 2.8 billones de strings de entrada; a 1 ms por test son 89 años corriendo sin parar. Lo que realmente se obtiene son ~10 tests este sprint — **elegidos, no muestreados**. Una técnica de prueba elige esos diez y justifica el resto.

**Tres familias de técnica:**

- **Black-box (spec-based):** desde la especificación. Sin referencia al código.
- **White-box (structure-based):** desde el código: rutas, ramas, estado.
- **Experience-based (tester-driven):** desde lo que el tester ya sabe.

Black-box y white-box son sistemáticas. Experience-based atrapa lo que un sistema se pierde, precisamente porque no lo es.

### 5.1 Equivalence Partitioning (EP)

**Concepto:** agrupar entradas para que cada valor de un grupo reciba el mismo tratamiento. Un valor habla por toda la partición: si revela un defecto, cualquier otro valor de esa partición debería también. Las particiones pueden ser **válidas** (aceptadas) o **inválidas** (rechazadas). Cobertura: particiones ejercitadas ÷ particiones identificadas. Así es como una entrada sin límites se vuelve una lista corta y defendible de clases que vale la pena probar.

**Ejemplo trabajado — boletos de cine por edad.** Spec: 0-12 niño, 13-64 adulto, 65-120 senior; cualquier otra edad se rechaza. Un campo, toma un número. Cuidado con el conteo: las edades rechazadas también son clases, y también lo es una entrada no numérica.

| Clase | Rango | Valor de prueba |
|---|---|---|
| inválido | `age < 0` | -3 |
| child | 0-12 | 7 |
| adult | 13-64 | 30 |
| senior | 65-120 | 70 |
| inválido | `age > 120` | 130 |
| inválido | no es un número entero | `"abc"` |

Seis clases, seis tests. Agregar `31` no compra nada: cae en la clase de `30`, así que solo puede encontrar lo que `30` ya encuentra.

### 5.2 Boundary Value Analysis (BVA)

**Concepto:** probar los bordes de las particiones ya encontradas. Solo funciona en particiones **ordenadas**: los valores frontera son su mínimo y máximo. Los desarrolladores se equivocan más en las fronteras que en el medio de un rango (un off-by-one, un `<` incorrecto). Forma más simple: probar el límite, más su vecino más cercano justo afuera de la partición. BVA no reemplaza equivalence partitioning, la afina.

**Ejemplo trabajado.** Spec: un campo *Name*, solo letras, de 5 a 12 caracteres.

- **Equivalence Partitioning** (un test por clase): invalid `< 5`, valid `5-12`, invalid `> 12`.
- **Boundary Value Analysis** (probar donde la validez cambia): 4, 5, 6, 11, 12, 13 — cubriendo las dos transiciones, "invalid → valid" (entre 4 y 5) y "valid → invalid" (entre 12 y 13).
- Seis valores en vez de miles. `4` y `13` son las pruebas negativas, donde viven los defectos off-by-one.

**Negative testing:** también llamado error-path o failure testing. Valida cómo se comporta la aplicación con datos **inválidos**. Los usuarios reales producen mucho más entrada inválida que válida. Equivalence partitioning y boundary value analysis son las dos técnicas que responden cuáles valores inválidos vale la pena probar.

### 5.3 Decision Table Testing

**Concepto:** para cuando el resultado depende de una **combinación** de condiciones, no solo una. Las filas son las condiciones y acciones; cada columna es una **regla**, una combinación de valores T/F. Una tabla completa tiene una columna por combinación; las infactibles pueden eliminarse. Cobertura: reglas factibles ejercitadas ÷ reglas factibles identificadas. Construir la tabla es la mitad del valor: poner cada combinación en fila tiende a exponer una regla que nadie había escrito.

**Ejemplo trabajado — envío gratis + descuento.**

*Spec en prosa:* "El carrito envía gratis cuando el total llega a Q200 o el cliente es miembro leal. Miembros con un carrito de Q200 o más también obtienen un 10% extra de descuento."

**Paso 1 — de prosa a condiciones:**

- Condiciones: C1 — ¿Cart total ≥ Q200? / C2 — ¿Loyalty member?
- Acciones: A1 — Free shipping / A2 — Extra 10% off
- Dos condiciones, cada una true o false: 2² = 4 columnas. Cada columna es una **regla**, y un caso de prueba.

**Paso 2 — llenar cada columna, luego leerla de vuelta:**

| | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| C1: Cart total ≥ Q200 | T | T | F | F |
| C2: Loyalty member | T | F | T | F |
| A1: Free shipping | ✓ | ✓ | ✓ | ✗ |
| A2: Extra 10% off | ✓ | ✗ | ✗ | ✗ |
| lee como | Q250, member | Q250, guest | Q80, member | Q80, guest |

✓ significa que la acción se dispara, ✗ que no. C1 alterna en pares, C2 uno por uno: ninguna combinación queda fuera.

**Paso 3 — las reglas se vuelven casos de prueba:**

| Regla | Entrada | Resultado esperado |
|---|---|---|
| R1 | Cart Q250, miembro autenticado | Shipping Q0, total Q225 (ambas acciones disparan) |
| R2 | Cart Q250, guest checkout | Shipping Q0, total Q250 (sin descuento extra) |
| R3 | Cart Q80, miembro autenticado | Shipping Q0, total Q80 (sin descuento extra) |
| R4 | Cart Q80, guest checkout | Shipping cobrado, total Q80 (ninguna acción) |

**El defecto que solo la tabla completa encuentra:**

```python
# el desarrollador cablea ambas acciones a partir de la misma condición
free_shipping = total >= 200 or is_member
extra_discount = total >= 200 or is_member   # debería ser 'and'
```

- R1: Q250 member — ambas se disparan, la spec quiere ambas. **Pasa.**
- R4: Q80 guest — ninguna se dispara, la spec quiere ninguna. **Pasa.**
- R2: Q250 guest — el código agrega el 10% de descuento. **Atrapado.**
- R3: Q80 member — el código agrega el 10% de descuento. **Atrapado.**

La intuición escribe R1 y R4 primero, todo-verdadero luego todo-falso: exactamente los dos que este código sobrevive. Por eso se necesitan las cuatro columnas.

### 5.4 State Transition Testing

**Concepto:** para cuando lo que pasa después depende de lo que ya pasó. Un **diagrama de estados** modela los estados y los eventos entre ellos: `event [guard] / action`. Una **tabla de estados** es el mismo modelo en grilla; una celda vacía es una transición inválida. Cobertura: **all states**, **valid transitions** (el baseline común), o **all transitions** (válidas e inválidas por igual). Las transiciones inválidas importan también: ¿qué debería pasar cuando el sistema recibe un evento que no espera, en ese estado?

**Notación:**

`Logged out → [wrong password] [attempt = 3] / lock the account → Locked`

| Parte | Significa |
|---|---|
| State | Lo que el sistema recuerda ahora mismo: `Logged out`, `Locked` |
| Event | Lo que llega desde afuera y puede moverlo: una contraseña incorrecta |
| Guard | Una condición sobre el evento. Mismo evento, destino distinto |
| Action | Lo que el sistema hace en el camino: bloquear la cuenta, enviar un correo |
| Transition | La flecha completa: state + event + guard → new state |

El guard es donde se esconden los defectos: un evento, dos destinos, decidido por un contador.

**Ejemplo trabajado — login con tres estados:**

- `Logged out` --correct password--> `Logged in`
- `Logged in` --logout--> `Logged out`
- `Logged out` --wrong password (loop sobre sí mismo)--> `Logged out`
- `Logged out` --3rd wrong password--> `Locked`
- `Locked` --admin unlock--> `Logged out`

La secuencia `wrong, wrong, wrong, correct` camina cuatro transiciones en un solo caso: el loop y la caída a *Locked* comparten un evento, y el **guard** decide cuál se dispara.

| Caso | Secuencia de eventos | Cubre |
|---|---|---|
| TC1 | correct password, logout | Logged out → in → out |
| TC2 | wrong, wrong, wrong, admin unlock | El loop, la caída guardada a Locked, el unlock |
| TC3 | desde Logged out, enviar `logout` | Una transición inválida: esperar un rechazo limpio |

- **All states:** TC1 y TC2 solos alcanzan los tres.
- **All valid transitions:** TC1 + TC2 caminan cada flecha del diagrama, el baseline usual.
- **All transitions:** necesita TC3 y sus similares, uno por cada evento que un estado nunca debería recibir.

### 5.5 White-box: statement coverage vs. branch coverage

**Concepto:** una vez el código existe, las técnicas pueden medir qué corrieron realmente las pruebas.

- **Statement coverage:** el porcentaje de líneas ejecutables corridas al menos una vez.
- **Branch coverage:** el porcentaje de resultados verdadero/falso ejercitados en cada punto de decisión.
- Branch coverage **subsume** statement coverage: 100% de branch siempre da 100% de statement, nunca al revés.

**Ejemplo trabajado — un test, la mitad de la lógica de decisión:**

```python
def grade(score):
    result = "fail"            # corre, sobreescrito después
    if score >= 60:            # True con 95. False: nunca probado
        result = "pass"        # corre
    if score >= 90:            # True con 95. False: nunca probado
        result = "honors"      # corre
    return result              # corre
```

La suite entera es un solo test, `grade(95)`. Cada línea corrió: **statement coverage 100%**. Solo dos de los cuatro resultados verdadero/falso ocurrieron: **branch coverage 50%**. Agregar `grade(45)` fuerza ambos `if` a `False` y cierra el resto.

**Coverage ≠ correcto:** la cobertura dice qué corrió, nunca qué se verificó realmente.

- Ejecutar una línea no garantiza que un defecto ahí se atrape: una división por cero solo falla para un denominador exacto.
- Cobertura es un piso, no un veredicto: una suite puede llegar a 100% de branch coverage mientras no asegura casi nada.
- Una suite que alcanza cada línea sin atrapar un bug plantado a propósito no es débil: la métrica está midiendo lo equivocado. **Mutation testing** mide calidad de pruebas directamente, insertando defectos y verificando que la suite los detecte.

### 5.6 Técnicas basadas en experiencia

1. **Error guessing:** predecir dónde se esconden los defectos, a partir de cómo ha fallado esta app antes.
2. **Exploratory testing:** diseñar, correr y evaluar pruebas a la vez, a menudo en sesión time-boxed guiada por un *charter*.
3. **Checklist-based testing:** trabajar a través de condiciones construidas de la experiencia o de patrones de fallo conocidos.

Estas tres son también las técnicas típicas de UAT: ninguna especificación captura completamente lo que hará un usuario real.

| Técnica | Se ve como |
|---|---|
| Error guessing | "Este formulario crasheó con entrada de emoji la release pasada, probarlo de nuevo." |
| Exploratory | Una sesión de 45 minutos, charter: *encontrar formas en que el botón atrás confunde el checkout* |
| Checklist-based | Heurística #1 de Nielsen: ¿toda acción da feedback dentro de un segundo? |

Ninguna necesita una spec escrita primero — eso es lo que las hace **complementarias** al black-box y white-box testing, no un sustituto de ninguno.

### 5.7 Guía de decisión: qué técnica usar cuándo

| Si... | Usar... |
|---|---|
| Rangos válidos e inválidos | Particiones de equivalencia + valores frontera |
| Reglas se combinan para decidir el resultado | Decision table testing |
| El comportamiento depende de lo que pasó antes | State transition testing |
| El código existe; hace falta saber qué corrió | Statement & branch coverage |
| Spec delgada, o se conoce la historia de esta app | Error guessing, exploratory, checklists |

Estas técnicas no son solo para comportamiento funcional: las mismas técnicas diseñan casos de prueba no funcionales también.

### 5.8 Puntos clave

- Explicar por qué el testing exhaustivo es imposible, y qué compra una técnica.
- Diseñar casos con particiones, fronteras, tablas de decisión y transiciones de estado.
- Distinguir statement de branch coverage, y por qué 100% no prueba que ninguno sea correcto.
- Recurrir a error guessing, exploratory o checklist-based testing, y justificar la elección.

---

## 6. TDD y calidad del código nuevo

### 6.1 Test-last vs. test-first

Las técnicas de diseño asumen que el código ya existe. No tiene que ser así.

- **Test-last:** construir la característica, luego diseñar casos contra ella. Las técnicas siguen funcionando, pero el código moldea las pruebas.
- **Test-first:** escribir la prueba que falla, luego el código que la hace pasar. La prueba moldea el código.
- Test-Driven Development es la segunda opción, convertida en un loop.

### 6.2 Red, Green, Refactor

1. **Red.** Escribir un test que falla para un comportamiento que aún no existe. Correrlo, y verlo fallar por la razón esperada.
2. **Green.** Escribir el mínimo código que pasa. Feo está permitido aquí.
3. **Refactor.** Limpiar el código con la suite en verde, para que cualquier daño aparezca de inmediato.

El loop es corto a propósito: minutos, no días. Un test que falla por la razón equivocada es lo único que lo rompe.

**Ejemplo micro-trabajado — construyendo `grade()` desde sus tests:**

```python
# RED — el test viene primero
def test_ninety_is_honors():
    assert grade(90) == "honors"
# falla: grade() no existe
```

```python
# GREEN — el mínimo código que pasa
def grade(score):
    return "honors"
# sí, de verdad. pasa.
```

Esa trampa es el punto: prueba que el test puede fallar, y hace que el *siguiente* test haga trabajo real. `grade(59) == "fail"` es lo que fuerza la rama; `59`, `60`, `89` y `90` son los valores frontera de la sección anterior, reutilizados aquí como los tests que fuerzan al código a existir.

### 6.3 Clean as You Code

Mantener un estándar en el código que se toca, no en el que se heredó.

- **Código nuevo** es lo que la definición del proyecto cubre: en un pull request, cada línea agregada o cambiada.
- El gate corre solo en código nuevo: sin bugs o vulnerabilidades nuevas, hotspots revisados, límites de duplicación y cobertura.
- Se responde por lo que se escribió, no por el módulo que alguien entregó en 2015.
- Sin sprint de limpieza, sin reescritura.

### 6.4 El half-life de una línea de código

*Git of Theseus* camina toda la historia de un repositorio y pregunta, de cada línea jamás escrita, si sigue ahí. Graficado como cohortes apiladas: cada banda es el código agregado en un año; el repo crece, y cada banda se encoge después de su propio año. La curva de supervivencia agregada cruza 50% alrededor de los 3.33 años.

| Repo | Half-life |
|---|---|
| Linux | 6.60 años |
| Git | 6.04 años |
| Django | 3.38 años |
| Rails | 2.43 años |
| Angular | 0.32 años |
| **Agregado** | **3.33 años** |

**Por qué gatear código nuevo termina limpiando el viejo:**

- La mitad de las líneas desaparecen en pocos años, así que la mayoría del repo vuelve a pasar por el editor de alguien.
- El momento en que se edita una línea, cuenta como **código nuevo**, y tiene que cumplir el estándar.
- El legado se limpia a la velocidad a la que el código rota, sin sprint de deuda dedicado.
- TDD hace esto barato: el código nuevo llega con sus tests, cumpliendo la condición de cobertura en el camino.
- Qué tan rápido depende del proyecto: Angular reemplazó la mitad de su código en cuatro meses, Linux tomó más de seis años.

---

