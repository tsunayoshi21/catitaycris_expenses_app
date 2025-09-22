from pydantic import BaseModel, Field
from typing import Optional, Literal

class ParsedEmail(BaseModel):
    """
    Esquema para representar la información extraída de un correo electrónico bancario.
    """
    tipo_transaccion: Literal["debito", "credito", "transferencia", "desconocido"] = Field(default="", description="Tipo de transacción detectada en el correo bancario: débito, crédito, transferencia o desconocido.")
    monto: float = Field(description="Monto de la transacción expresado en pesos chilenos, extraído del correo. Usa punto como separador decimal.")
    comercio: Optional[str] = Field(default=None, description="Nombre del comercio o persona involucrada en la transacción. En transferencias, corresponde al destinatario.")
    fecha_iso: Optional[str] = Field(default=None, description="Fecha de la transacción en formato ISO 8601 (ejemplo: '2025-09-22T14:30:00Z'). Puede ser nulo si no se encuentra.")

class CategorizeOutput(BaseModel):
    """
    Esquema para representar la categoría asignada a un gasto.
    Considerar definir categorías estándar para más consistencia.
    """
    categoria: str = Field(
        description="Categoría corta y descriptiva en minúsculas asignada al gasto, como 'comida', 'transporte', 'entretenimiento', etc."
    )