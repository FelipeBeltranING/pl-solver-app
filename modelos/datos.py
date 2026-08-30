"""
Modelos de datos para el resolvedor de programación lineal.

Estas clases representan la estructura definida en el diccionario de datos:
- Restriccion: una restricción individual del problema.
- ProblemaPL: el problema completo de programación lineal.
"""

from dataclasses import dataclass, field


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