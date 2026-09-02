"""
Lógica del método simplex para maximización.

Alcance de esta primera versión: restricciones de tipo "<=" con término
independiente no negativo (el caso estándar con el que se suele empezar
a enseñar simplex). Convierte cada restricción en igualdad agregando una
variable de holgura, arma la tabla inicial y itera hasta la condición
de parada (todos los coeficientes de la fila Z son >= 0).
"""


def _construir_tabla_inicial(problema):
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
    """
    Prueba de la razón mínima: entre las filas con coeficiente positivo en la
    columna pivote, la que tenga menor LD/coeficiente sale de la base.
    Devuelve None si el problema es no acotado (sin fila válida).
    """
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

    Devuelve un diccionario con:
      - iteraciones: lista de tablas (una copia por cada paso, para mostrarlas en la interfaz)
      - descripciones: lista de textos explicando qué ocurrió en cada paso
      - variables_basicas_por_iteracion: lista con las variables básicas vigentes en cada tabla
      - variables_basicas_final: nombres de las variables en la base al terminar
      - solucion: diccionario {variable: valor} con los valores de x1..xn
      - valor_optimo: valor final de Z
    Lanza ValueError si el problema no cumple los requisitos o es no acotado.
    """
    if problema.tipo_optimizacion != "max":
        raise ValueError("El método simplex en esta aplicación solo admite maximización.")

    tabla, nombres_columnas, variables_basicas = _construir_tabla_inicial(problema)

    iteraciones = [[fila[:] for fila in tabla]]  # guardamos copia de cada estado
    variables_basicas_por_iteracion = [list(variables_basicas)]
    descripciones = [
        "Tabla inicial: se agregó una variable de holgura por cada restricción "
        "(s1, s2, ...) para convertirlas en igualdades. La base inicial está "
        f"formada por las variables de holgura: {', '.join(variables_basicas)}."
    ]

    contador = 0
    while not _es_optima(tabla):
        contador += 1
        if contador > max_iteraciones:
            raise ValueError("Se alcanzó el máximo de iteraciones sin encontrar el óptimo.")

        columna_pivote = _elegir_columna_pivote(tabla)
        fila_pivote = _elegir_fila_pivote(tabla, columna_pivote)

        if fila_pivote is None:
            raise ValueError("El problema es no acotado (no tiene solución óptima finita).")

        variable_entra = nombres_columnas[columna_pivote]
        variable_sale = variables_basicas[fila_pivote]
        valor_pivote = tabla[fila_pivote][columna_pivote]

        variables_basicas[fila_pivote] = variable_entra
        _pivotear(tabla, fila_pivote, columna_pivote)

        iteraciones.append([fila[:] for fila in tabla])
        variables_basicas_por_iteracion.append(list(variables_basicas))
        descripciones.append(
            f"Iteración {contador}: entra a la base la variable {variable_entra} "
            f"(columna con el coeficiente más negativo en la fila Z). Sale de la base "
            f"la variable {variable_sale} (fila con la menor razón LD/coeficiente, "
            f"elemento pivote = {valor_pivote:.2f}). Se normaliza la fila pivote y se "
            f"anulan los demás valores de esa columna."
        )

    # Construir la solución final: valor de cada variable de decisión
    num_vars = problema.num_variables
    solucion = {f"x{i+1}": 0 for i in range(num_vars)}

    for i, nombre_var in enumerate(variables_basicas):
        if nombre_var in solucion:
            solucion[nombre_var] = tabla[i][-1]

    valor_optimo = tabla[-1][-1]

    texto_solucion = ", ".join(f"{var}={valor:.2f}" for var, valor in solucion.items())
    descripciones.append(
        f"Solución óptima alcanzada: todos los coeficientes de la fila Z son >= 0, "
        f"no hay más mejora posible. Resultado: {texto_solucion}, con Z = {valor_optimo:.2f}."
    )

    return {
        "iteraciones": iteraciones,
        "descripciones": descripciones,
        "nombres_columnas": nombres_columnas,
        "variables_basicas_por_iteracion": variables_basicas_por_iteracion,
        "variables_basicas_final": variables_basicas,
        "solucion": solucion,
        "valor_optimo": valor_optimo,
    }