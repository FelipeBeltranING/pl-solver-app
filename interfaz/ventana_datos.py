"""
Ventana de entrada de datos (Pantalla 2): genera dinámicamente los campos
de la función objetivo y de cada restricción según el número de variables
y restricciones definido en la Pantalla 1.

Los botones "Gráfico" y "Simplex" se habilitan o deshabilitan según si el
problema ingresado cumple los requisitos de cada método (ver utils/validaciones.py).
"""

import tkinter as tk
from tkinter import messagebox

from modelos.datos import Restriccion, ProblemaPL
from utils.validaciones import validar_para_grafico, validar_para_simplex


def _crear_entry_numerico(parent, width=5, valor_por_defecto="0"):
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

        # Import local para evitar import circular
        if metodo == "grafico":
            from interfaz.ventana_grafico import VentanaGrafico
            ventana_resultado = VentanaGrafico(self, problema)
        else:
            from interfaz.ventana_simplex import VentanaSimplex
            ventana_resultado = VentanaSimplex(self, problema)

        ventana_resultado.grab_set()

    def _cerrar(self):
        self.ventana_anterior.deiconify()
        self.destroy()


if __name__ == "__main__":
    # Prueba rápida de esta pantalla sola, sin pasar por la Pantalla 1
    raiz = tk.Tk()
    raiz.withdraw()
    ventana = VentanaDatos(raiz, tipo_optimizacion="max", num_variables=2, num_restricciones=2)
    ventana.mainloop()