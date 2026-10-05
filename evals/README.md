# Evals

Dos niveles de regresión para la skill.

## 1. Script (determinista, 3 s)

```bash
uv run --no-project --with pytest --with pypdf pytest evals/test_armar_reporte.py -q
```

`fixture-envios/` trae un `reporte.json`, el `junit.xml` y el `coverage.json` de una corrida real con un defecto sembrado en `src/envios.py:12` (`>= 30` en lugar de `> 30`). Las 9 pruebas verifican que `armar_reporte.py`:

- genera HTML y PDF con conteos tomados del JUnit (`8 de 9 pruebas pasan`) e índice con páginas reales;
- numera las citas por clave;
- cambia a modo corto cuando ningún riesgo es alto;
- rechaza tests sin ID documentado, fallas sin defecto, defectos sobre casos que pasan, `archivo:línea` que no contiene el ID, IDs inexistentes, código como oráculo y supuestos sin lista.

Si se regeneran los artefactos del fixture:

```bash
cd evals/fixture-envios
uv run --no-project --with pytest --with pytest-cov pytest -p no:cacheprovider \
  --junitxml=junit.xml --cov=src --cov-branch --cov-report=json:coverage.json; rm -f .coverage
```

## 2. Agente (manual, ~6 min)

`demo-tarifas/` es un proyecto sin pruebas con un defecto sembrado que solo una técnica de frontera encuentra. No contiene respuestas: no agregar pruebas ni reportes aquí.

Copiar el proyecto a un directorio temporal y lanzar un agente nuevo con:

> Usa la skill testing-and-continuous-delivery tal como está escrita para diseñar, implementar y ejecutar pruebas de `calcular_tarifa` en `<copia>/src/tarifas.py` (la spec está en su docstring). Usa `uv`. Entrega todo lo que la skill exige. Al terminar, lista los archivos creados, los resultados, las páginas del PDF y cada instrucción de la skill que fue ambigua, contradictoria o faltante.

**Pasa si:**

1. Un caso BVA en la edad 64 falla y queda documentado como defecto de severidad alta en `tarifas.py:18`; el esperado no se ajustó.
2. `armar_reporte.py` terminó sin errores de validación y generó `reportes-pruebas/<fecha>-*/reporte.pdf`.
3. El reporte salió en modo completo (la frontera de precio es riesgo alto) con definición, por qué, derivación, casos y límites por técnica.
4. `base_de_prueba.tipo` es `spec` y cita el docstring.
5. La lista de ambigüedades del agente no repite un problema ya corregido en la skill.
