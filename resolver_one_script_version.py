"""
Resolvedor de Programación Lineal - Método Gráfico y Método Simplex
=====================================================================
Aplicación de escritorio en Python (Tkinter + Matplotlib) para resolver
problemas de programación lineal:
  - Método gráfico: 2 variables de decisión, maximización o minimización.
  - Método simplex: solo maximización, restricciones "<=".

Este archivo contiene toda la aplicación en un solo módulo (entregable).
Está organizado en las mismas secciones que el proyecto original en
varios archivos, para que sea fácil de ubicar y explicar:

  1. MODELOS DE DATOS      -> clases Restriccion y ProblemaPL
  2. VALIDACIONES          -> reglas para habilitar cada método
  3. LÓGICA MÉTODO GRÁFICO -> cálculo de región factible y óptimo
  4. LÓGICA MÉTODO SIMPLEX -> tabla simplex e iteraciones
  5. INTERFAZ GRÁFICA      -> las 4 ventanas de la aplicación
  6. PUNTO DE ENTRADA      -> arranque de la app
"""

import tkinter as tk
from tkinter import messagebox, ttk
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


# =====================================================================
# 1. MODELOS DE DATOS
# =====================================================================

@dataclass
class Restriccion:
    """
    Representa una restricción del problema de programación lineal.

    coeficientes: lista de coeficientes de las variables, ej. [a1, a2] para a1*x1 + a2*x2
    operador: "<=", ">=" o "="
    termino_independiente: valor al lado derecho de la restricción (b)
    """
    coeficientes: list
    operador: str
    termino_independiente: float

    def __post_init__(self):
        operadores_validos = ("<=", ">=", "=")
        if self.operador not in operadores_validos:
            raise ValueError(
                f"Operador '{self.operador}' no válido. Debe ser uno de {operadores_validos}"
            )


@dataclass
class ProblemaPL:
    """
    Representa el problema completo de programación lineal.

    tipo_optimizacion: "max" o "min"
    funcion_objetivo: lista de coeficientes, ej. [c1, c2] para Z = c1*x1 + c2*x2
    restricciones: lista de objetos Restriccion
    """
    tipo_optimizacion: str
    funcion_objetivo: list
    restricciones: list = field(default_factory=list)

    def __post_init__(self):
        if self.tipo_optimizacion not in ("max", "min"):
            raise ValueError("tipo_optimizacion debe ser 'max' o 'min'")

    @property
    def num_variables(self):
        return len(self.funcion_objetivo)

    @property
    def num_restricciones(self):
        return len(self.restricciones)


# =====================================================================
# 2. VALIDACIONES
# =====================================================================
# El usuario elige el método (gráfico o simplex) desde la interfaz;
# estas funciones validan si esa elección es válida según las
# dimensiones del problema ingresado.

GRAFICO = "grafico"
SIMPLEX = "simplex"


def validar_para_grafico(problema):
    """
    Valida que el problema cumpla los requisitos del método gráfico.
    Devuelve (True, "") si es válido, o (False, mensaje_error) si no.
    """
    if problema.num_variables != 2:
        return False, "El método gráfico requiere exactamente 2 variables (x1 y x2)."
    return True, ""


def validar_para_simplex(problema):
    """
    Valida que el problema cumpla los requisitos del método simplex.
    Devuelve (True, "") si es válido, o (False, mensaje_error) si no.
    """
    if problema.tipo_optimizacion != "max":
        return False, "El método simplex en esta aplicación solo admite maximización."
    if problema.num_restricciones < 2:
        return False, "El método simplex requiere al menos 2 restricciones."
    return True, ""


# =====================================================================
# 3. LÓGICA MÉTODO GRÁFICO
# =====================================================================
# Pasos: (1) calcular cruces entre rectas, (2) filtrar los que cumplen
# todas las restricciones (vértices factibles), (3) evaluar Z en cada
# vértice, (4) elegir el mejor.

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


# =====================================================================
# 4. LÓGICA MÉTODO SIMPLEX
# =====================================================================
# Pasos: (1) armar tabla inicial con variables de holgura, (2) iterar
# mientras la fila Z tenga negativos (entra/sale de la base, pivoteo),
# (3) leer la solución final de la tabla.

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


