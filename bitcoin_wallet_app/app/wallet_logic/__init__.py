# This file marks the 'wallet_logic' directory as a Python package.

# Expose functions from the wallet module
from .wallet import generate_mnemonic, create_wallet_from_mnemonic

# Expose functions from the transactions module
from .transactions import (create_transaction, broadcast_transaction, 
                           get_balance, get_utxos, get_transaction_history)

# Expose functions from the settings module
from .settings import save_inheritance_settings, load_inheritance_settings

# Expose functions from the activity module
from .activity import update_last_activity_timestamp, get_last_activity_timestamp

__all__ = [
    'generate_mnemonic',
    'create_wallet_from_mnemonic',
    'create_transaction',
    'broadcast_transaction',
    'get_balance',
    'get_utxos',
    'get_transaction_history',
    'save_inheritance_settings',
    'load_inheritance_settings',
    'update_last_activity_timestamp',
    'get_last_activity_timestamp',
]
