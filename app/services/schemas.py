from pydantic import BaseModel, Field
from typing import Literal

class TransactionCategory(BaseModel):
    category: Literal['income', 'expense'] = Field(description="The category of the transaction")