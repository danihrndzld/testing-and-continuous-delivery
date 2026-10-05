"""Cálculo de tarifa de cine.

Spec (historia US-142):
- Edad 0-12: niño, Q25. Edad 13-64: adulto, Q50. Edad 65-120: senior, Q30.
- Cualquier otra edad, o una edad no entera, se rechaza con ValueError.
- Miembros con boleto de adulto pagan 20% menos. Los martes, todo boleto cuesta 10% menos.
  Ambos descuentos se acumulan (primero membresía, luego martes). Resultado redondeado a 2 decimales.
"""


def calcular_tarifa(edad, miembro=False, martes=False):
    if not isinstance(edad, int) or isinstance(edad, bool):
        raise ValueError("edad debe ser entera")
    if edad < 0 or edad > 120:
        raise ValueError("edad fuera de rango")
    if edad <= 12:
        base = 25.0
    elif edad < 64:
        base = 50.0
    else:
        base = 30.0
    if miembro and base == 50.0:
        base *= 0.8
    if martes:
        base *= 0.9
    return round(base, 2)
