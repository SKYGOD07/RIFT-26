from algokit_utils import (
    TransactionParameters,
    create_kmd_wallet_account,
    get_algod_client,
    get_indexer_client,
    get_kmd_client_from_algokit_config,
)
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import PaymentTxn, SuggestedParams
from smart_contracts.artifacts.ticketing.event_ticketing_client import (
    EventTicketingClient,
)

def deploy():
    # 1. Setup clients
    algod_client = get_algod_client()
    indexer_client = get_indexer_client()
    kmd_client = get_kmd_client_from_algokit_config()
    
    # 2. Get deployer account and fund it if needed (LocalNet default is rich)
    # Using 'unencrypted-default-wallet' from LocalNet with empty password
    deployer = create_kmd_wallet_account(kmd_client, "unencrypted-default-wallet", "")
    
    print(f"Deploying with account: {deployer.address}")

    # 3. Create the client
    app_client = EventTicketingClient(
        algod_client=algod_client,
        creator=deployer,
        indexer_client=indexer_client,
    )

    # 4. Deploy the app
    app_spec = app_client.deploy(
        on_schema_break="append",
        on_update="append",
    )
    app_id = app_spec.app_id
    app_addr = app_spec.app_address
    print(f"App deployed successfully! App ID: {app_id}, Address: {app_addr}")

    # 5. Fund the app account with 10 ALGO
    sp = algod_client.suggested_params()
    # 10 ALGO = 10,000,000 microAlgos
    fund_txn = PaymentTxn(deployer.address, sp, app_addr, 10_000_000)
    
    # Sign and send transaction
    signed_fund_txn = fund_txn.sign(deployer.private_key)
    txid = algod_client.send_transaction(signed_fund_txn)
    print(f"Funding transaction sent: {txid}")
    
    # Wait for confirmation
    from algosdk.transaction import wait_for_confirmation
    wait_for_confirmation(algod_client, txid, 4)
    print("App account funded with 10 ALGO")

    # 6. Mint 5 VIP tickets
    valid_ticket_price = 100 # Example price
    
    for i in range(1, 6):
        seat_num = f"VIP-{i}"
        
        # Call mint_ticket method
        # Note: mint_ticket returns an Asset (uint64 asset ID)
        result = app_client.mint_ticket(
            ticket_price=valid_ticket_price,
            seat_number=seat_num,
            transaction_parameters=TransactionParameters(
                sender=deployer.address,
                signer=deployer.signer,
                # Increase fee strictly for inner txn coverage if needed, 
                # though usually covered by inner txn pooling or explicit coverage
                # foreign_assets=[], # If needed
            )
        )
        
        created_asset_id = result.return_value
        print(f"Minted Ticket {i} (Seat: {seat_num}): Asset ID {created_asset_id}")

    print("Deployment and minting complete!")

if __name__ == "__main__":
    deploy()
