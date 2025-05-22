# activity.py
# Handles tracking and retrieving the last activity timestamp for a wallet.
# This is primarily used for the inheritance feature to determine wallet inactivity.

import json
import os
from datetime import datetime, timezone
from typing import Optional # Dict was imported but not used in type hints here

# Use the same base directory as settings.py for consistency.
APP_DATA_DIR = "wallet_data" 
ACTIVITY_DIR = os.path.join(APP_DATA_DIR, "activity")

# Ensure the activity directory exists.
try:
    os.makedirs(ACTIVITY_DIR, exist_ok=True)
except OSError as e:
    print(f"Warning: Could not create activity directory at '{ACTIVITY_DIR}': {e}")


def _get_activity_filepath(wallet_identifier: str) -> str:
    """
    Generates a standardized filepath for a given wallet's activity log file.

    Args:
        wallet_identifier (str): A unique identifier for the wallet (e.g., its address).

    Returns:
        str: The full path to the activity log JSON file for the wallet.
    """
    safe_identifier = "".join(c if c.isalnum() else "_" for c in wallet_identifier)
    filename = f"activity_log_{safe_identifier}.json"
    return os.path.join(ACTIVITY_DIR, filename)

def update_last_activity_timestamp(wallet_identifier: str) -> bool:
    """
    Updates the last activity timestamp for the given wallet to the current UTC time.

    The timestamp is stored in ISO 8601 format in a JSON file specific to the wallet.

    Args:
        wallet_identifier (str): The unique identifier for the wallet.

    Returns:
        bool: True if the timestamp was successfully updated, False otherwise.
    """
    if not wallet_identifier:
        print("Error: Wallet identifier is required to update activity timestamp.")
        return False

    filepath = _get_activity_filepath(wallet_identifier)
    now_utc = datetime.now(timezone.utc)
    timestamp_str = now_utc.isoformat() # ISO 8601 format, e.g., "YYYY-MM-DDTHH:MM:SS.ffffff+00:00"
    
    activity_data = {'last_activity_timestamp': timestamp_str}
    
    print(f"Attempting to update last activity timestamp for wallet '{wallet_identifier}' to: {filepath}")
    print(f"  New Timestamp: {timestamp_str}")
    
    try:
        with open(filepath, 'w') as f:
            json.dump(activity_data, f, indent=4)
        print(f"  Successfully updated activity timestamp in {filepath}")
        return True
    except IOError as e:
        print(f"  IOError saving activity timestamp to {filepath}: {e}")
        return False
    except Exception as e:
        print(f"  An unexpected error occurred during activity timestamp update: {e}")
        return False

def get_last_activity_timestamp(wallet_identifier: str) -> Optional[str]:
    """
    Retrieves the last recorded activity timestamp for the given wallet.

    The timestamp is read from a JSON file. If the file or timestamp doesn't exist,
    or if there's an error, None is returned.

    Args:
        wallet_identifier (str): The unique identifier for the wallet.

    Returns:
        Optional[str]: The last activity timestamp in ISO 8601 format, 
                       or None if not found or an error occurred.
    """
    if not wallet_identifier:
        print("Error: Wallet identifier is required to get activity timestamp.")
        return None

    filepath = _get_activity_filepath(wallet_identifier)
    print(f"Attempting to load last activity timestamp for wallet '{wallet_identifier}' from: {filepath}")
    
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                activity_data = json.load(f)
            timestamp_str = activity_data.get('last_activity_timestamp')
            
            if timestamp_str:
                # Basic validation of the timestamp format before returning.
                try:
                    datetime.fromisoformat(timestamp_str) # Checks if it's a valid ISO 8601 string
                    print(f"  Successfully loaded timestamp: {timestamp_str}")
                    return timestamp_str
                except ValueError:
                    print(f"  Error: Invalid timestamp format in {filepath}: '{timestamp_str}'")
                    return None # Invalid format, treat as missing
            else:
                print(f"  Timestamp key 'last_activity_timestamp' not found in {filepath}.")
                return None
        else:
            print(f"  No activity log file found at {filepath} for wallet '{wallet_identifier}'.")
            return None # No activity recorded yet
    except IOError as e:
        print(f"  IOError loading activity timestamp from {filepath}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"  Error decoding JSON from {filepath}: {e}. File might be corrupt.")
        return None
    except Exception as e:
        print(f"  An unexpected error occurred while loading activity timestamp: {e}")
        return None

if __name__ == '__main__':
    # Example usage and testing of the activity tracking functions.
    test_wallet_id_act = "my_activity_test_wallet_123"

    print("\n--- Testing update_last_activity_timestamp ---")
    update_success = update_last_activity_timestamp(test_wallet_id_act)
    print(f"Update successful for {test_wallet_id_act}: {update_success}")
    assert update_success

    print("\n--- Testing get_last_activity_timestamp ---")
    loaded_timestamp = get_last_activity_timestamp(test_wallet_id_act)
    if loaded_timestamp:
        print(f"Loaded timestamp for {test_wallet_id_act}: {loaded_timestamp}")
        # Check if it's a valid ISO format string (datetime.fromisoformat would have failed if not)
        assert "T" in loaded_timestamp 
    else:
        print(f"Could not load timestamp for {test_wallet_id_act}.")
        assert False # Should have loaded if update was successful

    # Test getting timestamp for a non-existent wallet
    non_existent_wallet_id_act = "wallet_no_activity_789"
    print(f"\n--- Testing get_last_activity_timestamp for non-existent wallet: {non_existent_wallet_id_act} ---")
    loaded_timestamp_non_existent = get_last_activity_timestamp(non_existent_wallet_id_act)
    if loaded_timestamp_non_existent is None:
        print(f"Timestamp for {non_existent_wallet_id_act} correctly returned None.")
        assert True
    else:
        print(f"Timestamp for {non_existent_wallet_id_act} was {loaded_timestamp_non_existent}, expected None.")
        assert False
        
    print("\nAll activity.py tests finished.")
