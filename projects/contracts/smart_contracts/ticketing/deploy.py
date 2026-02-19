from algokit_utils import (
    AlgorandClient,
    AlgoAmount
)
from smart_contracts.artifacts.ticketing.event_ticketing_client import (
    EventTicketingFactory,
)

def deploy():
    # 1. Setup client (using from_environment to support LocalNet/TestNet/MainNet)
    algorand = AlgorandClient.from_environment()
    
    # 2. Get deployer account
    deployer = algorand.account.from_environment("DEPLOYER", fund_with=AlgoAmount.from_algo(10))
    print(f"Deploying with account: {deployer.address}")

    # 3. Create the factory
    factory = algorand.client.get_typed_app_factory(
        EventTicketingFactory, 
        default_sender=deployer.address
    )

    # 4. Deploy the app
    app_client, result = factory.deploy(
        on_schema_break="append",
        on_update="append",
    )
    
    app_id = app_client.app_id
    app_addr = app_client.app_address
    print(f"App deployed successfully! App ID: {app_id}, Address: {app_addr}")

    # 5. Fund the app account with 10 ALGO
    algorand.send.payment(
        sender=deployer.address,
        receiver=app_addr,
        amount=AlgoAmount.from_algo(10)
    )
    print("App account funded with 10 ALGO")

    # 6. Mint 5 VIP tickets
    valid_ticket_price = 100 # Example price
    
    for i in range(1, 6):
        seat_num = f"VIP-{i}"
        
        # Call mint_ticket method
        # Returns SendAppTransactionResult[int] where generic type is the return value
        result = app_client.send.mint_ticket(
            args=(valid_ticket_price, seat_num)
        )
        
        created_asset_id = result.abi_return
        print(f"Minted Ticket {i} (Seat: {seat_num}): Asset ID {created_asset_id}")

    print("Deployment and minting complete!")

if __name__ == "__main__":
    deploy()
