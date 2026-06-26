from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.enums import (
    Channel,
    Language,
    TransactionStatus,
    TransactionType,
    UserType,
)


class Transaction(BaseModel):
    transaction_id: str
    timestamp: str = ""
    type: TransactionType | None = None
    amount: float = 0
    counterparty: str = ""
    status: TransactionStatus | None = None

    @field_validator("type", mode="before")
    @classmethod
    def coerce_type(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        try:
            return TransactionType(str(v))
        except ValueError:
            return None

    @field_validator("status", mode="before")
    @classmethod
    def coerce_status(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        try:
            return TransactionStatus(str(v))
        except ValueError:
            return None


class TicketRequest(BaseModel):
    ticket_id: str
    complaint: str
    language: Language | None = None
    channel: Channel | None = None
    user_type: UserType | None = None
    campaign_context: str | None = None
    transaction_history: list[Transaction] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("language", mode="before")
    @classmethod
    def coerce_language(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        try:
            return Language(str(v))
        except ValueError:
            return None

    @field_validator("channel", mode="before")
    @classmethod
    def coerce_channel(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        try:
            return Channel(str(v))
        except ValueError:
            return None

    @field_validator("user_type", mode="before")
    @classmethod
    def coerce_user_type(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        try:
            return UserType(str(v))
        except ValueError:
            return None

    @field_validator("transaction_history", mode="before")
    @classmethod
    def coerce_history(cls, v: Any) -> list:
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        result = []
        for item in v:
            try:
                result.append(Transaction.model_validate(item))
            except Exception:
                continue
        return result
