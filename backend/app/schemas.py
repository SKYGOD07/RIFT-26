"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ─────────────────── Events ─────────────────── #

class EventCreate(BaseModel):
    name: str = Field(..., max_length=255, examples=["RIFT 2026 Conference"])
    description: str | None = None
    venue: str | None = None
    event_date: datetime | None = None
    total_seats: int = Field(default=100, ge=1)
    max_resale_price: int = Field(..., description="Max resale price in microAlgos", examples=[1_000_000])
    organizer_wallet: str = Field(..., max_length=58)


class EventResponse(BaseModel):
    id: int
    name: str
    description: str | None
    venue: str | None
    event_date: datetime | None
    total_seats: int
    max_resale_price: int
    organizer_wallet: str
    app_id: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────── Tickets ─────────────────── #

class MintTicketRequest(BaseModel):
    event_id: int
    seat_number: str = Field(..., max_length=50, examples=["VIP-1"])
    ticket_price: int = Field(..., description="Price in microAlgos", examples=[1_000_000])


class TicketResponse(BaseModel):
    id: int
    event_id: int
    seat_number: str
    asa_id: int
    ticket_price: int
    status: str
    current_owner_wallet: str
    minted_at: datetime
    txn_id: str | None

    model_config = {"from_attributes": True}


class TransferTicketRequest(BaseModel):
    ticket_id: int
    buyer_wallet: str = Field(..., max_length=58)
    price: int = Field(..., description="Sale price in microAlgos")


# ─────────────────── Users ─────────────────── #

class UserCreate(BaseModel):
    wallet_address: str = Field(..., max_length=58)
    display_name: str | None = None
    email: str | None = None
    role: str = "buyer"


class UserResponse(BaseModel):
    id: int
    wallet_address: str
    display_name: str | None
    email: str | None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────── Transfers ─────────────────── #

class TransferResponse(BaseModel):
    id: int
    ticket_id: int
    from_wallet: str
    to_wallet: str
    price: int
    txn_id: str | None
    transfer_type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────── Health ─────────────────── #

class HealthResponse(BaseModel):
    status: str = "ok"
    app_id: int
    network: str = "testnet"