# =====================================================================
# 5. INTERFAZ GRÁFICA
# =====================================================================

class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Resolvedor de Programación Lineal")
        self.geometry("420x480")

        self.tipo_optimizacion = tk.StringVar(value="max")
        self.num_variables = tk.IntVar(value=1)
        self.num_restricciones = tk.IntVar(value=1)

        self._construir_widgets()

    def _construir_widgets(self):
        tk.Label(
            self, text="Resolvedor de Programación Lineal",
            font=("Arial", 14, "bold")
        ).pack(pady=(15, 0))
        tk.Label(self, text="Método Gráfico y Simplex").pack(pady=(0, 15))

        tk.Label(self, text="Seleccione maximizar o minimizar").pack(pady=(5, 5))
        frame_tipo = tk.Frame(self)
        frame_tipo.pack(pady=5)
        tk.Radiobutton(
            frame_tipo, text="Maximizar", variable=self.tipo_optimizacion, value="max"
        ).pack(side="left", padx=10)
        tk.Radiobutton(
            frame_tipo, text="Minimizar", variable=self.tipo_optimizacion, value="min"
        ).pack(side="left", padx=10)

        self._crear_contador("Número de Variables de Decisión", self.num_variables)
        self._crear_contador("Número de restricciones", self.num_restricciones)

        tk.Button(
            self, text="Continuar", command=self._continuar, width=20
        ).pack(pady=25)

    def _crear_contador(self, etiqueta, variable):
        tk.Label(self, text=etiqueta, font=("Arial", 11)).pack(pady=(15, 5))
        frame = tk.Frame(self)
        frame.pack()

        tk.Button(
            frame, text="-", width=3,
            command=lambda: self._ajustar_contador(variable, -1)
        ).pack(side="left", padx=5)

        tk.Label(frame, textvariable=variable, width=4, relief="solid").pack(side="left")

        tk.Button(
            frame, text="+", width=3,
            command=lambda: self._ajustar_contador(variable, 1)
        ).pack(side="left", padx=5)

    def _ajustar_contador(self, variable, delta):
        nuevo_valor = variable.get() + delta
        if nuevo_valor >= 1:
            variable.set(nuevo_valor)

    def _continuar(self):
        if self.num_variables.get() < 1 or self.num_restricciones.get() < 1:
            messagebox.showerror(
                "Datos incompletos",
                "Debe ingresar al menos 1 variable y 1 restricción."
            )
            return

        self.withdraw()  # oculta esta ventana en vez de cerrarla
        ventana_datos = VentanaDatos(
            ventana_anterior=self,
            tipo_optimizacion=self.tipo_optimizacion.get(),
            num_variables=self.num_variables.get(),
            num_restricciones=self.num_restricciones.get(),
        )
        ventana_datos.grab_set()


def _crear_entry_numerico(parent, width=5, valor_por_defecto="0"):
    """
    Crea un Entry con comportamiento tipo campo numérico:
    - Al ganar foco (clic o Tab), si el contenido es "0", se borra para
      que el usuario escriba directamente sin tener que borrarlo a mano.
    - Al perder foco, si quedó vacío, se vuelve a poner "0" para que
      el campo nunca quede sin valor al leerlo.
    """
    entry = tk.Entry(parent, width=width)
    entry.insert(0, valor_por_defecto)

    def al_ganar_foco(evento):
        if entry.get() == valor_por_defecto:
            entry.delete(0, tk.END)

    def al_perder_foco(evento):
        if entry.get().strip() == "":
            entry.insert(0, valor_por_defecto)

    entry.bind("<FocusIn>", al_ganar_foco)
    entry.bind("<FocusOut>", al_perder_foco)

    return entry


