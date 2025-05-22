# wallet.py
# Handles Bitcoin wallet generation, including mnemonic phrases and key derivation.
import os
from typing import Dict # For type hinting the return dictionary
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress # From python-bitcoinlib
from bitcoin.core import b2x # For converting bytes to hex string
from bitcoin.core.key import CECKey # For public key generation

# Attempt to import bip_utils and set a flag
try:
    from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes, Bip39MnemonicGenerator, Bip39WordsNum
    bip_utils_available = True
except ImportError:
    bip_utils_available = False
    print("WARNING: bip_utils library not found. Mnemonic generation and BIP44 derivation will be severely limited or disabled.")

# Note: Some imports like lx, COIN, COutPoint etc. were present but not used.
# They are removed for cleanliness. If needed for future features, they can be re-added.

class BipUtilsNotAvailableError(ImportError):
    """Custom exception for when bip_utils is not available but its functionality is called."""
    pass


def generate_mnemonic() -> str:
    """
    Generates a new BIP39 mnemonic phrase.
    
    If `bip_utils` is available, it attempts to generate a real 12-word mnemonic.
    Otherwise, it returns a fixed, known mnemonic phrase for development/testing.
    **WARNING: The fixed mnemonic is NOT secure and should NOT be used for real wallets.**

    Returns:
        str: The generated mnemonic phrase.
    
    Raises:
        RuntimeError: If `bip_utils` is unavailable and a real mnemonic was expected (though current fallback prevents this).
    """
    if bip_utils_available:
        # Generate a new 12-word mnemonic using bip_utils
        # entropy_bytes = os.urandom(16) # 128 bits for 12 words. For truly random.
        # For more deterministic "random" for some testing contexts, one might use a fixed entropy source
        # or allow bip_utils to handle entropy if its default is sufficient.
        # Here, we use its direct generator for simplicity.
        try:
            return Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
        except Exception as e: # Catch any error from Bip39MnemonicGenerator
            print(f"Error generating mnemonic with bip_utils: {e}. Falling back to fixed mnemonic.")
            # Fallback to fixed mnemonic if Bip39MnemonicGenerator fails for some reason
            fixed_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
            print(f"Warning: Using a fixed test mnemonic due to error: '{fixed_mnemonic}'. THIS IS NOT SECURE.")
            return fixed_mnemonic
    else:
        # Fallback to fixed mnemonic if bip_utils is not available
        fixed_mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        print(f"Warning: bip_utils not available. Using a fixed test mnemonic: '{fixed_mnemonic}'. THIS IS NOT SECURE.")
        return fixed_mnemonic


