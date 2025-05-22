# settings.py
# Manages saving and loading of application settings, particularly for the inheritance feature.
# Settings are stored in JSON files within a dedicated directory.

import json
import os
from typing import Dict, Optional, Any

# Define a base directory for application data.
# In a real application, this should be a platform-appropriate user data directory.
# For example, using `appdirs` library: `user_data_dir("PyQtBitcoinWallet", "YourAppName")`
APP_DATA_DIR = "wallet_data" 
SETTINGS_DIR = os.path.join(APP_DATA_DIR, "settings")

# Ensure the settings directory exists upon module load.
# This prevents errors if the directory hasn't been created yet when functions are called.
try:
    os.makedirs(SETTINGS_DIR, exist_ok=True)
except OSError as e:
    # Handle potential errors during directory creation, e.g., permission issues.
    print(f"Warning: Could not create settings directory at '{SETTINGS_DIR}': {e}")


def _get_settings_filepath(wallet_identifier: str) -> str:
    """
    Generates a standardized filepath for a given wallet's inheritance settings.

    Args:
        wallet_identifier (str): A unique identifier for the wallet (e.g., its address).
                                 This identifier will be part of the filename.

    Returns:
        str: The full path to the settings JSON file for the specified wallet.
    """
    # Basic sanitization: replace potentially problematic characters for filenames.
    # A more robust approach might involve hashing or using a UUID if identifiers are complex.
    safe_identifier = "".join(c if c.isalnum() else "_" for c in wallet_identifier)
    filename = f"inheritance_settings_{safe_identifier}.json"
    return os.path.join(SETTINGS_DIR, filename)

def save_inheritance_settings(wallet_identifier: str, settings: Dict[str, Any]) -> bool:
    """
    Saves inheritance settings for a specific wallet to a JSON file.

    The settings are stored in a file named `inheritance_settings_{wallet_identifier}.json`
    within the `SETTINGS_DIR`.

    Args:
        wallet_identifier (str): A unique identifier for the wallet.
        settings (Dict[str, Any]): A dictionary containing the inheritance settings to save.
                                   Expected keys: 'enabled', 'beneficiary_address', 
                                   'inactivity_period', 'transfer_amount'.

    Returns:
        bool: True if settings were saved successfully, False otherwise.
    """
    if not wallet_identifier:
        print("Error: Wallet identifier is required to save inheritance settings.")
        return False
        
    filepath = _get_settings_filepath(wallet_identifier)
    print(f"Attempting to save inheritance settings for wallet '{wallet_identifier}' to: {filepath}")
    print(f"  Settings being saved: {settings}")
    
    try:
        with open(filepath, 'w') as f:
            json.dump(settings, f, indent=4) # Use indent for readability
        print(f"  Successfully saved inheritance settings to {filepath}")
        return True
    except IOError as e: # More specific exception for I/O errors
        print(f"  IOError saving settings to {filepath}: {e}")
        return False
    except Exception as e: # Catch any other unexpected errors during save
        print(f"  An unexpected error occurred while saving settings: {e}")
        return False

def load_inheritance_settings(wallet_identifier: str) -> Optional[Dict[str, Any]]:
    """
    Loads inheritance settings for a specific wallet from its JSON file.

    If the settings file does not exist, it returns a default set of inheritance settings.

    Args:
        wallet_identifier (str): A unique identifier for the wallet.

    Returns:
        Optional[Dict[str, Any]]: A dictionary with the loaded inheritance settings,
                                   a default dictionary if the file is not found,
                                   or None if a critical error occurs during loading.
    """
    if not wallet_identifier:
        print("Error: Wallet identifier is required to load inheritance settings.")
        return None # Or raise ValueError

    filepath = _get_settings_filepath(wallet_identifier)
    print(f"Attempting to load inheritance settings for wallet '{wallet_identifier}' from: {filepath}")
    
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                settings = json.load(f)
            print(f"  Successfully loaded inheritance settings: {settings}")
            return settings
        else:
            # File not found, return default settings as specified for the application.
            print(f"  No settings file found at {filepath}. Returning default inheritance settings.")
            return {
                'enabled': False, 
                'beneficiary_address': '', 
                'inactivity_period': 90, # Default inactivity period in days
                'transfer_amount': '0.0'   # Default transfer amount in BTC (as string)
            }
    except IOError as e:
        print(f"  IOError loading settings from {filepath}: {e}")
        return None # Indicate error by returning None
    except json.JSONDecodeError as e:
        print(f"  Error decoding JSON from {filepath}: {e}. File might be corrupt or not valid JSON.")
        return None # Indicate error
    except Exception as e:
        print(f"  An unexpected error occurred while loading settings: {e}")
        return None