class VentanaDatos(tk.Toplevel):
    def __init__(self, ventana_anterior, tipo_optimizacion, num_variables, num_restricciones):
        super().__init__(ventana_anterior)
        self.ventana_anterior = ventana_anterior
        self.tipo_optimizacion = tipo_optimizacion
        self.num_variables = num_variables
        self.num_restricciones = num_restricciones

        self.title("Entrada de Datos")
        self.geometry("500x600")
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

        # Aquí se guardan las referencias a los Entry para leerlos después
        self.entries_funcion_objetivo = []
        self.entries_restricciones = []  # lista de (lista_entries_coef, entry_ld, combo_operador)

        self._construir_widgets()

    def _construir_widgets(self):
        tk.Label(
            self, text="Resolvedor de Programación Lineal",
            font=("Arial", 13, "bold")
        ).pack(pady=(10, 0))
        tk.Label(self, text="Método Gráfico y Simplex").pack(pady=(0, 10))

        # --- Función objetivo ---
        tk.Label(self, text="Función objetivo", font=("Arial", 11, "bold")).pack(pady=(10, 5))
        frame_fo = tk.Frame(self)
        frame_fo.pack()
        for i in range(self.num_variables):
            entry = _crear_entry_numerico(frame_fo)
            entry.pack(side="left", padx=2)
            self.entries_funcion_objetivo.append(entry)
            texto = f"x{i+1}" + (" +" if i < self.num_variables - 1 else "")
            tk.Label(frame_fo, text=texto).pack(side="left", padx=2)

        # --- Restricciones (en un canvas con scroll, por si son muchas) ---
        tk.Label(self, text="Restricciones", font=("Arial", 11, "bold")).pack(pady=(15, 5))
        contenedor = tk.Frame(self)
        contenedor.pack(fill="both", expand=True, padx=10)
        canvas = tk.Canvas(contenedor, height=250)
        scrollbar = tk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        frame_scrolleable = tk.Frame(canvas)

        frame_scrolleable.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=frame_scrolleable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for r in range(self.num_restricciones):
            fila_frame = tk.Frame(frame_scrolleable)
            fila_frame.pack(pady=5, anchor="w")
            tk.Label(fila_frame, text=f"Restricción {r+1}:").pack(side="left", padx=(0, 5))

            entries_coef = []
            for i in range(self.num_variables):
                entry = _crear_entry_numerico(fila_frame)
                entry.pack(side="left", padx=2)
                entries_coef.append(entry)
                texto = f"x{i+1}" + (" +" if i < self.num_variables - 1 else "")
                tk.Label(fila_frame, text=texto).pack(side="left", padx=2)

            combo_operador = tk.StringVar(value="<=")
            tk.OptionMenu(fila_frame, combo_operador, "<=", ">=", "=").pack(side="left", padx=5)

            entry_ld = _crear_entry_numerico(fila_frame)
            entry_ld.pack(side="left", padx=2)

            self.entries_restricciones.append((entries_coef, entry_ld, combo_operador))

        # --- Botones de método ---
        tk.Label(
            self, text="Método/s disponible/s", font=("Arial", 11, "bold")
        ).pack(pady=(15, 5))
        frame_metodos = tk.Frame(self)
        frame_metodos.pack()

        self.boton_grafico = tk.Button(
            frame_metodos, text="Gráfico", width=15,
            command=lambda: self._resolver("grafico")
        )
        self.boton_grafico.pack(side="left", padx=10)

        self.boton_simplex = tk.Button(
            frame_metodos, text="Simplex", width=15,
            command=lambda: self._resolver("simplex")
        )
        self.boton_simplex.pack(side="left", padx=10)

        self._actualizar_disponibilidad_metodos()

    def _leer_problema(self):
        """Lee los Entry actuales y construye un ProblemaPL. Puede lanzar ValueError."""
        try:
            funcion_objetivo = [
                float(entry.get()) for entry in self.entries_funcion_objetivo
            ]
        except ValueError:
            raise ValueError("La función objetivo tiene valores no numéricos.")

        restricciones = []
        for entries_coef, entry_ld, combo_operador in self.entries_restricciones:
            try:
                coeficientes = [float(entry.get()) for entry in entries_coef]
                termino_independiente = float(entry_ld.get())
            except ValueError:
                raise ValueError("Una restricción tiene valores no numéricos.")
            restricciones.append(
                Restriccion(coeficientes, combo_operador.get(), termino_independiente)
            )

        return ProblemaPL(self.tipo_optimizacion, funcion_objetivo, restricciones)

    def _actualizar_disponibilidad_metodos(self):
        """
        Habilita o deshabilita los botones de método según si el problema
        actualmente ingresado cumple los requisitos de cada uno.
        Nota: esto solo depende de num_variables/num_restricciones/tipo,
        que ya se conocen sin necesidad de leer los coeficientes.
        """
        # Validación de dimensiones (no requiere los valores de los campos)
        grafico_valido = self.num_variables == 2
        simplex_valido = self.tipo_optimizacion == "max" and self.num_restricciones >= 2

        self.boton_grafico.config(state="normal" if grafico_valido else "disabled")
        self.boton_simplex.config(state="normal" if simplex_valido else "disabled")

    def _resolver(self, metodo):
        try:
            problema = self._leer_problema()
        except ValueError as error:
            messagebox.showerror("Error en los datos", str(error))
            return

        if metodo == "grafico":
            es_valido, mensaje = validar_para_grafico(problema)
        else:
            es_valido, mensaje = validar_para_simplex(problema)

        if not es_valido:
            messagebox.showerror("Método no aplicable", mensaje)
            return
        if metodo == "grafico":
            ventana_resultado = VentanaGrafico(self, problema)
        else:
            ventana_resultado = VentanaSimplex(self, problema)

        ventana_resultado.grab_set()

    def _cerrar(self):
        self.ventana_anterior.deiconify()
        self.destroy()


