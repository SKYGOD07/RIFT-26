"""
SQLAlchemy ORM models for the ticketing database.
Maps to the schema defined in implementation_plan.md.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ─────────────────────── Enums ─────────────────────── #

class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SOLD_OUT = "sold_out"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TicketStatus(str, enum.Enum):
    MINTED = "minted"
    SOLD = "sold"
    TRANSFERRED = "transferred"
    USED = "used"
    CANCELLED = "cancelled"


class UserRole(str, enum.Enum):
    BUYER = "buyer"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class TransferType(str, enum.Enum):
    PRIMARY_SALE = "primary_sale"
    RESALE = "resale"
    GIFT = "gift"


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class CheckinMethod(str, enum.Enum):
    QR_SCAN = "qr_scan"
    MANUAL = "manual"
    NFC = "nfc"


# ─────────────────────── Models ─────────────────────── #

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_seats: Mapped[int] = mapped_column(Integer, default=0)
    max_resale_price: Mapped[int] = mapped_column(BigInteger, default=0)
    organizer_wallet: Mapped[str] = mapped_column(String(58), nullable=False)
    app_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus), default=EventStatus.DRAFT
    )

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    seat_number: Mapped[str] = mapped_column(String(50), nullable=False)
    asa_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    ticket_price: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus), default=TicketStatus.MINTED
    )
    current_owner_wallet: Mapped[str] = mapped_column(String(58), nullable=False)
    minted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    txn_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="tickets")
    transfers: Mapped[list["Transfer"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    checkin: Mapped["Checkin | None"] = relationship(back_populates="ticket", uselist=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_address: Mapped[str] = mapped_column(String(58), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.BUYER)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    checkins: Mapped[list["Checkin"]] = relationship(back_populates="user")


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=False)
    from_wallet: Mapped[str] = mapped_column(String(58), nullable=False)
    to_wallet: Mapped[str] = mapped_column(String(58), nullable=False)
    price: Mapped[int] = mapped_column(BigInteger, default=0)
    txn_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transfer_type: Mapped[TransferType] = mapped_column(
        Enum(TransferType), default=TransferType.PRIMARY_SALE
    )
    status: Mapped[TransferStatus] = mapped_column(
        Enum(TransferStatus), default=TransferStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="transfers")


class Checkin(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    method: Mapped[CheckinMethod] = mapped_column(
        Enum(CheckinMethod), default=CheckinMethod.QR_SCAN
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="checkin")
    user: Mapped["User"] = relationship(back_populates="checkins")
