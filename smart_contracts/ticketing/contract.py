from algopy import ARC4Contract, String, UInt64, Asset, Global, itxn, gtxn, arc4, Txn

class EventTicketing(ARC4Contract):
    max_resale_price: UInt64

    @arc4.abimethod
    def mint_ticket(self, ticket_price: UInt64, seat_number: String) -> Asset:
        self.max_resale_price = ticket_price
        
        return itxn.AssetConfig(
            total=1,
            decimals=0,
            default_frozen=False,
            unit_name="TICKET",
            asset_name=seat_number,
            manager=Global.current_application_address,
            reserve=Global.current_application_address,
            freeze=Global.current_application_address,
            clawback=Global.current_application_address,
        ).submit().created_asset

    @arc4.abimethod
    def transfer_ticket(self, payment: gtxn.PaymentTransaction, asset: Asset) -> None:
        assert payment.amount <= self.max_resale_price, "Price exceeds max resale price"
        assert payment.receiver == Global.current_application_address, "Payment must be to the contract"
        
        itxn.AssetTransfer(
            xfer_asset=asset,
            asset_receiver=Txn.sender,
            asset_amount=1,
        ).submit()
