"""
Punto de entrada de la aplicación.
Ejecutar con: python main.py
"""
from interfaz.ventana_principal import VentanaPrincipal

if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()