class VentanaGrafico(tk.Toplevel):
    def __init__(self, ventana_anterior, problema):
        super().__init__(ventana_anterior)
        self.title("Resultado - Método Gráfico")
        self.geometry("600x600")

        try:
            self.resultado = resolver_metodo_grafico(problema)
        except ValueError as error:
            tk.Label(self, text=f"Error: {error}", fg="red", wraplength=500).pack(pady=20)
            return

        self.problema = problema
        self._mostrar_resultado()

    def _mostrar_resultado(self):
        punto_optimo = self.resultado["punto_optimo"]
        valor_optimo = self.resultado["valor_optimo"]

        tk.Label(
            self, text=f"Punto óptimo: x1={punto_optimo[0]:.2f}, x2={punto_optimo[1]:.2f}",
            font=("Arial", 12, "bold")
        ).pack(pady=(10, 0))
        tk.Label(
            self, text=f"Valor óptimo Z = {valor_optimo:.2f}",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))

        figura = self._crear_figura()
        canvas = FigureCanvasTkAgg(figura, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _crear_figura(self):
        vertices = self.resultado["region_factible"]
        punto_optimo = self.resultado["punto_optimo"]

        figura, ejes = plt.subplots(figsize=(5, 5))

        limite = max(max(v) for v in vertices) * 1.3 if vertices else 10
        x_vals = np.linspace(0, limite, 200)

        # Dibujar cada restricción como una recta
        for restriccion in self.problema.restricciones:
            a, b = restriccion.coeficientes
            c = restriccion.termino_independiente
            if b != 0:
                y_vals = (c - a * x_vals) / b
                ejes.plot(x_vals, y_vals, label=f"{a}x1 + {b}x2 {restriccion.operador} {c}")
            else:
                ejes.axvline(x=c / a, label=f"{a}x1 {restriccion.operador} {c}")

        # Sombrear la región factible (ordenando los vértices angularmente)
        if len(vertices) >= 3:
            centro_x = sum(v[0] for v in vertices) / len(vertices)
            centro_y = sum(v[1] for v in vertices) / len(vertices)
            vertices_ordenados = sorted(
                vertices,
                key=lambda v: np.arctan2(v[1] - centro_y, v[0] - centro_x)
            )
            poligono_x = [v[0] for v in vertices_ordenados] + [vertices_ordenados[0][0]]
            poligono_y = [v[1] for v in vertices_ordenados] + [vertices_ordenados[0][1]]
            ejes.fill(poligono_x, poligono_y, alpha=0.3, color="green")

        # Marcar el punto óptimo
        ejes.plot(punto_optimo[0], punto_optimo[1], "ro", markersize=8, label="Óptimo")

        ejes.set_xlim(0, limite)
        ejes.set_ylim(0, limite)
        ejes.set_xlabel("x1")
        ejes.set_ylabel("x2")
        ejes.legend(fontsize=8, loc="upper right")
        ejes.grid(True, linestyle="--", alpha=0.5)

        return figura


class VentanaSimplex(tk.Toplevel):
    def __init__(self, ventana_anterior, problema):
        super().__init__(ventana_anterior)
        self.title("Resultado - Método Simplex")
        self.geometry("750x650")
        self.minsize(650, 500)

        try:
            self.resultado = resolver_metodo_simplex(problema)
        except ValueError as error:
            tk.Label(self, text=f"Error: {error}", fg="red", wraplength=600).pack(pady=20)
            return

        self._mostrar_resultado()

    def _mostrar_resultado(self):
        solucion = self.resultado["solucion"]
        valor_optimo = self.resultado["valor_optimo"]

        texto_solucion = ", ".join(f"{var}={valor:.2f}" for var, valor in solucion.items())
        tk.Label(
            self, text=f"Solución óptima: {texto_solucion}",
            font=("Arial", 12, "bold")
        ).pack(pady=(10, 0))
        tk.Label(
            self, text=f"Valor óptimo Z = {valor_optimo:.2f}",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))

        # Panel dividido: tabla arriba, descripción del paso abajo.
        # Así se aprovecha el espacio que antes quedaba en blanco.
        panel = tk.PanedWindow(self, orient="vertical", sashrelief="raised")
        panel.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        notebook = ttk.Notebook(panel)
        panel.add(notebook, stretch="always", height=280)

        frame_descripcion = tk.LabelFrame(panel, text="Explicación del paso", padx=10, pady=10)
        panel.add(frame_descripcion, stretch="always", height=200)

        self.texto_descripcion = tk.Text(
            frame_descripcion, wrap="word", font=("Arial", 10),
            state="disabled", relief="flat", bg=self.cget("bg")
        )
        self.texto_descripcion.pack(fill="both", expand=True)

        nombres_columnas = self.resultado["nombres_columnas"]
        descripciones = self.resultado["descripciones"]

        for indice, tabla in enumerate(self.resultado["iteraciones"]):
            etiqueta = "Tabla inicial" if indice == 0 else f"Iteración {indice}"
            frame_tab = tk.Frame(notebook)
            notebook.add(frame_tab, text=etiqueta)
            self._dibujar_tabla(frame_tab, tabla, nombres_columnas)

        # Al cambiar de pestaña, actualizar el texto de explicación correspondiente
        notebook.bind(
            "<<NotebookTabChanged>>",
            lambda evento: self._mostrar_descripcion(
                descripciones, notebook.index(notebook.select())
            )
        )

        # Mostrar la descripción de la tabla inicial de una vez,
        # y agregar la explicación final de la solución al terminar.
        self._descripciones_completas = descripciones
        self._mostrar_descripcion(descripciones, 0)

    def _mostrar_descripcion(self, descripciones, indice_tabla):
        """
        Muestra en el panel de texto la explicación correspondiente a la
        pestaña seleccionada. La última descripción (solución final) se
        añade siempre después de la explicación del último paso.
        """
        texto = descripciones[indice_tabla]
        es_ultima_tabla = indice_tabla == len(descripciones) - 2
        if es_ultima_tabla:
            texto += "\n\n" + descripciones[-1]

        self.texto_descripcion.config(state="normal")
        self.texto_descripcion.delete("1.0", tk.END)
        self.texto_descripcion.insert("1.0", texto)
        self.texto_descripcion.config(state="disabled")

    def _dibujar_tabla(self, frame, tabla, nombres_columnas):
        tree = ttk.Treeview(frame, columns=nombres_columnas, show="headings", height=8)
        for nombre in nombres_columnas:
            tree.heading(nombre, text=nombre)
            tree.column(nombre, width=60, anchor="center")

        for fila in tabla:
            valores_formateados = [f"{valor:.2f}" for valor in fila]
            tree.insert("", "end", values=valores_formateados)

        tree.pack(fill="both", expand=True, padx=5, pady=5)


# =====================================================================
# 6. PUNTO DE ENTRADA
# =====================================================================

if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()