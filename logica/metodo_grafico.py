"""
Lógica del método gráfico (problemas de 2 variables: x1, x2).

Así se resuelve, en el mismo orden en que se hace a mano en papel:
  1. Se calculan los puntos donde se cruzan cada par de rectas
     (las restricciones y los ejes x1=0, x2=0).
  2. De esos cruces, se descartan los que no cumplen alguna restricción.
     Los que sobreviven son los vértices de la región factible.
  3. Se calcula el valor de la función objetivo Z en cada vértice.
  4. Se elige el vértice con mejor Z (el mayor si es maximizar,
     el menor si es minimizar).
"""

from modelos.datos import Restriccion


def resolver_metodo_grafico(problema):
    """
    Resuelve un problema de programación lineal de 2 variables.
    Devuelve un diccionario con la región factible, el punto óptimo y su valor de Z.
    """
    # Agregamos los ejes x1=0 y x2=0 como si fueran restricciones más,
    # porque las variables de decisión no pueden ser negativas.
    rectas = list(problema.restricciones)
    rectas.append(Restriccion([1, 0], "=", 0))  # eje x1 = 0
    rectas.append(Restriccion([0, 1], "=", 0))  # eje x2 = 0

    # Paso 1: calcular el cruce entre cada par de rectas
    cruces = []
    for i in range(len(rectas)):
        for j in range(i + 1, len(rectas)):
            punto = _cruce_de_dos_rectas(rectas[i], rectas[j])
            if punto is not None:
                cruces.append(punto)

    # Paso 2: quedarnos solo con los puntos que cumplen TODAS las
    # restricciones originales (esos son los vértices de la región factible)
    vertices = []
    for punto in cruces:
        x1, x2 = punto
        if x1 < -1e-6 or x2 < -1e-6:
            continue  # no puede haber valores negativos
        if all(_cumple_restriccion(r, punto) for r in problema.restricciones):
            vertices.append(punto)

    vertices = _quitar_puntos_repetidos(vertices)

    if not vertices:
        raise ValueError("No existe una región factible para este problema.")

    # Pasos 3 y 4: evaluar Z en cada vértice y quedarnos con el mejor
    mejor_punto, mejor_valor = vertices[0], _evaluar_z(problema, vertices[0])
    for punto in vertices[1:]:
        valor = _evaluar_z(problema, punto)
        if problema.tipo_optimizacion == "max" and valor > mejor_valor:
            mejor_punto, mejor_valor = punto, valor
        elif problema.tipo_optimizacion == "min" and valor < mejor_valor:
            mejor_punto, mejor_valor = punto, valor

    return {
        "region_factible": vertices,
        "punto_optimo": mejor_punto,
        "valor_optimo": mejor_valor,
    }


def _cruce_de_dos_rectas(r1, r2):
    """Calcula dónde se cruzan dos rectas a1*x1 + b1*x2 = c1 y a2*x1 + b2*x2 = c2."""
    a1, b1 = r1.coeficientes
    c1 = r1.termino_independiente
    a2, b2 = r2.coeficientes
    c2 = r2.termino_independiente

    denominador = a1 * b2 - a2 * b1
    if abs(denominador) < 1e-9:
        return None  # rectas paralelas: no se cruzan en un solo punto

    x1 = (c1 * b2 - c2 * b1) / denominador
    x2 = (a1 * c2 - a2 * c1) / denominador
    return (x1, x2)


def _cumple_restriccion(restriccion, punto):
    """Revisa si el punto (x1, x2) cumple una restricción dada."""
    valor = restriccion.coeficientes[0] * punto[0] + restriccion.coeficientes[1] * punto[1]
    tolerancia = 1e-6
    if restriccion.operador == "<=":
        return valor <= restriccion.termino_independiente + tolerancia
    if restriccion.operador == ">=":
        return valor >= restriccion.termino_independiente - tolerancia
    return abs(valor - restriccion.termino_independiente) <= tolerancia


def _evaluar_z(problema, punto):
    """Calcula Z = c1*x1 + c2*x2 en un punto dado."""
    c1, c2 = problema.funcion_objetivo
    return c1 * punto[0] + c2 * punto[1]


def _quitar_puntos_repetidos(puntos):
    """Elimina puntos duplicados que pueden aparecer por redondeo."""
    unicos = []
    for p in puntos:
        repetido = any(abs(p[0] - u[0]) < 1e-6 and abs(p[1] - u[1]) < 1e-6 for u in unicos)
        if not repetido:
            unicos.append(p)
    return unicos