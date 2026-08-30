"""
Validaciones del resolvedor de programación lineal.

El usuario elige el método (gráfico o simplex) desde la interfaz; estas
funciones validan si esa elección es válida según las dimensiones del
problema ingresado.

Reglas definidas:
- Método gráfico: exactamente 2 variables de decisión. El número de
  restricciones es libre (puede ser 1, 2, 3...). Admite maximización
  o minimización.
- Método simplex: solo maximización, y 2 o más restricciones. El número
  de variables es libre (puede usarse incluso con 2 variables si el
  usuario así lo elige).
"""

GRAFICO = "grafico"
SIMPLEX = "simplex"


def validar_para_grafico(problema):
    if problema.num_variables != 2:
        return False, "El método gráfico requiere exactamente 2 variables (x1 y x2)."
    return True, ""


def validar_para_simplex(problema):
    if problema.tipo_optimizacion != "max":
        return False, "El método simplex en esta aplicación solo admite maximización."
    if problema.num_restricciones < 2:
        return False, "El método simplex requiere al menos 2 restricciones."
    return True, ""