if __name__ == '__main__':
    # Example usage and testing of the settings functions.
    # These tests demonstrate saving, loading, and handling of non-existent settings.
    test_wallet_id_1 = "my_test_wallet_address_123"
    test_wallet_id_2 = "another_wallet_456"

    print("\n--- Testing save_inheritance_settings ---")
    settings_to_save_1 = {
        'enabled': True,
        'beneficiary_address': '1BeneficiaryAddressHere',
        'inactivity_period': 180, # days
        'transfer_amount': '1.25' # BTC
    }
    save_success_1 = save_inheritance_settings(test_wallet_id_1, settings_to_save_1)
    print(f"Save successful for {test_wallet_id_1}: {save_success_1}")

    settings_to_save_2 = {
        'enabled': False,
        'beneficiary_address': '',
        'inactivity_period': 90,
        'transfer_amount': '0.0'
    }
    save_success_2 = save_inheritance_settings(test_wallet_id_2, settings_to_save_2)
    print(f"Save successful for {test_wallet_id_2}: {save_success_2}")

    print("\n--- Testing load_inheritance_settings ---")
    loaded_settings_1 = load_inheritance_settings(test_wallet_id_1)
    if loaded_settings_1:
        print(f"Loaded settings for {test_wallet_id_1}: {loaded_settings_1}")
        assert loaded_settings_1 == settings_to_save_1
    else:
        print(f"Could not load settings for {test_wallet_id_1} or they were default.")

    loaded_settings_2 = load_inheritance_settings(test_wallet_id_2)
    if loaded_settings_2:
        print(f"Loaded settings for {test_wallet_id_2}: {loaded_settings_2}")
        assert loaded_settings_2 == settings_to_save_2
    else:
        print(f"Could not load settings for {test_wallet_id_2} or they were default.")
        
    # Test loading non-existent settings
    non_existent_wallet_id = "wallet_does_not_exist_789"
    print(f"\n--- Testing load_inheritance_settings for non-existent wallet: {non_existent_wallet_id} ---")
    loaded_settings_non_existent = load_inheritance_settings(non_existent_wallet_id)
    if loaded_settings_non_existent:
        print(f"Loaded settings for {non_existent_wallet_id}: {loaded_settings_non_existent} (Should be default)")
        # Check if it matches the default structure provided by load_inheritance_settings
        assert loaded_settings_non_existent['enabled'] == False
        assert loaded_settings_non_existent['beneficiary_address'] == ''
    else:
        print(f"Settings for {non_existent_wallet_id} correctly returned None or default on first load.")

    # Test saving with an empty wallet_identifier (should fail)
    print("\n--- Testing save_inheritance_settings with empty wallet_id ---")
    save_fail = save_inheritance_settings("", settings_to_save_1)
    print(f"Save attempt with empty ID successful: {save_fail} (should be False)")
    assert not save_fail

    print("\n--- Testing load_inheritance_settings with empty wallet_id ---")
    load_fail = load_inheritance_settings("")
    print(f"Load attempt with empty ID returned: {load_fail} (should be None)")
    assert load_fail is None
    
    print("\nAll settings.py tests finished.")
