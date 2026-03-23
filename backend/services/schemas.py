from typing import Optional, Literal
from pydantic import BaseModel


class ParsedEmail(BaseModel):
    tipo_transaccion: Literal['debito', 'credito', 'transferencia', 'desconocido']
    monto: float
    comercio: Optional[str] = None
    fecha_iso: Optional[str] = None


class CategorizeOutput(BaseModel):
    categoria: str