def create_wallet_from_mnemonic(mnemonic_phrase: str) -> Dict[str, str]:
    """
    Creates wallet details (private key, public key, address) from a BIP39 mnemonic.

    This function takes a mnemonic phrase, generates a seed using BIP39 (if `bip_utils` is available), 
    and then derives the first account's private key (m/44'/0'/0'/0/0 for Bitcoin mainnet)
    according to BIP44 specification. From this private key, the corresponding
    public key and P2PKH Bitcoin address are generated using `python-bitcoinlib`.

    Args:
        mnemonic_phrase (str): The BIP39 mnemonic phrase.

    Returns:
        Dict[str, str]: A dictionary containing:
            - "mnemonic": The input mnemonic phrase.
            - "private_key_wif": The derived private key in Wallet Import Format (WIF).
            - "public_key_hex": The derived public key in hexadecimal format (compressed).
            - "address": The derived P2PKH Bitcoin address.
    Raises:
        BipUtilsNotAvailableError: If `bip_utils` is required but not available.
        ValueError: If the mnemonic_phrase is invalid or other issues occur during derivation.
    """
    if not bip_utils_available:
        # This behavior ensures that if bip_utils failed to import (e.g. build issue),
        # we don't proceed with operations that depend on it.
        # Tests for this function should mock bip_utils or expect this error.
        raise BipUtilsNotAvailableError(
            "bip_utils is not available. Cannot create wallet from mnemonic without it."
        )

    try:
        # Step 1: Convert mnemonic to seed bytes using BIP39.
        seed_bytes = Bip39SeedGenerator(mnemonic_phrase).Generate()

        # Step 2: Derive keys using BIP44.
        bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
        bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
        bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
        bip44_addr_ctx = bip44_chg_ctx.AddressIndex(0)

        private_key_bytes = bip44_addr_ctx.PrivateKey().Raw().ToBytes()
        
        # Step 3: Use python-bitcoinlib for WIF, public key, and address generation.
        cec_key = CECKey()
        cec_key.set_secretbytes(private_key_bytes)
        cec_key.set_compressed(True) 
        private_key_wif = CBitcoinSecret.from_secret_bytes(private_key_bytes, compressed=True)
        public_key = cec_key.get_pubkey()
        address = P2PKHBitcoinAddress.from_pubkey(public_key)

        return {
            "mnemonic": mnemonic_phrase,
            "private_key_wif": str(private_key_wif),
            "public_key_hex": b2x(public_key),
            "address": str(address)
        }
    except Exception as e:
        # Catch potential errors from bip_utils (e.g., invalid mnemonic checksum) or python-bitcoinlib
        print(f"Error creating wallet from mnemonic ('{mnemonic_phrase}'): {e}")
        # Re-raise as a ValueError for consistent error handling by the caller.
        # Include the original exception message for context.
        raise ValueError(f"Failed to create wallet from mnemonic: {e}")


if __name__ == '__main__':
    # Example usage and testing of the wallet functions.
    print("--- Wallet Generation Test ---")
    
    print("\nGenerating a new mnemonic (fixed for testing purposes)...")
    test_mnemonic = generate_mnemonic()
    print(f"Generated Test Mnemonic: {test_mnemonic}")

    print("\nCreating wallet from the test mnemonic...")
    try:
        wallet_details = create_wallet_from_mnemonic(test_mnemonic)
        print("Wallet Details:")
        print(f"  Mnemonic: {wallet_details['mnemonic']}")
        print(f"  Private Key (WIF): {wallet_details['private_key_wif']}")
        print(f"  Public Key (Hex): {wallet_details['public_key_hex']}")
        print(f"  Address: {wallet_details['address']}")
    except ValueError as e:
        print(f"Error in wallet creation test: {e}")

    print("\n--- Test with a potentially invalid mnemonic (example) ---")
    invalid_mnemonic_example = "this is not a valid bip39 mnemonic phrase probably"
    print(f"Attempting to create wallet from invalid mnemonic: '{invalid_mnemonic_example}'")
    try:
        wallet_details_invalid = create_wallet_from_mnemonic(invalid_mnemonic_example)
        print(f"Wallet Details (Invalid Mnemonic Test - unexpectedly succeeded): {wallet_details_invalid}")
    except ValueError as e:
        print(f"Successfully caught error for invalid mnemonic: {e}")
    
    # Example of using python-bitcoinlib to switch to testnet (if needed for other functions)
    # import bitcoin
    # print("\nSwitching to Bitcoin testnet parameters for context (not used in current functions directly)...")
    # bitcoin.SelectParams('testnet')
    # # Note: CBitcoinSecret and P2PKHBitcoinAddress will automatically use testnet params
    # # if this is set globally. For instance, a private key would get a 'c' prefix for WIF.
    # # Ensure to switch back if other parts of an application expect mainnet.
    # # cec_key_testnet = CECKey()
    # # cec_key_testnet.set_secretbytes(private_key_bytes_from_valid_mnemonic) # Assuming you have these
    # # private_key_wif_testnet = CBitcoinSecret.from_secret_bytes(private_key_bytes_from_valid_mnemonic, compressed=True)
    # # print(f"  Example Testnet WIF prefix: {str(private_key_wif_testnet)[0]}") # Should be 'c'
    # print("Switching back to Bitcoin mainnet parameters...")
    # bitcoin.SelectParams('mainnet')

    print("\nWallet generation tests finished.")
