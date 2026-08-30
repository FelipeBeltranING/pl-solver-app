"""
Lógica del método simplex para maximización.

Alcance de esta primera versión: restricciones de tipo "<=" con término
independiente no negativo (el caso estándar con el que se suele empezar
a enseñar simplex). Convierte cada restricción en igualdad agregando una
variable de holgura, arma la tabla inicial y itera hasta la condición
de parada (todos los coeficientes de la fila Z son >= 0).
"""


def _construir_tabla_inicial(problema):
    """
    Arma la tabla simplex inicial a partir del problema.
    Devuelve (tabla, nombres_columnas, variables_basicas).
    """
    num_vars = problema.num_variables
    num_restricciones = problema.num_restricciones

    nombres_columnas = [f"x{i+1}" for i in range(num_vars)]
    nombres_columnas += [f"s{i+1}" for i in range(num_restricciones)]
    nombres_columnas += ["LD"]  # lado derecho

    tabla = []
    variables_basicas = []

    for i, restriccion in enumerate(problema.restricciones):
        if restriccion.operador != "<=":
            raise ValueError(
                "Esta versión del método simplex solo admite restricciones de tipo '<='."
            )
        if restriccion.termino_independiente < 0:
            raise ValueError(
                "Esta versión del método simplex requiere términos independientes no negativos."
            )

        fila = list(restriccion.coeficientes)
        # columnas de holgura: 1 en la propia restricción, 0 en las demás
        fila += [1 if j == i else 0 for j in range(num_restricciones)]
        fila.append(restriccion.termino_independiente)
        tabla.append(fila)
        variables_basicas.append(f"s{i+1}")

    # Fila Z: -coeficientes de la función objetivo (para maximizar), 0 en holguras, 0 en LD
    fila_z = [-c for c in problema.funcion_objetivo]
    fila_z += [0] * num_restricciones
    fila_z.append(0)
    tabla.append(fila_z)

    return tabla, nombres_columnas, variables_basicas


def _es_optima(tabla):
    """La solución es óptima cuando todos los coeficientes de la fila Z son >= 0."""
    fila_z = tabla[-1]
    return all(coef >= -1e-9 for coef in fila_z[:-1])


def _elegir_columna_pivote(tabla):
    """Columna con el coeficiente más negativo en la fila Z (regla estándar de entrada)."""
    fila_z = tabla[-1][:-1]
    return fila_z.index(min(fila_z))


def _elegir_fila_pivote(tabla, columna_pivote):
    mejor_fila = None
    mejor_razon = None
    for i in range(len(tabla) - 1):  # todas menos la fila Z
        coef = tabla[i][columna_pivote]
        if coef > 1e-9:
            razon = tabla[i][-1] / coef
            if mejor_razon is None or razon < mejor_razon:
                mejor_razon = razon
                mejor_fila = i
    return mejor_fila


def _pivotear(tabla, fila_pivote, columna_pivote):
    """Realiza la operación de pivoteo: normaliza la fila pivote y anula el resto de la columna."""
    num_filas = len(tabla)
    num_columnas = len(tabla[0])

    valor_pivote = tabla[fila_pivote][columna_pivote]
    tabla[fila_pivote] = [valor / valor_pivote for valor in tabla[fila_pivote]]

    for i in range(num_filas):
        if i != fila_pivote:
            factor = tabla[i][columna_pivote]
            if factor != 0:
                tabla[i] = [
                    tabla[i][j] - factor * tabla[fila_pivote][j]
                    for j in range(num_columnas)
                ]


def resolver_metodo_simplex(problema, max_iteraciones=50):
    """
    Resuelve el problema por método simplex (solo maximización, restricciones "<=").
    """
    
    if problema.tipo_optimizacion != "max":
        raise ValueError("El método simplex en esta aplicación solo admite maximización.")

    tabla, nombres_columnas, variables_basicas = _construir_tabla_inicial(problema)

    iteraciones = [[fila[:] for fila in tabla]]  # guardamos copia de cada estado

    contador = 0
    while not _es_optima(tabla):
        contador += 1
        if contador > max_iteraciones:
            raise ValueError("Se alcanzó el máximo de iteraciones sin encontrar el óptimo.")

        columna_pivote = _elegir_columna_pivote(tabla)
        fila_pivote = _elegir_fila_pivote(tabla, columna_pivote)

        if fila_pivote is None:
            raise ValueError("El problema es no acotado (no tiene solución óptima finita).")

        variables_basicas[fila_pivote] = nombres_columnas[columna_pivote]
        _pivotear(tabla, fila_pivote, columna_pivote)

        iteraciones.append([fila[:] for fila in tabla])

    num_vars = problema.num_variables
    solucion = {f"x{i+1}": 0 for i in range(num_vars)}

    for i, nombre_var in enumerate(variables_basicas):
        if nombre_var in solucion:
            solucion[nombre_var] = tabla[i][-1]

    valor_optimo = tabla[-1][-1]

    return {
        "iteraciones": iteraciones,
        "nombres_columnas": nombres_columnas,
        "variables_basicas_final": variables_basicas,
        "solucion": solucion,
        "valor_optimo": valor_optimo,
    }