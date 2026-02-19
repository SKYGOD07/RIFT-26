import pytest
import algokit_utils
from algokit_utils import (
    AlgorandClient,
    OnSchemaBreak,
    OnUpdate,
    PaymentTxnParams,
    TransactionParameters,
)
from algosdk.atomic_transaction_composer import TransactionWithSigner
from smart_contracts.artifacts.ticketing.event_ticketing_client import (
    EventTicketingClient,
)

@pytest.fixture(scope="module")
def app_client(algorand_client: AlgorandClient) -> EventTicketingClient:
    """Deploy the contract and return the client."""
    creator = algorand_client.account.random()
    # Fund creator
    algorand_client.send.payment(
        PaymentTxnParams(
            sender=algorand_client.account.localnet_app_account().address,
            receiver=creator.address,
            amount=10_000_000,
        )
    )
    
    client = EventTicketingClient(
        algod_client=algorand_client.client.algod,
        creator=creator,
        indexer_client=algorand_client.client.indexer,
    )
    
    client.deploy(
        on_schema_break=OnSchemaBreak.Append,
        on_update=OnUpdate.Append,
    )
    
    # Fund the app account for inner transactions (opt-ins, etc.)
    algorand_client.send.payment(
        PaymentTxnParams(
            sender=creator.address,
            receiver=client.app_address,
            amount=1_000_000,
        )
    )
    
    return client

def test_scalper_attack(app_client: EventTicketingClient, algorand_client: AlgorandClient):
    """
    Test that the contract rejects a transfer with a price higher than max_resale_price.
    """
    # 1. Mint a ticket with a price of 100 microAlgos
    ticket_price = 100
    seat_number = "VIP-1"
    
    mint_result = app_client.mint_ticket(
        ticket_price=ticket_price,
        seat_number=seat_number,
    )
    asset_id = mint_result.return_value
    
    print(f"Minted asset {asset_id} with max resale price {ticket_price}")

    # Opt-in scalper and fan to the asset - handled automatically by atomic_transaction_composer in Transfer? 
    # No, usually need explicit opt-in for ASAs unless using specific ARC standards that allow implicitly.
    # Standard ASA requires opt-in.
    
    scalper = algorand_client.account.random()
    fan = algorand_client.account.random()
    
    # Fund scalper and fan
    algorand_client.send.payment(
        PaymentTxnParams(
            sender=algorand_client.account.localnet_app_account().address,
            receiver=scalper.address,
            amount=10_000_000,
        )
    )
    algorand_client.send.payment(
        PaymentTxnParams(
            sender=algorand_client.account.localnet_app_account().address,
            receiver=fan.address,
            amount=10_000_000,
        )
    )

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

    # Transfer asset from creator to scalper (this should work, initial sale)
    # But wait, our transfer_ticket method logic is:
    # assert payment.amount <= self.max_resale_price
    # assert payment.receiver == Global.current_application_address
    # itxn.AssetTransfer(xfer_asset=asset, asset_receiver=Txn.sender, asset_amount=1)
    
    # So the "transfer_ticket" method IS the purchase method from the contract to the user.
    # It seems the logic I wrote in contract.py handles the "Primary Sale" or "Secondary Sale" 
    # where the contract is the seller/broker.
    
    # Let's test the Contract's enforcement.
    
    # SCENARIO 1: Scalper tries to buy/claim the ticket paying MORE than max_price
    # (Maybe scalper thinks paying more gets them priority? or this simulates a secondary market wrapper?)
    # In this specific contract logic:
    # `transfer_ticket` exchanges Payment -> Asset.
    
    print("Scalper trying to buy for 500 (limit 100)...")
    
    import algosdk
    
    # Construct payment transaction
    sp = app_client.algod_client.suggested_params()
    payment_scalper = algosdk.transaction.PaymentTxn(
        sender=scalper.address,
        sp=sp,
        receiver=app_client.app_address,
        # 500% of price
        amt=500
    )
    
    # Expect failure
    with pytest.raises(Exception, match="Price exceeds max resale price"):
        app_client.transfer_ticket(
            payment=TransactionWithSigner(payment_scalper, scalper.signer),
            asset=asset_id,
            transaction_parameters=algokit_utils.TransactionParameters(
                sender=scalper.address,
                signer=scalper.signer,
            )
        )
    print("Scalper attack REJECTED as expected!")

    # SCENARIO 2: Fan buys at face value
    print("Fan buying for 100...")
    payment_fan = algosdk.transaction.PaymentTxn(
        sender=fan.address,
        sp=sp,
        receiver=app_client.app_address,
        amt=100
    )
    
    app_client.transfer_ticket(
        payment=TransactionWithSigner(payment_fan, fan.signer),
        asset=asset_id,
        transaction_parameters=algokit_utils.TransactionParameters(
            sender=fan.address,
            signer=fan.signer,
        )
    )
    print("Fan purchase ACCEPTED!")
    
    # Verify ownership
    account_info = app_client.algod_client.account_asset_info(fan.address, asset_id)
    assert account_info['asset-holding']['amount'] == 1
    print("Fan owns the ticket.")
