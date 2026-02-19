import pytest
import algokit_utils
from algokit_utils import (
    AlgorandClient,
    OnSchemaBreak,
    OnUpdate,
    AlgoAmount,
    TransactionParameters,
)
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import PaymentTxn
from smart_contracts.artifacts.ticketing.event_ticketing_client import (
    EventTicketingFactory,
    EventTicketingClient,
)

@pytest.fixture(scope="module")
def app_client(algorand_client: AlgorandClient) -> EventTicketingClient:
    """Deploy the contract and return the client."""
    creator = algorand_client.account.from_environment("CREATOR", fund_with=AlgoAmount.from_algo(1000))
    
    factory = algorand_client.client.get_typed_app_factory(
        EventTicketingFactory, 
        default_sender=creator.address
    )
    
    client, _ = factory.deploy(
        on_schema_break="append",
        on_update="append",
    )
    
    # Fund the app account for inner transactions (opt-ins, etc.)
    algorand_client.send.payment(
        sender=creator.address,
        receiver=client.app_address,
        amount=AlgoAmount.from_algo(1)
    )
    
    return client

def test_scalper_attack(app_client: EventTicketingClient, algorand_client: AlgorandClient):
    """
    Test that the contract rejects a transfer with a price higher than max_resale_price.
    """
    # 1. Mint a ticket with a price of 100 microAlgos
    ticket_price = 100
    seat_number = "VIP-1"
    
    mint_result = app_client.send.mint_ticket(
        args=(ticket_price, seat_number)
    )
    asset_id = mint_result.abi_return
    
    print(f"Minted asset {asset_id} with max resale price {ticket_price}")

    scalper = algorand_client.account.from_environment("SCALPER", fund_with=AlgoAmount.from_algo(100))
    fan = algorand_client.account.from_environment("FAN", fund_with=AlgoAmount.from_algo(100))
    
    # Opt-in to asset
    algorand_client.send.asset_opt_in(
        sender=scalper.address,
        asset_id=asset_id,
        signer=scalper.signer
    )
    algorand_client.send.asset_opt_in(
        sender=fan.address,
        asset_id=asset_id,
        signer=fan.signer
    )

    # SCENARIO 1: Scalper tries to buy/claim the ticket paying MORE than max_price
    print("Scalper trying to buy for 500 (limit 100)...")
    
    # Construct payment transaction
    sp = app_client.algorand.client.algod.suggested_params()
    payment_scalper = PaymentTxn(
        sender=scalper.address,
        sp=sp,
        receiver=app_client.app_address,
        # 500% of price
        amt=500
    )
    
    # Expect failure
    with pytest.raises(Exception, match="Price exceeds max resale price"):
        app_client.send.transfer_ticket(
            args=(
                TransactionWithSigner(payment_scalper, scalper.signer),
                asset_id
            ),
            send_params={"sender": scalper.address, "signer": scalper.signer}
        )
    print("Scalper attack REJECTED as expected!")

    # SCENARIO 2: Fan buys at face value
    print("Fan buying for 100...")
    payment_fan = PaymentTxn(
        sender=fan.address,
        sp=sp,
        receiver=app_client.app_address,
        amt=100
    )
    
    app_client.send.transfer_ticket(
        args=(
            TransactionWithSigner(payment_fan, fan.signer),
            asset_id
        ),
        send_params={"sender": fan.address, "signer": fan.signer}
    )
    print("Fan purchase ACCEPTED!")
    
    # Verify ownership
    account_info = app_client.algorand.client.algod.account_asset_info(fan.address, asset_id)
    assert account_info['asset-holding']['amount'] == 1
    print("Fan owns the ticket.")
