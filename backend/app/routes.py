"""
FastAPI route handlers for the ticketing API.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Event, EventStatus, Ticket, TicketStatus, Transfer, TransferType, TransferStatus, User, UserRole
from app.schemas import (
    EventCreate,
    EventResponse,
    HealthResponse,
    MintTicketRequest,
    TicketResponse,
    TransferResponse,
    TransferTicketRequest,
    UserCreate,
    UserResponse,
)
from app.algorand_service import algorand_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────── Health ─────────────────── #

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        app_id=settings.app_id,
        network="testnet",
    )


# ─────────────────── Events ─────────────────── #

@router.post("/events", response_model=EventResponse, status_code=201, tags=["Events"])
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    """Create a new event."""
    db_event = Event(
        name=event.name,
        description=event.description,
        venue=event.venue,
        event_date=event.event_date,
        total_seats=event.total_seats,
        max_resale_price=event.max_resale_price,
        organizer_wallet=event.organizer_wallet,
        app_id=settings.app_id,
        status=EventStatus.ACTIVE,
    )
    db.add(db_event)
    await db.flush()
    await db.refresh(db_event)
    return db_event


@router.get("/events", response_model=list[EventResponse], tags=["Events"])
async def list_events(db: AsyncSession = Depends(get_db)):
    """List all events."""
    result = await db.execute(select(Event).order_by(Event.created_at.desc()))
    return result.scalars().all()


@router.get("/events/{event_id}", response_model=EventResponse, tags=["Events"])
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single event by ID."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# ─────────────────── Tickets ─────────────────── #

@router.post("/tickets/mint", response_model=TicketResponse, status_code=201, tags=["Tickets"])
async def mint_ticket(req: MintTicketRequest, db: AsyncSession = Depends(get_db)):
    """
    Mint a ticket NFT on-chain and store it in the database.
    This is the core endpoint: POST /tickets/mint -> on-chain ASA + DB row.
    """
    # 1. Verify event exists
    result = await db.execute(select(Event).where(Event.id == req.event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # 2. Mint on-chain
    try:
        chain_result = await algorand_service.mint_ticket_on_chain(
            ticket_price=req.ticket_price,
            seat_number=req.seat_number,
        )
    except Exception as e:
        logger.error(f"On-chain mint failed: {e}")
        raise HTTPException(status_code=502, detail=f"Blockchain error: {str(e)}")

    # 3. Save to database
    ticket = Ticket(
        event_id=req.event_id,
        seat_number=req.seat_number,
        asa_id=chain_result["asa_id"],
        ticket_price=req.ticket_price,
        status=TicketStatus.MINTED,
        current_owner_wallet=chain_result["app_address"],
        txn_id=chain_result.get("txn_id"),
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)

    logger.info(f"Ticket minted: id={ticket.id}, asa_id={ticket.asa_id}, seat={ticket.seat_number}")
    return ticket


@router.get("/tickets", response_model=list[TicketResponse], tags=["Tickets"])
async def list_tickets(
    event_id: int | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List tickets, optionally filtered by event_id or status."""
    query = select(Ticket).order_by(Ticket.minted_at.desc())
    if event_id:
        query = query.where(Ticket.event_id == event_id)
    if status:
        query = query.where(Ticket.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Tickets"])
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single ticket by ID."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/tickets/asa/{asa_id}", response_model=TicketResponse, tags=["Tickets"])
async def get_ticket_by_asa(asa_id: int, db: AsyncSession = Depends(get_db)):
    """Get a ticket by its on-chain ASA ID."""
    result = await db.execute(select(Ticket).where(Ticket.asa_id == asa_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found for ASA ID")
    return ticket


# ─────────────────── Transfers ─────────────────── #

@router.get("/transfers", response_model=list[TransferResponse], tags=["Transfers"])
async def list_transfers(
    ticket_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List transfer history, optionally filtered by ticket_id."""
    query = select(Transfer).order_by(Transfer.created_at.desc())
    if ticket_id:
        query = query.where(Transfer.ticket_id == ticket_id)
    result = await db.execute(query)
    return result.scalars().all()


# ─────────────────── Users ─────────────────── #

@router.post("/users", response_model=UserResponse, status_code=201, tags=["Users"])
async def create_or_get_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a user by wallet address (idempotent)."""
    result = await db.execute(
        select(User).where(User.wallet_address == user.wallet_address)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    db_user = User(
        wallet_address=user.wallet_address,
        display_name=user.display_name,
        email=user.email,
        role=UserRole(user.role) if user.role else UserRole.BUYER,
    )
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user


@router.get("/users/{wallet_address}", response_model=UserResponse, tags=["Users"])
async def get_user(wallet_address: str, db: AsyncSession = Depends(get_db)):
    """Get user by wallet address."""
    result = await db.execute(
        select(User).where(User.wallet_address == wallet_address)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ─────────────────── Chain State ─────────────────── #

@router.get("/chain/app-info", tags=["Chain"])
async def get_chain_app_info():
    """Query the smart contract state directly from the blockchain."""
    info = algorand_service.get_app_info()
    return info
