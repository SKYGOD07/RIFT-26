"""
Testnet Deployment Script for EventTicketing Smart Contract.

Usage:
    1. Copy .env.template to .env
    2. Fill in DEPLOYER_MNEMONIC with a funded Testnet account
    3. Run: python -m smart_contracts.ticketing.deploy_testnet
"""

import os
import sys
from pathlib import Path

from algosdk import mnemonic, account
from algosdk.v2client import algod
from dotenv import load_dotenv

import algokit_utils

# Load environment
load_dotenv(Path(__file__).parent.parent.parent / ".env")


def get_algod_client() -> algod.AlgodClient:
    """Create an Algod client pointing to Testnet."""
    server = os.environ.get("ALGOD_SERVER", "https://testnet-api.algonode.cloud")
    token = os.environ.get("ALGOD_TOKEN", "")
    port = os.environ.get("ALGOD_PORT", "")
    if port:
        server = f"{server}:{port}"
    return algod.AlgodClient(token, server)


def deploy() -> None:
    """Deploy EventTicketing to Testnet and print App ID."""
    # 1. Validate mnemonic
    deployer_mnemonic = os.environ.get("DEPLOYER_MNEMONIC", "").strip()
    if not deployer_mnemonic:
        print("ERROR: Set DEPLOYER_MNEMONIC in .env (25-word Algorand mnemonic)")
        print("Fund at: https://bank.testnet.algorand.network/")
        sys.exit(1)

    private_key = mnemonic.to_private_key(deployer_mnemonic)
    address = account.address_from_private_key(private_key)
    print(f"Deployer address: {address}")

    # 2. Create Algod client
    algod_client = get_algod_client()

    # Check balance
    account_info = algod_client.account_info(address)
    balance = account_info.get("amount", 0)
    print(f"Balance: {balance / 1_000_000:.6f} ALGO")
    if balance < 1_000_000:
        print("ERROR: Insufficient funds. Need at least 1 ALGO.")
        print("Fund at: https://bank.testnet.algorand.network/")
        sys.exit(1)

    # 3. Create AlgorandClient
    algorand = algokit_utils.AlgorandClient.testnet()

    # 4. Load Deployer Account from mnemonic
    deployer = algorand.account.from_mnemonic(mnemonic=deployer_mnemonic)
    print(f"Deployer address: {deployer.address}")

    # 5. Load ARC-56 app spec
    arc56_path = Path(__file__).parent.parent / "artifacts" / "ticketing" / "EventTicketing.arc56.json"
    if not arc56_path.exists():
        print(f"ERROR: ARC-56 spec not found at {arc56_path}")
        print("Run: python -m smart_contracts build ticketing")
        sys.exit(1)

    app_spec = algokit_utils.Arc56Contract.from_json(arc56_path.read_text())

    # 6. Create app factory and deploy
    factory = algorand.client.get_app_factory(
        app_spec=app_spec,
        default_sender=deployer.address,
        default_signer=deployer.signer,
    )

    print("Deploying EventTicketing to Testnet...")
    app_client, deploy_result = factory.deploy(
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        on_update=algokit_utils.OnUpdate.AppendApp,
    )

    app_id = app_client.app_id
    app_address = app_client.app_address
    print(f"\n{'='*60}")
    print(f"  DEPLOYED SUCCESSFULLY!")
    print(f"  App ID:      {app_id}")
    print(f"  App Address: {app_address}")
    print(f"  View on Lora: https://lora.algokit.io/testnet/application/{app_id}")
    print(f"{'='*60}\n")

    # 7. Save App ID to .env
    env_path = Path(__file__).parent.parent.parent / ".env"
    env_content = env_path.read_text() if env_path.exists() else ""

    # Update or add APP_ID
    updates = {"APP_ID": str(app_id), "VITE_APP_ID": str(app_id)}
    for key, value in updates.items():
        if f"{key}=" in env_content:
            import re
            env_content = re.sub(rf"^{key}=.*$", f"{key}={value}", env_content, flags=re.MULTILINE)
        else:
            env_content += f"\n{key}={value}\n"

    env_path.write_text(env_content)
    print(f"Saved APP_ID={app_id} to {env_path}")

    # 8. Fund the app account (0.5 ALGO for inner txns)
    print("Funding app account with 0.5 ALGO for inner transactions...")
    algorand.send.payment(
        algokit_utils.PaymentParams(
            sender=deployer.address,
            signer=deployer.signer,
            receiver=app_address,
            amount=algokit_utils.AlgoAmount.from_micro_algo(500_000),  # 0.5 ALGO
        )
    )
    print("App account funded.")

    # 9. Mint a test ticket
    print("\nMinting test ticket (VIP-1)...")
    from smart_contracts.artifacts.ticketing.event_ticketing_client import (
        EventTicketingClient,
        MintTicketArgs,
    )

    # Create the typed client from the deployed app
    typed_client = EventTicketingClient(app_client)
    result = typed_client.send.mint_ticket(
        args=MintTicketArgs(ticket_price=1_000_000, seat_number="VIP-1"),
        params=algokit_utils.CommonAppCallParams(extra_fee=algokit_utils.AlgoAmount.from_micro_algo(1_000)),
    )
    print(f"Minted ticket ASA ID: {result.abi_return}")
    print(f"\nDeployment complete! Your App ID is: {app_id}")


if __name__ == "__main__":
    deploy()
