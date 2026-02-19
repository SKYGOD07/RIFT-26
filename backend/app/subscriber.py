"""
Blockchain Sync Engine — watches the Algorand Testnet for EventTicketing contract events
and syncs them to the local database.

Uses polling against the Algorand Indexer since `algokit-subscriber` requires
an async runtime. This runs as a background task inside the FastAPI event loop.

Watches for:
  - mint_ticket ABI calls → INSERT into tickets table
  - transfer_ticket ABI calls → UPDATE current_owner_wallet
"""

import asyncio
import base64
import logging
from datetime import datetime, timezone

from algosdk.v2client import indexer
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models import Ticket, TicketStatus, Transfer, TransferType, TransferStatus

logger = logging.getLogger(__name__)

# ABI method selectors (first 4 bytes of SHA-512/256 of method signature)
# mint_ticket(uint64,string)uint64 → 0x3311de72
# transfer_ticket(pay,uint64)void  → 0xe5ff5d13
MINT_SELECTOR = "3311de72"
TRANSFER_SELECTOR = "e5ff5d13"


class ChainSubscriber:
    """
    Background service that polls the Algorand Indexer for transactions
    on the deployed EventTicketing app and syncs state to the database.
    """

    def __init__(self) -> None:
        self.indexer_client: indexer.IndexerClient | None = None
        self.app_id: int = 0
        self._last_round: int = 0
        self._running: bool = False
        self._poll_interval: int = 5  # seconds between polls

    def initialize(self) -> None:
        """Set up the indexer client."""
        self.app_id = settings.app_id
        if not self.app_id:
            logger.warning("Subscriber: No APP_ID configured — sync disabled.")
            return

        self.indexer_client = indexer.IndexerClient(
            settings.indexer_token,
            settings.indexer_server,
        )
        logger.info(f"Subscriber initialized for App ID {self.app_id}")

    async def start(self) -> None:
        """Start the polling loop (run as asyncio background task)."""
        if not self.indexer_client or not self.app_id:
            logger.warning("Subscriber not configured — skipping.")
            return

        self._running = True
        logger.info(f"Subscriber started — polling every {self._poll_interval}s")

        while self._running:
            try:
                await self._poll()
            except Exception as e:
                logger.error(f"Subscriber poll error: {e}", exc_info=True)

            await asyncio.sleep(self._poll_interval)

    def stop(self) -> None:
        """Stop the polling loop."""
        self._running = False
        logger.info("Subscriber stopped.")

    async def _poll(self) -> None:
        """Fetch new transactions for the app and process them."""
        try:
            # Query indexer for app transactions since last round
            search_params = {
                "application_id": self.app_id,
                "limit": 50,
            }
            if self._last_round > 0:
                search_params["min_round"] = self._last_round + 1

            response = self.indexer_client.search_transactions(**search_params)

            transactions = response.get("transactions", [])
            if not transactions:
                return

            logger.info(f"Subscriber: Processing {len(transactions)} transaction(s)")

            for txn in transactions:
                await self._process_transaction(txn)

                # Track the latest round
                confirmed_round = txn.get("confirmed-round", 0)
                if confirmed_round > self._last_round:
                    self._last_round = confirmed_round

        except Exception as e:
            logger.error(f"Indexer query failed: {e}")

    async def _process_transaction(self, txn: dict) -> None:
        """Process a single transaction — detect mints and transfers."""
        txn_type = txn.get("tx-type")
        txn_id = txn.get("id", "")

        # We need application call transactions
        if txn_type != "appl":
            return

        app_call = txn.get("application-transaction", {})
        app_args = app_call.get("application-args", [])

        if not app_args:
            return

        # Decode first arg (method selector)
        try:
            selector_bytes = base64.b64decode(app_args[0])
            selector_hex = selector_bytes.hex()
        except Exception:
            return

        if selector_hex == MINT_SELECTOR:
            await self._handle_mint(txn, txn_id)
        elif selector_hex == TRANSFER_SELECTOR:
            await self._handle_transfer(txn, txn_id)

    async def _handle_mint(self, txn: dict, txn_id: str) -> None:
        """Handle a mint_ticket transaction — insert into tickets table."""
        # Extract the created ASA ID from inner transactions
        inner_txns = txn.get("inner-txns", [])
        asa_id = None
        for inner in inner_txns:
            if inner.get("tx-type") == "acfg":
                asa_id = inner.get("created-asset-index") or inner.get("asset-config-transaction", {}).get("asset-id")
                break

        if asa_id is None:
            # Also check the ABI return value in logs
            logs = txn.get("logs", [])
            if logs:
                try:
                    # ARC-4 return: first log entry, first 4 bytes = 0x151f7c75, rest = uint64
                    last_log = base64.b64decode(logs[-1])
                    if last_log[:4] == b"\x15\x1f\x7c\x75":
                        asa_id = int.from_bytes(last_log[4:12], "big")
                except Exception:
                    pass

        if asa_id is None:
            logger.warning(f"Mint txn {txn_id}: could not extract ASA ID")
            return

        # Extract ticket_price and seat_number from app args
        app_call = txn.get("application-transaction", {})
        app_args = app_call.get("application-args", [])

        ticket_price = 0
        seat_number = "UNKNOWN"
        try:
            if len(app_args) > 1:
                price_bytes = base64.b64decode(app_args[1])
                ticket_price = int.from_bytes(price_bytes, "big")
            if len(app_args) > 2:
                seat_bytes = base64.b64decode(app_args[2])
                # ARC-4 string: first 2 bytes = length prefix, rest = utf-8
                seat_number = seat_bytes[2:].decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to decode mint args: {e}")

        sender = txn.get("sender", "")
        confirmed_round = txn.get("confirmed-round", 0)

        async with async_session() as session:
            # Check if already synced
            existing = await session.execute(
                select(Ticket).where(Ticket.asa_id == asa_id)
            )
            if existing.scalar_one_or_none():
                logger.debug(f"ASA {asa_id} already in DB — skipping")
                return

            ticket = Ticket(
                event_id=1,  # Default event — adjust as needed
                seat_number=seat_number,
                asa_id=asa_id,
                ticket_price=ticket_price,
                status=TicketStatus.MINTED,
                current_owner_wallet=sender,
                txn_id=txn_id,
            )
            session.add(ticket)
            await session.commit()
            logger.info(f"SYNCED MINT: ASA {asa_id} ({seat_number}) → DB ticket id={ticket.id}")

    async def _handle_transfer(self, txn: dict, txn_id: str) -> None:
        """Handle a transfer_ticket transaction — update ownership in DB."""
        # Extract asset ID from app args
        app_call = txn.get("application-transaction", {})
        app_args = app_call.get("application-args", [])

        asa_id = None
        try:
            if len(app_args) > 1:
                asset_bytes = base64.b64decode(app_args[1])
                asa_id = int.from_bytes(asset_bytes, "big")
        except Exception:
            pass

        if asa_id is None:
            logger.warning(f"Transfer txn {txn_id}: could not extract ASA ID")
            return

        # The buyer is the Txn.sender (caller of transfer_ticket)
        buyer = txn.get("sender", "")

        # Extract payment amount from the grouped payment transaction
        price = 0
        group_id = txn.get("group")
        # For grouped transactions, the payment is the previous txn in the group
        # We can get the amount from inner-txns or the group

        async with async_session() as session:
            result = await session.execute(
                select(Ticket).where(Ticket.asa_id == asa_id)
            )
            ticket = result.scalar_one_or_none()
            if not ticket:
                logger.warning(f"Transfer ASA {asa_id}: ticket not found in DB")
                return

            # Record transfer
            transfer = Transfer(
                ticket_id=ticket.id,
                from_wallet=ticket.current_owner_wallet,
                to_wallet=buyer,
                price=price,
                txn_id=txn_id,
                transfer_type=TransferType.RESALE,
                status=TransferStatus.CONFIRMED,
            )
            session.add(transfer)

            # Update ownership
            ticket.current_owner_wallet = buyer
            ticket.status = TicketStatus.TRANSFERRED

            await session.commit()
            logger.info(f"SYNCED TRANSFER: ASA {asa_id} → {buyer}")


# Singleton
chain_subscriber = ChainSubscriber()
