"""
Lógica del método gráfico para resolver problemas de programación lineal
de 2 variables de decisión (x1, x2).

Algoritmo:
1. Calcular los puntos de intersección entre cada par de restricciones
   (y con los ejes x1=0, x2=0), que son los candidatos a vértices.
2. Filtrar los que cumplen TODAS las restricciones (región factible).
3. Evaluar la función objetivo en cada vértice factible.
4. Elegir el mejor según se maximice o minimice.
"""

from itertools import combinations


def _evaluar_restriccion(restriccion, punto, tolerancia=1e-6):
    """Verifica si un punto (x1, x2) cumple una restricción dada."""
    valor = restriccion.coeficientes[0] * punto[0] + restriccion.coeficientes[1] * punto[1]
    if restriccion.operador == "<=":
        return valor <= restriccion.termino_independiente + tolerancia
    elif restriccion.operador == ">=":
        return valor >= restriccion.termino_independiente - tolerancia
    else:  # "="
        return abs(valor - restriccion.termino_independiente) <= tolerancia


def _interseccion(r1, r2):
    """
    Calcula el punto de intersección entre dos rectas a1*x1 + b1*x2 = c1
    y a2*x1 + b2*x2 = c2. Devuelve None si son paralelas (sin solución única).
    """
    a1, b1 = r1.coeficientes
    c1 = r1.termino_independiente
    a2, b2 = r2.coeficientes
    c2 = r2.termino_independiente

    determinante = a1 * b2 - a2 * b1
    if abs(determinante) < 1e-9:
        return None  # rectas paralelas, no hay intersección única

    x1 = (c1 * b2 - c2 * b1) / determinante
    x2 = (a1 * c2 - a2 * c1) / determinante
    return (x1, x2)


def calcular_region_factible(problema):
    """
    Calcula los vértices de la región factible de un problema de 2 variables.
    Devuelve una lista de puntos (x1, x2) que son factibles.
    """
    from modelos.datos import Restriccion

    eje_x1 = Restriccion([1, 0], "=", 0)  # x1 = 0
    eje_x2 = Restriccion([0, 1], "=", 0)  # x2 = 0

    todas_las_rectas = list(problema.restricciones) + [eje_x1, eje_x2]

    candidatos = []
    for r1, r2 in combinations(todas_las_rectas, 2):
        punto = _interseccion(r1, r2)
        if punto is not None:
            candidatos.append(punto)

    vertices_factibles = []
    for punto in candidatos:
        x1, x2 = punto
        if x1 < -1e-6 or x2 < -1e-6:
            continue
        if all(_evaluar_restriccion(r, punto) for r in problema.restricciones):
            vertices_factibles.append(punto)

    vertices_unicos = []
    for punto in vertices_factibles:
        if not any(
            abs(punto[0] - v[0]) < 1e-6 and abs(punto[1] - v[1]) < 1e-6
            for v in vertices_unicos
        ):
            vertices_unicos.append(punto)

    return vertices_unicos


def evaluar_funcion_objetivo(problema, punto):
    """Evalúa Z = c1*x1 + c2*x2 en un punto dado."""
    c1, c2 = problema.funcion_objetivo
    return c1 * punto[0] + c2 * punto[1]


def resolver_metodo_grafico(problema):
    """
    Resuelve el problema por método gráfico.
    Devuelve un diccionario con:
      - region_factible: lista de vértices (x1, x2)
      - punto_optimo: (x1, x2) del mejor vértice
      - valor_optimo: valor de Z en el punto óptimo
    Lanza ValueError si no hay región factible.
    """
    vertices = calcular_region_factible(problema)

    if not vertices:
        raise ValueError("No existe una región factible para este problema.")

    valores = [(punto, evaluar_funcion_objetivo(problema, punto)) for punto in vertices]

    if problema.tipo_optimizacion == "max":
        punto_optimo, valor_optimo = max(valores, key=lambda item: item[1])
    else:
        punto_optimo, valor_optimo = min(valores, key=lambda item: item[1])

    return {
        "region_factible": vertices,
        "punto_optimo": punto_optimo,
        "valor_optimo": valor_optimo,
    }