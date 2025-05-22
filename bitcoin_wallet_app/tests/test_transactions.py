# tests/test_transactions.py
import unittest
from decimal import Decimal
from typing import List, Dict, Any

# Adjust import path based on test execution context
from app.wallet_logic.transactions import (
    create_transaction, 
    broadcast_transaction, 
    get_balance, 
    get_utxos, 
    get_transaction_history
)

class TestTransactions(unittest.TestCase):
    """Test suite for (mocked) transaction-related functions."""

    def test_create_transaction(self):
        """Test the mock create_transaction function."""
        # Define sample inputs, though they are mostly for logging in the mock
        sender_address = "1SenderAddressPlaceholder"
        private_key_wif = "L1PlaceholderPrivateKeyWIF"
        recipient_address = "1RecipientAddressPlaceholder"
        amount_btc = Decimal("0.01")
        # Mock UTXOs can be simple for this test as the function is mocked
        utxos: List[Dict[str, Any]] = [{"txid": "mocktxid", "vout": 0, "amount_satoshi": 1000000}]
        fee_btc = Decimal("0.0001")

        # The mock function returns a predictable string
        expected_tx_id_part = f"mock_tx_id_for_{recipient_address}_amount{amount_btc}_fee{fee_btc}"
        
        # Call the function
        # We are not checking print statements here, just the return value as per current mock.
        # If print statements were critical, we'd use unittest.mock.patch('builtins.print').
        result_tx_id = create_transaction(
            sender_address, private_key_wif, recipient_address, 
            amount_btc, utxos, fee_btc
        )
        self.assertEqual(result_tx_id, expected_tx_id_part,
                         "Mock create_transaction should return the expected mock transaction ID string.")

    def test_broadcast_transaction(self):
        """Test the mock broadcast_transaction function."""
        # The mock function always returns True
        raw_tx_hex = "mock_raw_tx_hex_data" # Input value doesn't affect mock's current return
        result = broadcast_transaction(raw_tx_hex)
        self.assertTrue(result, "Mock broadcast_transaction should return True.")

    def test_get_balance(self):
        """Test the mock get_balance function."""
        address = "1AddressForBalanceCheck"
        # The mock function returns a fixed Decimal value
        expected_balance = Decimal("0.12345") 
        
        result_balance = get_balance(address)
        self.assertIsInstance(result_balance, Decimal, "Mock get_balance should return a Decimal.")
        self.assertEqual(result_balance, expected_balance,
                         f"Mock get_balance returned {result_balance}, expected {expected_balance}.")

    def test_get_utxos(self):
        """Test the mock get_utxos function."""
        address = "1AddressForUtxoCheck"
        # The mock function returns a list of specific dicts
        result_utxos = get_utxos(address)
        
        self.assertIsInstance(result_utxos, list, "Mock get_utxos should return a list.")
        self.assertTrue(len(result_utxos) > 0, "Mock get_utxos should return non-empty list for testing.")
        
        # Check structure of the first UTXO as an example
        first_utxo = result_utxos[0]
        self.assertIn("txid", first_utxo)
        self.assertIn("vout", first_utxo)
        self.assertIn("amount_satoshi", first_utxo) # or "value"
        self.assertIn("value", first_utxo) # As per current mock

        # Expected mock data structure from transactions.py
        expected_utxo_structure_example = [
            {"txid": "mock_txid_1_for_address_" + address[:5], "vout": 0, "amount_satoshi": 5000000, "scriptpubkey": "mock_script_1", "value": 5000000},
            {"txid": "mock_txid_2_for_address_" + address[:5], "vout": 1, "amount_satoshi": 7300000, "scriptpubkey": "mock_script_2", "value": 7300000}
        ]
        self.assertEqual(result_utxos, expected_utxo_structure_example, "Mock UTXO data does not match expected.")


    def test_get_transaction_history(self):
        """Test the mock get_transaction_history function."""
        address = "1AddressForHistoryCheck"
        # The mock function returns a list of specific dicts
        result_history = get_transaction_history(address)

        self.assertIsInstance(result_history, list, "Mock get_transaction_history should return a list.")
        self.assertTrue(len(result_history) > 0, "Mock get_transaction_history should return non-empty list for testing.")

        # Check structure of the first transaction in history as an example
        first_tx = result_history[0]
        self.assertIn("date", first_tx)
        self.assertIn("type", first_tx)
        self.assertIn("amount", first_tx)
        self.assertIsInstance(first_tx["amount"], Decimal, "Transaction amount should be Decimal.")
        self.assertIn("address", first_tx)
        self.assertIn("tx_id", first_tx)
        
        # Compare with the known mock structure
        expected_history_structure_example = [
             {
                'date': '2023-10-26', 
                'type': 'receive', 
                'amount': Decimal('0.05000000'), 
                'address': 'some_sender_address_1LongEnoughToTestUI', 
                'tx_id': 'mock_tx_id_received_abc123xyz789'
            },
            {
                'date': '2023-10-27', 
                'type': 'send', 
                'amount': Decimal('0.01000000'), 
                'address': 'some_recipient_address_2LongEnoughToTestUI', 
                'tx_id': 'mock_tx_id_sent_def456uvw012'
            },
            {
                'date': '2023-10-28', 
                'type': 'receive', 
                'amount': Decimal('0.12345678'), 
                'address': 'another_sender_address_3WithMoreChars', 
                'tx_id': 'mock_tx_id_received_ghi789rst345'
            },
            {
                'date': '2023-10-29', 
                'type': 'send' if address.startswith("1") else 'receive', 
                'amount': Decimal('0.00200000'), 
                'address': address, 
                'tx_id': 'mock_tx_id_related_to_user_jkl012mno456'
            }
        ]
        self.assertEqual(result_history, expected_history_structure_example, "Mock transaction history data does not match expected.")

if __name__ == '__main__':
    unittest.main()
