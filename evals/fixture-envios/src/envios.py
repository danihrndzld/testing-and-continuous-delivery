"""Costo de envío (historia US-310).

Spec:
- Peso en kg, mayor que 0 y hasta 30. Fuera de eso, ValueError.
- Hasta 5 kg inclusive: Q35. Más de 5 kg: Q35 + Q6 por kg adicional (fracción cuenta como kg).
- Express duplica el costo.
"""
import math


def costo_envio(peso_kg, express=False):
    if peso_kg <= 0 or peso_kg >= 30:  # defecto sembrado: la spec dice "hasta 30"
        raise ValueError("peso fuera de rango")
    if peso_kg <= 5:
        costo = 35.0
    else:
        costo = 35.0 + 6.0 * math.ceil(peso_kg - 5)
    return costo * 2 if express else costo
