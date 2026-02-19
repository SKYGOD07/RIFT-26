"""
Generate and fund two LocalNet accounts (Alice & Bob) with 100 Algos each.

Usage:
    cd projects/contracts
    .venv\Scripts\python scripts\fund_accounts.py

Requires: Docker running with AlgoKit LocalNet (algokit localnet start)
"""

import algokit_utils
from algokit_utils import AlgorandClient, PaymentParams, AlgoAmount


def main() -> None:
    # 1. Connect to LocalNet
    algorand = AlgorandClient.default_localnet()
    print("Connected to AlgoKit LocalNet\n")

    # 2. Get the default LocalNet dispenser (pre-funded account)
    dispenser = algorand.account.localnet_dispenser()
    print(f"Dispenser: {dispenser.address}")

    # 3. Generate random accounts for Alice and Bob
    alice = algorand.account.random()
    bob = algorand.account.random()

    print(f"Alice:     {alice.address}")
    print(f"Bob:       {bob.address}\n")

    # 4. Fund Alice with exactly 100 Algos (100_000_000 microAlgos)
    algorand.send.payment(
        PaymentParams(
            sender=dispenser.address,
            receiver=alice.address,
            amount=AlgoAmount.from_micro_algo(100_000_000),  # 100 ALGO
        )
    )
    print("✅ Alice funded with 100 ALGO")

    # 5. Fund Bob with exactly 100 Algos
    algorand.send.payment(
        PaymentParams(
            sender=dispenser.address,
            receiver=bob.address,
            amount=AlgoAmount.from_micro_algo(100_000_000),  # 100 ALGO
        )
    )
    print("✅ Bob funded with 100 ALGO")

    # 6. Verify balances
    alice_info = algorand.client.algod.account_info(alice.address)
    bob_info = algorand.client.algod.account_info(bob.address)

    print(f"\n{'='*50}")
    print(f"Alice balance: {alice_info['amount'] / 1_000_000:.6f} ALGO")
    print(f"Bob balance:   {bob_info['amount'] / 1_000_000:.6f} ALGO")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
