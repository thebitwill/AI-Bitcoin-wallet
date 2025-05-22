# tests/test_wallet.py
import unittest
# Import BipUtilsNotAvailableError to specifically catch it
from app.wallet_logic.wallet import generate_mnemonic, create_wallet_from_mnemonic, bip_utils_available, BipUtilsNotAvailableError

class TestWallet(unittest.TestCase):
    """Test suite for wallet generation functions."""

    def test_generate_mnemonic(self):
        """Test the generate_mnemonic function."""
        mnemonic = generate_mnemonic()
        self.assertIsInstance(mnemonic, str, "Mnemonic should be a string.")
        words = mnemonic.split()
        
        if bip_utils_available:
            # If bip_utils is available, a real mnemonic is generated
            self.assertEqual(len(words), 12, "Generated mnemonic should consist of 12 words when bip_utils is available.")
            # We can't check for specific words as it's random, but we can check if it's not the fallback
            self.assertNotEqual(mnemonic, "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
                                "Should generate a random mnemonic, not the fallback, when bip_utils is available.")
        else:
            # If bip_utils is not available, it returns the fixed fallback mnemonic
            self.assertEqual(len(words), 12, "Fallback mnemonic should consist of 12 words.")
            self.assertEqual(mnemonic, "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
                             "Should return the fixed fallback mnemonic when bip_utils is not available.")

    def test_create_wallet_from_valid_mnemonic(self):
        """Test create_wallet_from_mnemonic with a known valid mnemonic."""
        test_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        expected_address = "18fAsheD3yUeSjNqN2hLzT2c9x3E2qYDWN"
        # expected_wif = "L1uyy5qTuGrVXrmrsvHWHgVzW9kKdrp27wBC7Vs6nZDTF2GYP6zV" 
        # expected_pub_hex = "03e770fd264a6afd67a06838980076997582c66310710618718021374199058999"

        if not bip_utils_available:
            with self.assertRaises(BipUtilsNotAvailableError):
                create_wallet_from_mnemonic(test_mnemonic)
            self.skipTest("bip_utils not available, skipping valid mnemonic test's main assertions.")
            return

        wallet_details = create_wallet_from_mnemonic(test_mnemonic)

        self.assertIsInstance(wallet_details, dict)
        self.assertIn("mnemonic", wallet_details)
        self.assertIn("private_key_wif", wallet_details)
        self.assertIn("public_key_hex", wallet_details)
        self.assertIn("address", wallet_details)
        self.assertEqual(wallet_details["mnemonic"], test_mnemonic)
        self.assertEqual(wallet_details["address"], expected_address)
        self.assertTrue(wallet_details["private_key_wif"].startswith(('K', 'L', '5')))
        self.assertTrue(wallet_details["public_key_hex"].startswith(('02', '03', '04')))

    def test_create_wallet_from_invalid_mnemonic_short(self):
        """Test create_wallet_from_mnemonic with a too short mnemonic."""
        if not bip_utils_available:
            self.skipTest("bip_utils not available, cannot test specific mnemonic validation errors.")
            return
            
        # This import is safe here because the test is skipped if bip_utils is not available
        from bip_utils.bip39.bip39_ex import Bip39InvalidMnemonicEx 

        invalid_mnemonic = "abandon abandon"
        # The create_wallet_from_mnemonic wraps the Bip39InvalidMnemonicEx in a ValueError
        with self.assertRaisesRegex(ValueError, "Failed to create wallet from mnemonic: .*Invalid mnemonic bit length.*"):
            create_wallet_from_mnemonic(invalid_mnemonic)
            
    def test_create_wallet_from_invalid_mnemonic_checksum(self):
        """Test create_wallet_from_mnemonic with a mnemonic with invalid checksum."""
        if not bip_utils_available:
            self.skipTest("bip_utils not available, cannot test specific mnemonic validation errors.")
            return

        from bip_utils.bip39.bip39_ex import Bip39InvalidMnemonicEx

        invalid_mnemonic_checksum = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon zoo"
        with self.assertRaisesRegex(ValueError, "Failed to create wallet from mnemonic: .*Invalid checksum.*"):
            create_wallet_from_mnemonic(invalid_mnemonic_checksum)

    def test_create_wallet_from_empty_mnemonic(self):
        """Test create_wallet_from_mnemonic with an empty string."""
        if not bip_utils_available:
            # Even without bip_utils, an empty mnemonic should ideally be caught before bip_utils is involved,
            # but the current implementation might pass it to Bip39SeedGenerator if bip_utils was available.
            # If bip_utils is NOT available, it raises BipUtilsNotAvailableError first.
            with self.assertRaises(BipUtilsNotAvailableError):
                create_wallet_from_mnemonic("")
            self.skipTest("bip_utils not available. Tested for BipUtilsNotAvailableError on empty mnemonic.")
            return

        # If bip_utils IS available, it should raise an error related to empty/invalid mnemonic.
        # The exact error message might come from bip_utils itself.
        with self.assertRaisesRegex(ValueError, "Failed to create wallet from mnemonic: .*Mnemonic cannot be empty.*"):
             create_wallet_from_mnemonic("")

if __name__ == '__main__':
    unittest.main()
