"""
Algorand blockchain integration service.
Uses algokit-utils v4 and the generated typed client to interact with the EventTicketing contract.
"""

import logging
import sys
from pathlib import Path

from algosdk import mnemonic
from algosdk.v2client import algod, indexer

import algokit_utils

from app.config import settings

logger = logging.getLogger(__name__)

# ─────────────────── Add contracts artifacts to path ─────────────────── #
# So we can import the generated typed client
_contracts_root = Path(__file__).parent.parent.parent / "projects" / "contracts"
if str(_contracts_root) not in sys.path:
    sys.path.insert(0, str(_contracts_root))

from smart_contracts.artifacts.ticketing.event_ticketing_client import (  # noqa: E402
    EventTicketingClient,
    MintTicketArgs,
    TransferTicketArgs,
)


class AlgorandService:
    """
    Service layer for all Algorand interactions.
    Initialized once at app startup.
    """

    def __init__(self) -> None:
        self.algod_client: algod.AlgodClient | None = None
        self.indexer_client: indexer.IndexerClient | None = None
        self.algorand: algokit_utils.AlgorandClient | None = None
        self.deployer_address: str | None = None
        self._deployer_private_key: str | None = None
        self.app_id: int = 0
        self.app_client: EventTicketingClient | None = None

    def initialize(self) -> None:
        """Initialize all Algorand clients. Call once at startup."""
        logger.info("Initializing Algorand service for Testnet...")

        # 1. Algod client
        self.algod_client = algod.AlgodClient(
            settings.algod_token,
            settings.algod_server,
        )

        # 2. Indexer client
        self.indexer_client = indexer.IndexerClient(
            settings.indexer_token,
            settings.indexer_server,
        )

        # 3. AlgorandClient (testnet)
        self.algorand = algokit_utils.AlgorandClient.testnet()

        # 4. Deployer account
        if settings.deployer_mnemonic:
            self._deployer_private_key = mnemonic.to_private_key(settings.deployer_mnemonic)
            self.deployer_address = mnemonic.to_public_key(settings.deployer_mnemonic)
            logger.info(f"Deployer: {self.deployer_address}")
        else:
            logger.warning("No DEPLOYER_MNEMONIC set — on-chain operations will fail.")

        # 5. App ID
        self.app_id = settings.app_id
        if self.app_id:
            logger.info(f"App ID: {self.app_id}")
            self._init_typed_client()
        else:
            logger.warning("No APP_ID set — deploy the contract first.")

    def _init_typed_client(self) -> None:
        """Initialize the typed EventTicketing client from the deployed App ID."""
        if not self.algorand or not self.app_id:
            return

        arc56_path = (
            _contracts_root / "smart_contracts" / "artifacts" / "ticketing" / "EventTicketing.arc56.json"
        )
        if not arc56_path.exists():
            logger.error(f"ARC-56 spec not found: {arc56_path}")
            return

        app_spec = algokit_utils.Arc56Contract.from_json(arc56_path.read_text())

        # Create base AppClient
        base_client = self.algorand.client.get_app_client_by_id(
            app_spec=app_spec,
            app_id=self.app_id,
            default_sender=self.deployer_address,
            default_signer=algokit_utils.SigningAccountTransactionSigner(self._deployer_private_key)
            if self._deployer_private_key
            else None,
        )

        # Wrap in typed client
        self.app_client = EventTicketingClient(base_client)
        logger.info("EventTicketing typed client initialized.")

    async def mint_ticket_on_chain(
        self,
        ticket_price: int,
        seat_number: str,
    ) -> dict:
        """
        Mint a ticket NFT on the Algorand blockchain.

        Args:
            ticket_price: Price in microAlgos (also sets max_resale_price)
            seat_number: Seat identifier (e.g., "VIP-1")

        Returns:
            dict with asa_id, txn_id, and app_address
        """
        if not self.app_client:
            raise RuntimeError("App client not initialized. Set APP_ID and DEPLOYER_MNEMONIC in .env")

        logger.info(f"Minting ticket: seat={seat_number}, price={ticket_price}")

        result = self.app_client.send.mint_ticket(
            args=MintTicketArgs(
                ticket_price=ticket_price,
                seat_number=seat_number,
            ),
        )

        asa_id = result.abi_return
        txn_id = result.tx_ids[0] if result.tx_ids else None

        logger.info(f"Minted ASA {asa_id} (txn: {txn_id})")

        return {
            "asa_id": asa_id,
            "txn_id": txn_id,
            "app_address": self.app_client._app_client.app_address,
        }

    async def transfer_ticket_on_chain(
        self,
        asa_id: int,
        buyer_address: str,
        price: int,
    ) -> dict:
        """
        Transfer a ticket NFT to a buyer (requires buyer to send payment).
        This is called by the backend to orchestrate the transfer.

        Returns:
            dict with txn_id
        """
        if not self.app_client:
            raise RuntimeError("App client not initialized.")

        logger.info(f"Transferring ASA {asa_id} to {buyer_address} for {price} microAlgos")

        # The transfer_ticket method expects a grouped payment transaction
        # For backend-mediated transfers, we compose the atomic group
        result = self.app_client.send.transfer_ticket(
            args=TransferTicketArgs(
                payment=algokit_utils.PayParams(
                    sender=buyer_address,
                    receiver=self.app_client._app_client.app_address,
                    amount=price,
                ),
                asset=asa_id,
            ),
        )

        txn_id = result.tx_ids[0] if result.tx_ids else None
        logger.info(f"Transfer complete (txn: {txn_id})")

        return {"txn_id": txn_id}

    def get_app_info(self) -> dict:
        """Get current app info from the chain."""
        if not self.algod_client or not self.app_id:
            return {"error": "Not configured"}

        try:
            info = self.algod_client.application_info(self.app_id)
            return info
        except Exception as e:
            logger.error(f"Failed to get app info: {e}")
            return {"error": str(e)}


# Singleton instance
algorand_service = AlgorandService()
