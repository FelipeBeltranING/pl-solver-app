"""
Ventana principal (Pantalla 1): selección de maximizar/minimizar,
y número de variables de decisión y de restricciones.

Al presionar "Continuar", abre la ventana de entrada de datos
(Pantalla 2) con la cantidad de campos correspondiente.
"""

import tkinter as tk
from tkinter import messagebox


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

        # Import local para evitar import circular con ventana_datos
        from interfaz.ventana_datos import VentanaDatos

        self.withdraw()  # oculta esta ventana en vez de cerrarla
        ventana_datos = VentanaDatos(
            ventana_anterior=self,
            tipo_optimizacion=self.tipo_optimizacion.get(),
            num_variables=self.num_variables.get(),
            num_restricciones=self.num_restricciones.get(),
        )
        ventana_datos.grab_set()


if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()