"""
Ventana de resultados del método gráfico (Pantalla de resultado).

Muestra la gráfica de la región factible (usando matplotlib embebido en
Tkinter) y el punto óptimo con su valor de Z.
"""

import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from logica.metodo_grafico import resolver_metodo_grafico


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