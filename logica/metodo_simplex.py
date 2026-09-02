"""
Lógica del método simplex (solo maximización, restricciones "<=").

Así se resuelve, en el mismo orden en que se hace a mano con la tabla simplex:
  1. Se arma la tabla inicial: una fila por restricción (agregando una
     variable de holgura por cada una) y una fila para la función objetivo (Z).
  2. Mientras la fila Z tenga algún número negativo, el problema se puede mejorar:
       a) Se elige la columna con el número más negativo de la fila Z
          (esa es la variable que entra a la base).
       b) Se elige la fila con la menor razón LD/coeficiente
          (esa es la variable que sale de la base).
       c) Se "pivotea": se deja 1 en la posición pivote y 0 en el resto de esa columna.
  3. Cuando ya no hay negativos en la fila Z, se llegó a la solución óptima.
"""


def resolver_metodo_simplex(problema, max_iteraciones=50):
    """
    Resuelve un problema de maximización con restricciones "<=" por método simplex.
    Devuelve un diccionario con las tablas de cada paso, su explicación,
    y la solución óptima final.
    """
    if problema.tipo_optimizacion != "max":
        raise ValueError("El método simplex en esta aplicación solo admite maximización.")

    num_vars = problema.num_variables
    num_restricciones = problema.num_restricciones
    nombres_columnas = (
        [f"x{i+1}" for i in range(num_vars)]
        + [f"s{i+1}" for i in range(num_restricciones)]
        + ["LD"]
    )

    # Paso 1: armar la tabla inicial
    tabla = []
    variables_basicas = []
    for i, restriccion in enumerate(problema.restricciones):
        if restriccion.operador != "<=":
            raise ValueError("Esta versión del método simplex solo admite restricciones '<='.")
        if restriccion.termino_independiente < 0:
            raise ValueError("El término independiente de cada restricción debe ser >= 0.")

        fila = list(restriccion.coeficientes)
        fila += [1 if j == i else 0 for j in range(num_restricciones)]  # variable de holgura
        fila.append(restriccion.termino_independiente)
        tabla.append(fila)
        variables_basicas.append(f"s{i+1}")

    fila_z = [-c for c in problema.funcion_objetivo] + [0] * num_restricciones + [0]
    tabla.append(fila_z)

    iteraciones = [_copiar(tabla)]
    descripciones = [
        f"Tabla inicial: se agregó una variable de holgura por restricción. "
        f"La base inicial es: {', '.join(variables_basicas)}."
    ]

    # Paso 2: iterar mientras la fila Z tenga negativos
    contador = 0
    while any(v < -1e-9 for v in tabla[-1][:-1]):
        contador += 1
        if contador > max_iteraciones:
            raise ValueError("Se alcanzó el máximo de iteraciones sin encontrar el óptimo.")

        columna = tabla[-1][:-1].index(min(tabla[-1][:-1]))  # columna con el más negativo
        fila = _fila_con_menor_razon(tabla, columna)
        if fila is None:
            raise ValueError("El problema es no acotado (no tiene solución óptima finita).")

        entra, sale = nombres_columnas[columna], variables_basicas[fila]
        variables_basicas[fila] = entra
        _pivotear(tabla, fila, columna)

        iteraciones.append(_copiar(tabla))
        descripciones.append(f"Iteración {contador}: entra {entra} a la base, sale {sale}.")

    # Paso 3: leer la solución final desde la tabla
    solucion = {f"x{i+1}": 0 for i in range(num_vars)}
    for i, variable in enumerate(variables_basicas):
        if variable in solucion:
            solucion[variable] = tabla[i][-1]
    valor_optimo = tabla[-1][-1]

    texto_solucion = ", ".join(f"{v}={val:.2f}" for v, val in solucion.items())
    descripciones.append(f"Solución óptima: {texto_solucion}, con Z = {valor_optimo:.2f}.")

    return {
        "iteraciones": iteraciones,
        "descripciones": descripciones,
        "nombres_columnas": nombres_columnas,
        "solucion": solucion,
        "valor_optimo": valor_optimo,
    }


def _fila_con_menor_razon(tabla, columna):
    """Prueba de la razón mínima: elige qué variable sale de la base."""
    mejor_fila, mejor_razon = None, None
    for i in range(len(tabla) - 1):
        coef = tabla[i][columna]
        if coef > 1e-9:
            razon = tabla[i][-1] / coef
            if mejor_razon is None or razon < mejor_razon:
                mejor_fila, mejor_razon = i, razon
    return mejor_fila


def _pivotear(tabla, fila_pivote, columna_pivote):
    """Deja 1 en la posición pivote y 0 en el resto de esa columna."""
    pivote = tabla[fila_pivote][columna_pivote]
    tabla[fila_pivote] = [v / pivote for v in tabla[fila_pivote]]
    for i in range(len(tabla)):
        if i != fila_pivote:
            factor = tabla[i][columna_pivote]
            if factor != 0:
                tabla[i] = [
                    tabla[i][j] - factor * tabla[fila_pivote][j] for j in range(len(tabla[i]))
                ]


def _copiar(tabla):
    """Copia el estado actual de la tabla (para guardar el historial de pasos)."""
    return [fila[:] for fila in tabla]