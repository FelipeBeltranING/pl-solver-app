"""
Ventana de resultados del método simplex (Pantalla de resultado).

Muestra la tabla de cada iteración del método simplex y la solución final
(valores de las variables de decisión y valor óptimo de Z).
"""

import tkinter as tk
from tkinter import ttk

from logica.metodo_simplex import resolver_metodo_simplex


class VentanaSimplex(tk.Toplevel):
    def __init__(self, ventana_anterior, problema):
        super().__init__(ventana_anterior)
        self.title("Resultado - Método Simplex")
        self.geometry("700x600")

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

        # Pestañas: una por cada iteración
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        nombres_columnas = self.resultado["nombres_columnas"]

        for indice, tabla in enumerate(self.resultado["iteraciones"]):
            etiqueta = "Tabla inicial" if indice == 0 else f"Iteración {indice}"
            frame_tab = tk.Frame(notebook)
            notebook.add(frame_tab, text=etiqueta)
            self._dibujar_tabla(frame_tab, tabla, nombres_columnas)

    def _dibujar_tabla(self, frame, tabla, nombres_columnas):
        tree = ttk.Treeview(frame, columns=nombres_columnas, show="headings", height=8)
        for nombre in nombres_columnas:
            tree.heading(nombre, text=nombre)
            tree.column(nombre, width=60, anchor="center")

        for fila in tabla:
            valores_formateados = [f"{valor:.2f}" for valor in fila]
            tree.insert("", "end", values=valores_formateados)

        tree.pack(fill="both", expand=True, padx=5, pady=5)