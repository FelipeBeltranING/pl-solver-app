"""
Ventana de resultados del método simplex (Pantalla de resultado).

Muestra la tabla de cada iteración del método simplex, una descripción en
texto de lo que ocurrió en ese paso, y la solución final (valores de las
variables de decisión y valor óptimo de Z).
"""

import tkinter as tk
from tkinter import ttk

from logica.metodo_simplex import resolver_metodo_simplex


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