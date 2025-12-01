from pydantic import BaseModel, UUID4, Field
from enum import Enum

class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"

class WalletOperation(BaseModel):
    operation_type: OperationType
    amount: float = Field(gt=0)

class WalletResponse(BaseModel):
    id: UUID4
    balance: float