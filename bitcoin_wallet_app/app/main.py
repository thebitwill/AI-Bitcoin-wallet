# main.py
# Main application for the PyQt Bitcoin Wallet.
# This file sets up the GUI, handles user interactions, and integrates with the wallet logic.

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFormLayout, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt
from decimal import Decimal, InvalidOperation # For handling Bitcoin amounts accurately
from datetime import datetime, timezone # For activity tracking and inheritance checks

# Attempt to import wallet logic modules.
# If imports fail, it indicates a setup issue or missing files.
# Dummy functions are defined to allow the UI to run for design/preview purposes,
# but core functionality will be disabled.
try:
    from app.wallet_logic import (generate_mnemonic, create_wallet_from_mnemonic,
                                  get_balance, get_utxos, create_transaction, 
                                  broadcast_transaction, get_transaction_history,
                                  save_inheritance_settings, load_inheritance_settings,
                                  update_last_activity_timestamp, get_last_activity_timestamp)
    wallet_logic_available = True
    current_wallet_info = None # Global variable to store current wallet's details (address, keys)
except ImportError as e:
    wallet_logic_available = False
    print(f"Wallet logic could not be imported. Error: {e}. Ensure it's correctly placed and __init__.py is set up.")
    # Define dummy functions if import fails, allowing UI to load without crashing.
    def generate_mnemonic(): print("Dummy: generate_mnemonic"); return "Import failed - dummy mnemonic"
    def create_wallet_from_mnemonic(m): print(f"Dummy: create_wallet_from_mnemonic({m})"); return {"mnemonic": m, "private_key_wif": "N/A", "address": "N/A", "public_key_hex": "N/A"}
    def get_balance(addr): print(f"Dummy: get_balance({addr})"); return Decimal("0.00")
    def get_utxos(addr): print(f"Dummy: get_utxos({addr})"); return []
    def create_transaction(sa, pk, ra, am, ut, fe): print("Dummy: create_transaction"); return "mock_tx_dummy_import_fail"
    def broadcast_transaction(tx): print(f"Dummy: broadcast_transaction({tx})"); return False
    def get_transaction_history(addr): print(f"Dummy: get_transaction_history({addr})"); return [] 
    def save_inheritance_settings(wallet_id, settings): print(f"Dummy: save_inheritance_settings({wallet_id}, {settings})"); return False
    def load_inheritance_settings(wallet_id): print(f"Dummy: load_inheritance_settings({wallet_id})"); return None
    def update_last_activity_timestamp(wallet_id): print(f"Dummy: update_last_activity_timestamp({wallet_id})"); return False
    def get_last_activity_timestamp(wallet_id): print(f"Dummy: get_last_activity_timestamp({wallet_id})"); return None
    current_wallet_info = create_wallet_from_mnemonic("dummy") # Initialize with dummy data


class MainWindow(QMainWindow):
    """
    Main application window for the Bitcoin wallet.
    Handles UI setup, display of wallet information, and user interactions
    for sending Bitcoin, viewing history, and managing inheritance settings.
    """
    def __init__(self):
        """
        Initializes the MainWindow, sets up the UI layout and components,
        and connects signals to slots for handling user actions.
        """
        super().__init__()
        self.setWindowTitle("PyQt Bitcoin Wallet")
        self.setGeometry(100, 100, 800, 750) 
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) 

        # Global status label at the top
        self.status_label = QLabel("Initializing...") 
        self.status_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.status_label)

        # Initialize wallet data (generates/loads wallet)
        self.initialize_wallet_data() 

        # --- Wallet Overview Section ---
        self._setup_wallet_overview_ui(main_layout)

        # --- Send Bitcoin Section ---
        self._setup_send_bitcoin_ui(main_layout)

        # --- Receive Bitcoin Section ---
        self._setup_receive_bitcoin_ui(main_layout)

        # --- Transaction History Section ---
        self._setup_transaction_history_ui(main_layout)

        # --- Inheritance Setup Section ---
        self._setup_inheritance_ui(main_layout)

        # Initial UI state based on wallet logic availability
        if wallet_logic_available:
            self.status_label.setText("Wallet functions loaded. Address generated.")
            self.handle_refresh_history() # Populate history table
        else:
            self.status_label.setText("Wallet logic import failed. Using dummy data. Check console.")
        
        # Variable to store details of a prepared inheritance transaction
        self.prepared_inheritance_tx_details = None

    def _setup_wallet_overview_ui(self, parent_layout: QVBoxLayout):
        """Sets up the Wallet Overview section of the UI."""
        wallet_overview_group = QGroupBox("Wallet Overview")
        wallet_overview_layout = QFormLayout(wallet_overview_group)
        
        self.address_display_label = QLabel("Your Wallet Address:")
        self.address_display_field = QLineEdit()
        self.address_display_field.setReadOnly(True)
        if current_wallet_info:
            self.address_display_field.setText(current_wallet_info.get('address', 'N/A'))
        wallet_overview_layout.addRow(self.address_display_label, self.address_display_field)
        
        self.balance_label = QLabel("Balance: Fetching...")
        wallet_overview_layout.addRow(self.balance_label)
        
        parent_layout.addWidget(wallet_overview_group)
        self.update_balance_display()

    def _setup_send_bitcoin_ui(self, parent_layout: QVBoxLayout):
        """Sets up the Send Bitcoin section of the UI."""
        send_group = QGroupBox("Send Bitcoin")
        send_layout_outer = QVBoxLayout(send_group)
        send_form_layout = QFormLayout() 

        # Recipient Address
        self.recipient_address_input = QLineEdit()
        self.recipient_address_input.setPlaceholderText("Enter recipient's Bitcoin address")
        self.recipient_address_error_label = QLabel("") # For validation errors
        self.recipient_address_error_label.setStyleSheet("color: red;")
        send_form_layout.addRow("Recipient Address:", self.recipient_address_input)
        send_form_layout.addRow("", self.recipient_address_error_label)
        self.recipient_address_input.textChanged.connect(lambda: self.recipient_address_error_label.setText(""))
        self.recipient_address_input.textChanged.connect(self.update_send_button_state)

        # Amount
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount in BTC (e.g., 0.01)")
        self.amount_error_label = QLabel("")
        self.amount_error_label.setStyleSheet("color: red;")
        send_form_layout.addRow("Amount (BTC):", self.amount_input)
        send_form_layout.addRow("", self.amount_error_label)
        self.amount_input.textChanged.connect(lambda: self.amount_error_label.setText(""))
        self.amount_input.textChanged.connect(self.update_send_button_state)

        # Fee
        self.fee_input = QLineEdit()
        self.fee_input.setPlaceholderText("Enter transaction fee in BTC (e.g., 0.0001)")
        self.fee_error_label = QLabel("")
        self.fee_error_label.setStyleSheet("color: red;")
        send_form_layout.addRow("Fee (BTC):", self.fee_input)
        send_form_layout.addRow("", self.fee_error_label)
        self.fee_input.textChanged.connect(lambda: self.fee_error_label.setText(""))
        self.fee_input.textChanged.connect(self.update_send_button_state)
        
        send_layout_outer.addLayout(send_form_layout)

        self.send_button = QPushButton("Send Bitcoin")
        self.send_button.clicked.connect(self.handle_send_btc)
        send_layout_outer.addWidget(self.send_button)
        parent_layout.addWidget(send_group)
        self.update_send_button_state() # Set initial enabled state

    def _setup_receive_bitcoin_ui(self, parent_layout: QVBoxLayout):
        """Sets up the Receive Bitcoin section of the UI."""
        receive_group_box = QGroupBox("Receive Bitcoin")
        receive_layout = QVBoxLayout(receive_group_box)
        
        self.generate_new_address_button = QPushButton("Generate New Address (Placeholder)")
        self.generate_new_address_button.setToolTip("Functionality to generate additional addresses is not yet implemented.")
        self.generate_new_address_button.clicked.connect(self.handle_generate_new_address)
        receive_layout.addWidget(self.generate_new_address_button)
        
        self.qr_code_label_placeholder = QLabel("QR Code for your address will be displayed here (placeholder).")
        self.qr_code_label_placeholder.setAlignment(Qt.AlignCenter)
        self.qr_code_label_placeholder.setMinimumHeight(150) # Placeholder for QR code
        receive_layout.addWidget(self.qr_code_label_placeholder)
        parent_layout.addWidget(receive_group_box)

    def _setup_transaction_history_ui(self, parent_layout: QVBoxLayout):
        """Sets up the Transaction History section of the UI."""
        history_group_box = QGroupBox("Transaction History")
        history_layout = QVBoxLayout(history_group_box)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Date", "Type", "Amount (BTC)", "Address", "Transaction ID"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Columns stretch to fill width
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers) # Make table read-only
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows) # Select whole rows
        self.history_table.setAlternatingRowColors(True)
        history_layout.addWidget(self.history_table)
        
        self.refresh_history_button = QPushButton("Refresh History")
        self.refresh_history_button.clicked.connect(self.handle_refresh_history)
        history_layout.addWidget(self.refresh_history_button)
        parent_layout.addWidget(history_group_box)

    def _setup_inheritance_ui(self, parent_layout: QVBoxLayout):
        """Sets up the Inheritance Setup section of the UI."""
        inheritance_group_box = QGroupBox("Inheritance Setup")
        inheritance_form_layout = QFormLayout(inheritance_group_box)

        self.enable_inheritance_checkbox = QCheckBox("Enable Inheritance Feature")
        inheritance_form_layout.addRow(self.enable_inheritance_checkbox)

        # Beneficiary Address
        self.beneficiary_address_input = QLineEdit()
        self.beneficiary_address_error_label = QLabel("")
        self.beneficiary_address_error_label.setStyleSheet("color: red;")
        inheritance_form_layout.addRow("Beneficiary Address:", self.beneficiary_address_input)
        inheritance_form_layout.addRow("", self.beneficiary_address_error_label)
        self.beneficiary_address_input.textChanged.connect(lambda: self.beneficiary_address_error_label.setText(""))

        # Inactivity Period
        self.inactivity_period_input = QLineEdit()
        self.inactivity_period_input.setPlaceholderText("e.g., 90, 180, 365")
        self.inactivity_period_error_label = QLabel("")
        self.inactivity_period_error_label.setStyleSheet("color: red;")
        inheritance_form_layout.addRow("Inactivity Period (days):", self.inactivity_period_input)
        inheritance_form_layout.addRow("", self.inactivity_period_error_label)
        self.inactivity_period_input.textChanged.connect(lambda: self.inactivity_period_error_label.setText(""))

        # Amount to Transfer
        self.inheritance_amount_input = QLineEdit()
        self.inheritance_amount_input.setPlaceholderText("e.g., 0.5")
        self.inheritance_amount_error_label = QLabel("")
        self.inheritance_amount_error_label.setStyleSheet("color: red;")
        inheritance_form_layout.addRow("Amount to Transfer (BTC):", self.inheritance_amount_input)
        inheritance_form_layout.addRow("", self.inheritance_amount_error_label)
        self.inheritance_amount_input.textChanged.connect(lambda: self.inheritance_amount_error_label.setText(""))

        self.save_inheritance_button = QPushButton("Save Inheritance Settings")
        self.save_inheritance_button.clicked.connect(self.handle_save_inheritance_settings)
        inheritance_form_layout.addRow(self.save_inheritance_button)

        self.last_activity_label = QLabel("Last Wallet Activity: N/A")
        inheritance_form_layout.addRow(self.last_activity_label)

        self.check_inheritance_button = QPushButton("Check Inheritance Status")
        self.check_inheritance_button.clicked.connect(self.handle_check_inheritance_status)
        inheritance_form_layout.addRow(self.check_inheritance_button)
        
        self.prepare_inheritance_tx_button = QPushButton("Prepare Inheritance Transaction")
        self.prepare_inheritance_tx_button.clicked.connect(self.handle_prepare_inheritance_transaction)
        inheritance_form_layout.addRow(self.prepare_inheritance_tx_button)
        self.prepare_inheritance_tx_button.setVisible(False) # Initially hidden

        self.broadcast_inheritance_tx_button = QPushButton("Broadcast Inheritance Tx")
        self.broadcast_inheritance_tx_button.clicked.connect(self.handle_broadcast_inheritance_tx)
        inheritance_form_layout.addRow(self.broadcast_inheritance_tx_button)
        self.broadcast_inheritance_tx_button.setVisible(False) # Initially hidden
        
        parent_layout.addWidget(inheritance_group_box)

        # Connect checkbox to toggle field enabled state
        self.toggle_inheritance_fields_enabled(False) 
        self.enable_inheritance_checkbox.toggled.connect(self.toggle_inheritance_fields_enabled)
        
    def clear_send_errors(self):
        """Clears error messages in the Send Bitcoin section."""
        self.recipient_address_error_label.setText("")
        self.amount_error_label.setText("")
        self.fee_error_label.setText("")

    def clear_inheritance_errors(self):
        """Clears error messages in the Inheritance Setup section."""
        self.beneficiary_address_error_label.setText("")
        self.inactivity_period_error_label.setText("")
        self.inheritance_amount_error_label.setText("")

    def initialize_wallet_data(self):
        """
        Initializes or loads the wallet data.
        This involves generating a mnemonic and creating wallet details if no existing
        wallet is found, or loading existing wallet information.
        Also loads inheritance settings and updates activity display.
        """
        global current_wallet_info
        self.status_label.setText("Initializing wallet...")
        if wallet_logic_available:
            try:
                # In a real app, we might check for existing saved wallet first.
                # For this mock, we always generate from a fixed mnemonic.
                mnemonic = generate_mnemonic() 
                current_wallet_info = create_wallet_from_mnemonic(mnemonic)
                self.status_label.setText("Wallet initialized successfully. (Mock data)")
                if hasattr(self, 'address_display_field') and self.address_display_field: 
                    self.address_display_field.setText(current_wallet_info.get('address', 'N/A'))
                print(f"Initialized Wallet Address: {current_wallet_info.get('address')}")
                
                self.load_and_apply_inheritance_settings() 
                self.update_last_activity_display() 

            except Exception as e:
                print(f"Error initializing wallet data: {e}")
                self.status_label.setText(f"Error initializing wallet: {e}")
                current_wallet_info = create_wallet_from_mnemonic("error dummy") 
                # Still attempt to load settings/activity for consistent UI state
                self.load_and_apply_inheritance_settings()
                self.update_last_activity_display()
        else:
            self.status_label.setText("Wallet logic not available. Using dummy data.")
            self.load_and_apply_inheritance_settings() 
            self.update_last_activity_display() 

    def update_balance_display(self):
        """
        Updates the balance label with the current wallet's (mock) balance.
        """
        if not wallet_logic_available or not current_wallet_info:
            self.balance_label.setText("Balance: N/A (Wallet logic error)")
            return
        try:
            self.balance_label.setText("Balance: Fetching...")
            address = current_wallet_info.get('address')
            if address:
                balance = get_balance(address) # Mock function call
                self.balance_label.setText(f"Balance: {balance} BTC (Mock)")
            else:
                self.balance_label.setText("Balance: N/A (Address not found)")
        except Exception as e:
            self.balance_label.setText("Balance: Error")
            print(f"Error updating balance display: {e}")

    def toggle_inheritance_fields_enabled(self, enabled: bool):
        """
        Enables or disables input fields in the Inheritance Setup section
        based on the 'Enable Inheritance' checkbox state.

        Args:
            enabled (bool): True to enable fields, False to disable.
        """
        self.beneficiary_address_input.setEnabled(enabled)
        self.inactivity_period_input.setEnabled(enabled)
        self.inheritance_amount_input.setEnabled(enabled)
        self.save_inheritance_button.setEnabled(enabled) 
        # Also toggle labels for better visual feedback
        self.beneficiary_address_label.setEnabled(enabled)
        self.inactivity_period_label.setEnabled(enabled)
        self.inheritance_amount_label.setEnabled(enabled)
        if not enabled:
            self.clear_inheritance_errors() # Clear errors when disabling

    def update_send_button_state(self):
        """
        Enables the 'Send Bitcoin' button only if all required input fields
        (recipient address, amount, fee) are non-empty.
        """
        is_send_enabled = bool(self.recipient_address_input.text().strip() and \
                               self.amount_input.text().strip() and \
                               self.fee_input.text().strip())
        self.send_button.setEnabled(is_send_enabled)

    def handle_send_btc(self):
        """
        Handles the 'Send Bitcoin' button click.
        Validates inputs, calls (mock) transaction creation and broadcasting logic,
        and updates UI accordingly.
        """
        global current_wallet_info
        self.clear_send_errors() # Clear previous error messages

        if not wallet_logic_available or not current_wallet_info:
            self.status_label.setText("Send failed: Wallet logic not available.")
            return

        recipient_address = self.recipient_address_input.text().strip()
        amount_btc_str = self.amount_input.text().strip()
        fee_btc_str = self.fee_input.text().strip()
        
        valid_input = True
        # Validate Recipient Address
        if not recipient_address:
            self.recipient_address_error_label.setText("Recipient address cannot be empty.")
            valid_input = False
        elif not recipient_address.startswith(('1', '3', 'bc1', 'tb1')): # Basic check for mainnet and testnet P2PKH/P2SH/Bech32
             self.recipient_address_error_label.setText("Invalid Bitcoin address format.")
             valid_input = False

        # Validate Amount
        try:
            amount_btc = Decimal(amount_btc_str)
            if amount_btc <= 0:
                self.amount_error_label.setText("Amount must be positive.")
                valid_input = False
        except InvalidOperation: # More specific exception for Decimal
            self.amount_error_label.setText("Invalid amount format.")
            valid_input = False

        # Validate Fee
        try:
            fee_btc = Decimal(fee_btc_str)
            if fee_btc <= 0: 
                self.fee_error_label.setText("Fee must be positive.")
                valid_input = False
        except InvalidOperation:
            self.fee_error_label.setText("Invalid fee format.")
            valid_input = False
            
        if not valid_input:
            self.status_label.setText("Send failed: Please check input field errors.")
            return

        self.status_label.setText(f"Preparing to send {amount_btc_str} BTC...")
        sender_address = current_wallet_info.get('address')
        private_key_wif = current_wallet_info.get('private_key_wif')

        if not sender_address or not private_key_wif:
            self.status_label.setText("Send failed: Wallet information (address/private key) missing.")
            return

        try:
            utxos = get_utxos(sender_address) # Mock UTXOs
            if not utxos: 
                self.status_label.setText("No UTXOs available to spend (mock response).")
                return

            # Call mock transaction creation
            raw_tx_hex_or_id = create_transaction(
                sender_address=sender_address, private_key_wif=private_key_wif,
                recipient_address=recipient_address, amount_btc=amount_btc,
                utxos=utxos, fee_btc=fee_btc
            )
            
            if "mock_tx_id" in raw_tx_hex_or_id: # Check if it's a mock ID (as per current mock)
                self.status_label.setText(f"Transaction created (mock): {raw_tx_hex_or_id[:20]}...")
                
                # Call mock broadcast
                broadcast_success = broadcast_transaction(raw_tx_hex_or_id)
                if broadcast_success:
                    self.status_label.setText(f"Sent {amount_btc_str} BTC to {recipient_address[:10]}... (Mock Broadcast Success)")
                    # Clear input fields after successful send
                    self.recipient_address_input.clear()
                    self.amount_input.clear()
                    self.fee_input.clear()
                    
                    self.update_balance_display() # Refresh balance (will be mock)
                    self.handle_refresh_history() # Refresh history (will be mock)
                    
                    # Update last activity timestamp
                    if current_wallet_info and current_wallet_info.get('address'):
                        wallet_id = current_wallet_info['address']
                        if update_last_activity_timestamp(wallet_id):
                            print(f"Successfully updated last activity for {wallet_id} after send.")
                            self.update_last_activity_display() # Update UI
                        else:
                            print(f"Failed to update last activity for {wallet_id} after send.")
                            # Status label already indicates send success; this is a background failure.
                else:
                    self.status_label.setText("Broadcast failed (mock).")
            else:
                self.status_label.setText("Failed to create transaction (mock).")
        except Exception as e:
            self.status_label.setText(f"Error during send operation: {e}")
            print(f"Error in handle_send_btc: {e}")

    def handle_generate_new_address(self):
        """
        Placeholder for generating a new receive address.
        Currently, HD wallets generate many addresses; this function is a stub.
        """
        print("Generate New Address button clicked (Placeholder).")
        self.status_label.setText("Address generation beyond the first one is not yet implemented.")
        # In a real HD wallet, this would derive a new address (e.g., m/44'/0'/0'/0/1)
        # and update the UI, possibly adding it to a list of receive addresses.
        if current_wallet_info:
            self.address_display_field.setText(current_wallet_info.get('address', 'N/A') + " (No new address generated)")

    def handle_refresh_history(self):
        """
        Handles the 'Refresh History' button click.
        Clears the transaction history table and repopulates it with (mock) data.
        """
        self.history_table.setRowCount(0) # Clear existing rows
        if not wallet_logic_available or not current_wallet_info:
            self.status_label.setText("Cannot refresh history: Wallet logic or info missing.")
            return

        current_address = current_wallet_info.get('address')
        if not current_address:
            self.status_label.setText("Cannot refresh history: Current address not available.")
            return
        
        self.status_label.setText(f"Refreshing transaction history for {current_address[:10]}...")
        try:
            transactions = get_transaction_history(current_address) # Mock function call
            if not transactions:
                # Display a message in the table if no transactions are found
                self.history_table.setRowCount(1)
                no_tx_item = QTableWidgetItem("No transactions found for this address (mock).")
                no_tx_item.setTextAlignment(Qt.AlignCenter)
                self.history_table.setItem(0, 0, no_tx_item)
                if self.history_table.columnCount() > 1: # Span across all columns
                    self.history_table.setSpan(0,0, 1, self.history_table.columnCount())
                self.status_label.setText("No transactions found (mock).")
                return

            self.history_table.setRowCount(len(transactions))
            for row, tx in enumerate(transactions):
                # Populate table rows with transaction data
                self.history_table.setItem(row, 0, QTableWidgetItem(tx.get('date', 'N/A')))
                self.history_table.setItem(row, 1, QTableWidgetItem(tx.get('type', 'N/A')))
                self.history_table.setItem(row, 2, QTableWidgetItem(str(tx.get('amount', 'N/A'))))
                self.history_table.setItem(row, 3, QTableWidgetItem(tx.get('address', 'N/A'))) 
                self.history_table.setItem(row, 4, QTableWidgetItem(tx.get('tx_id', 'N/A')))
            self.status_label.setText(f"Transaction history refreshed ({len(transactions)} items - mock).")
        except Exception as e:
            print(f"Error refreshing transaction history: {e}")
            self.status_label.setText(f"Error refreshing history: {e}")

    def update_last_activity_display(self):
        """
        Updates the 'Last Wallet Activity' label with the timestamp from storage.
        Formats the ISO timestamp to a more readable local time format.
        """
        global current_wallet_info
        if not wallet_logic_available or not current_wallet_info or not hasattr(self, 'last_activity_label'):
            if hasattr(self, 'last_activity_label'): # Check if UI element exists
                self.last_activity_label.setText("Last Wallet Activity: Error (logic/wallet info missing)")
            return

        wallet_id = current_wallet_info.get('address')
        if not wallet_id:
            self.last_activity_label.setText("Last Wallet Activity: N/A (Wallet ID missing)")
            return
        
        try:
            timestamp_str = get_last_activity_timestamp(wallet_id)
            if timestamp_str:
                try:
                    # Parse ISO format string from storage
                    dt_object = datetime.fromisoformat(timestamp_str)
                    # Ensure it's timezone-aware (timestamps are stored as UTC)
                    if dt_object.tzinfo is None:
                         dt_object = dt_object.replace(tzinfo=timezone.utc)
                    # Convert to system's local timezone for display
                    local_dt = dt_object.astimezone(None) 
                    display_ts = local_dt.strftime("%Y-%m-%d %H:%M:%S %Z") # Example format
                    self.last_activity_label.setText(f"Last Wallet Activity: {display_ts}")
                except ValueError: # Handle cases where timestamp string is malformed
                    self.last_activity_label.setText(f"Last Wallet Activity: {timestamp_str} (raw/invalid format)")
            else:
                self.last_activity_label.setText("Last Wallet Activity: No activity recorded.")
        except Exception as e:
            self.last_activity_label.setText("Last Wallet Activity: Error fetching timestamp.")
            print(f"Error updating last activity display: {e}")

    def handle_save_inheritance_settings(self):
        """
        Handles the 'Save Inheritance Settings' button click.
        Validates inputs and calls logic to save settings.
        """
        global current_wallet_info
        self.clear_inheritance_errors() # Clear previous errors

        if not wallet_logic_available or not current_wallet_info:
            self.status_label.setText("Cannot save settings: Wallet logic or info missing.")
            return

        enabled = self.enable_inheritance_checkbox.isChecked()
        beneficiary_address = self.beneficiary_address_input.text().strip()
        inactivity_period_str = self.inactivity_period_input.text().strip()
        transfer_amount_str = self.inheritance_amount_input.text().strip()
        
        valid_settings = True
        inactivity_period = 90 # Default if not enabled or invalid
        transfer_amount = Decimal("0.0") # Default if not enabled or invalid

        if enabled:
            # Validate Beneficiary Address
            if not beneficiary_address:
                self.beneficiary_address_error_label.setText("Beneficiary address cannot be empty.")
                valid_settings = False
            elif not beneficiary_address.startswith(('1', '3', 'bc1', 'tb1')): 
                 self.beneficiary_address_error_label.setText("Invalid Bitcoin address format.")
                 valid_settings = False

            # Validate Inactivity Period
            try:
                inactivity_period = int(inactivity_period_str)
                if not (30 <= inactivity_period <= 3650): # Example range: 30 days to 10 years
                    self.inactivity_period_error_label.setText("Period must be between 30 and 3650 days.")
                    valid_settings = False
            except ValueError:
                self.inactivity_period_error_label.setText("Inactivity period must be a valid number.")
                valid_settings = False
            
            # Validate Transfer Amount
            try:
                transfer_amount = Decimal(transfer_amount_str)
                if transfer_amount <= Decimal("0.0"): # Allow 0 if they want to disable amount but keep settings
                    self.inheritance_amount_error_label.setText("Amount must be positive if transferring.")
                    # This might be a warning rather than a hard error if 0 is allowed to "disable" transfer
                    # For now, let's assume positive is required if enabled.
                    if transfer_amount < Decimal("0.0"): valid_settings = False 
            except InvalidOperation:
                self.inheritance_amount_error_label.setText("Invalid transfer amount format.")
                valid_settings = False
            
            if not valid_settings:
                self.status_label.setText("Save failed: Please check inheritance input field errors.")
                return
        else: 
            # If not enabled, we still save the state, potentially clearing sensitive fields
            # or using last valid/default values.
            beneficiary_address = "" # Clear beneficiary if feature is disabled
            # Keep potentially last set values for period/amount or set to default
            try:
                inactivity_period = int(inactivity_period_str) if inactivity_period_str else 90
            except ValueError:
                inactivity_period = 90 # Default if invalid
            try:
                transfer_amount = Decimal(transfer_amount_str) if transfer_amount_str else Decimal("0.0")
            except InvalidOperation:
                transfer_amount = Decimal("0.0")


        settings_to_save = {
            'enabled': enabled,
            'beneficiary_address': beneficiary_address,
            'inactivity_period': inactivity_period,
            'transfer_amount': str(transfer_amount) # Store as string for consistency
        }
        
        wallet_id = current_wallet_info.get('address') 
        if not wallet_id:
            self.status_label.setText("Cannot save settings: Wallet identifier (address) is missing.")
            return

        try:
            from app.wallet_logic import save_inheritance_settings # Import here to ensure latest version if reloaded
            if save_inheritance_settings(wallet_id, settings_to_save):
                self.status_label.setText("Inheritance settings saved (mock).")
                # Saving settings is considered an activity
                if update_last_activity_timestamp(wallet_id):
                    print(f"Updated last activity for {wallet_id} after saving inheritance settings.")
                    self.update_last_activity_display()
                else:
                    print(f"Failed to update activity for {wallet_id} after saving inheritance settings.")
            else:
                self.status_label.setText("Failed to save inheritance settings (mock backend failure).")
        except ImportError:
             self.status_label.setText("Critical Error: save_inheritance_settings function not found.")
        except Exception as e:
            self.status_label.setText(f"Error saving inheritance settings: {e}")
            print(f"Error in handle_save_inheritance_settings: {e}")

    def load_and_apply_inheritance_settings(self):
        """
        Loads inheritance settings for the current wallet and updates the UI fields.
        Called on startup and potentially when wallet changes.
        """
        global current_wallet_info
        # Ensure UI elements exist before trying to access them.
        if not all(hasattr(self, attr_name) for attr_name in [
            'enable_inheritance_checkbox', 'beneficiary_address_input', 
            'inactivity_period_input', 'inheritance_amount_input', 'status_label'
        ]):
            print("Warning: Inheritance UI elements not fully initialized. Skipping load/apply settings.")
            return

        if not wallet_logic_available or not current_wallet_info:
            self.toggle_inheritance_fields_enabled(False) 
            self.enable_inheritance_checkbox.setChecked(False)
            self.status_label.setText("Cannot load inheritance settings: Wallet logic or info missing.")
            return
            
        wallet_id = current_wallet_info.get('address')
        if not wallet_id:
            self.toggle_inheritance_fields_enabled(False)
            self.enable_inheritance_checkbox.setChecked(False)
            self.status_label.setText("Cannot load settings: Wallet identifier missing.")
            return
            
        try:
            from app.wallet_logic import load_inheritance_settings # Import here for safety
            settings = load_inheritance_settings(wallet_id) # This is a mock load
            
            if settings:
                is_enabled = settings.get('enabled', False)
                self.enable_inheritance_checkbox.setChecked(is_enabled)
                self.beneficiary_address_input.setText(settings.get('beneficiary_address', ''))
                self.inactivity_period_input.setText(str(settings.get('inactivity_period', 90)))
                self.inheritance_amount_input.setText(str(settings.get('transfer_amount', '0.0')))
                
                self.toggle_inheritance_fields_enabled(is_enabled)
                self.status_label.setText("Inheritance settings loaded (mock)." if is_enabled else "Inheritance feature disabled (settings loaded).")
            else: # Handles case where load_inheritance_settings might return None on error
                self.enable_inheritance_checkbox.setChecked(False)
                self.toggle_inheritance_fields_enabled(False)
                self.beneficiary_address_input.clear()
                self.inactivity_period_input.setText("90") 
                self.inheritance_amount_input.clear()
                self.status_label.setText("No inheritance settings found or error loading. Feature disabled.")
        except ImportError:
             self.status_label.setText("Critical Error: load_inheritance_settings function not found.")
             self.toggle_inheritance_fields_enabled(False)
             self.enable_inheritance_checkbox.setChecked(False)
        except Exception as e:
            self.status_label.setText(f"Error loading inheritance settings: {e}")
            print(f"Error in load_and_apply_inheritance_settings: {e}")
            self.toggle_inheritance_fields_enabled(False)
            self.enable_inheritance_checkbox.setChecked(False)

    def handle_check_inheritance_status(self):
        """
        Handles the 'Check Inheritance Status' button click.
        Determines if the wallet is considered inactive based on settings and last activity.
        Updates UI to show/hide buttons for preparing/broadcasting inheritance transaction.
        """
        global current_wallet_info
        self.status_label.setText("Checking inheritance status...")
        # Hide action buttons by default, show them only if conditions are met
        self.prepare_inheritance_tx_button.setVisible(False)
        self.broadcast_inheritance_tx_button.setVisible(False)

        if not wallet_logic_available or not current_wallet_info:
            self.status_label.setText("Cannot check status: Wallet logic or current wallet info missing.")
            return

        wallet_id = current_wallet_info.get('address')
        if not wallet_id:
            self.status_label.setText("Cannot check status: Wallet identifier (address) missing.")
            return
        
        # Checking status is considered an activity
        if update_last_activity_timestamp(wallet_id): 
            print(f"Updated last activity for {wallet_id} due to inheritance status check.")
            self.update_last_activity_display()
        else:
            print(f"Failed to update activity for {wallet_id} during inheritance status check.")
            # Not critical for the check itself, but good to log

        settings = load_inheritance_settings(wallet_id)
        if not settings or not settings.get('enabled'):
            self.status_label.setText("Inheritance feature is not enabled in settings.")
            return

        last_activity_ts_str = get_last_activity_timestamp(wallet_id)
        days_inactive = float('inf') # Assume infinitely inactive if no activity log exists
        
        if last_activity_ts_str:
            try:
                last_activity_dt = datetime.fromisoformat(last_activity_ts_str)
                # Ensure timestamp is timezone-aware (should be UTC from storage)
                if last_activity_dt.tzinfo is None: 
                    last_activity_dt = last_activity_dt.replace(tzinfo=timezone.utc)
                
                now_aware = datetime.now(timezone.utc) # Compare with current UTC time
                days_inactive = (now_aware - last_activity_dt).days
            except ValueError: # Malformed timestamp
                self.status_label.setText("Error parsing last activity timestamp. Cannot accurately determine inactivity.")
                # Proceeding with days_inactive = float('inf') might be one way to handle,
                # or return and ask user to check logs/data. For now, assume max inactivity.
        else: 
             self.status_label.setText("No activity recorded for this wallet. Assuming maximum inactivity for inheritance check.")
        
        inactivity_period_days = settings.get('inactivity_period', 90) # Default if key is missing
        
        print(f"Inheritance Check: Days inactive: {days_inactive}, Required inactivity period: {inactivity_period_days} days.")

        if days_inactive >= inactivity_period_days:
            self.status_label.setText(f"Wallet inactive for {days_inactive} days (threshold: {inactivity_period_days} days). Ready to prepare inheritance transaction.")
            self.prepare_inheritance_tx_button.setVisible(True) # Show prepare button
        else:
            remaining_days = inactivity_period_days - days_inactive
            self.status_label.setText(f"Wallet active. {days_inactive} days since last activity. {remaining_days} more days of inactivity needed for inheritance (threshold: {inactivity_period_days} days).")

    def handle_prepare_inheritance_transaction(self):
        """
        Handles the 'Prepare Inheritance Transaction' button click.
        (Mock) Gathers necessary data and "prepares" a transaction.
        """
        global current_wallet_info
        self.status_label.setText("Preparing inheritance transaction...")
        if not wallet_logic_available or not current_wallet_info:
            self.status_label.setText("Preparation failed: Wallet logic or current wallet info missing.")
            return

        wallet_id = current_wallet_info.get('address')
        private_key_wif = current_wallet_info.get('private_key_wif')
        settings = load_inheritance_settings(wallet_id)

        if not settings or not settings.get('enabled'):
            self.status_label.setText("Preparation failed: Inheritance not enabled or settings missing.")
            return

        beneficiary_address = settings.get('beneficiary_address')
        transfer_amount_str = settings.get('transfer_amount')
        
        if not beneficiary_address or not transfer_amount_str:
            self.status_label.setText("Preparation failed: Beneficiary address or transfer amount missing in settings.")
            return
        try:
            transfer_amount_btc = Decimal(transfer_amount_str)
            if transfer_amount_btc <= Decimal("0.0"): # Should be positive
                 self.status_label.setText("Preparation failed: Transfer amount in settings must be positive.")
                 return
        except InvalidOperation:
            self.status_label.setText("Preparation failed: Invalid transfer amount format in settings.")
            return

        # In a real scenario, fetch actual UTXOs and calculate fee appropriately.
        mock_utxos_for_inheritance = get_utxos(wallet_id) 
        if not mock_utxos_for_inheritance:
             self.status_label.setText("Preparation failed: No UTXOs available to spend (mock).")
             return

        mock_fee_btc = Decimal("0.0001") # Placeholder fee
        
        # MOCK: Store details for the broadcast step.
        # A real implementation would call `create_transaction` and store the raw hex.
        # try:
        #     raw_tx_hex = create_transaction(
        #         sender_address=wallet_id,
        #         private_key_wif=private_key_wif,
        #         recipient_address=beneficiary_address,
        #         amount_btc=transfer_amount_btc,
        #         utxos=mock_utxos_for_inheritance, 
        #         fee_btc=mock_fee_btc
        #     )
        #     # Check if raw_tx_hex is valid before proceeding
        # except Exception as e:
        #     self.status_label.setText(f"Error during inheritance tx creation: {e}")
        #     return

        self.prepared_inheritance_tx_details = {
            "recipient": beneficiary_address,
            "amount_btc": transfer_amount_btc,
            "fee_btc": mock_fee_btc,
            "mock_tx_id_or_hex": f"mock_inheritance_tx_for_{beneficiary_address}_{transfer_amount_btc}" # Placeholder
        }
        
        self.status_label.setText(f"Mock inheritance tx to {beneficiary_address} for {transfer_amount_btc} BTC prepared. Ready to broadcast.")
        self.broadcast_inheritance_tx_button.setVisible(True) # Show broadcast button
        self.prepare_inheritance_tx_button.setVisible(False) # Hide prepare button

    def handle_broadcast_inheritance_tx(self):
        """
        Handles the 'Broadcast Inheritance Tx' button click.
        (Mock) "Broadcasts" the prepared transaction.
        """
        global current_wallet_info
        self.status_label.setText("Broadcasting inheritance transaction...")
        if not hasattr(self, 'prepared_inheritance_tx_details') or not self.prepared_inheritance_tx_details:
            self.status_label.setText("Broadcast failed: No transaction was prepared.")
            return
        
        mock_tx_to_broadcast = self.prepared_inheritance_tx_details.get("mock_tx_id_or_hex")
        if not mock_tx_to_broadcast: # Should not happen if preparation was successful
            self.status_label.setText("Broadcast failed: Prepared transaction data is missing or invalid.")
            return

        if broadcast_transaction(mock_tx_to_broadcast): # This is a mock broadcast call
            self.status_label.setText(f"Inheritance transaction broadcasted (mock): {mock_tx_to_broadcast[:20]}...")
            
            wallet_id = current_wallet_info.get('address')
            if wallet_id: # Update activity log after successful broadcast
                if update_last_activity_timestamp(wallet_id):
                    print(f"Updated last activity for {wallet_id} after broadcasting inheritance tx.")
                    self.update_last_activity_display()
                else:
                    print(f"Failed to update activity for {wallet_id} after inheritance broadcast.")
            
            # Refresh UI elements
            self.update_balance_display() 
            self.handle_refresh_history() 
        else:
            self.status_label.setText("Inheritance transaction broadcast failed (mock backend).")
        
        self.prepared_inheritance_tx_details = None # Clear the prepared transaction
        self.broadcast_inheritance_tx_button.setVisible(False) # Hide after attempt
        # Prepare button remains hidden; user should re-check status if they want to try again.

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # This pre-GUI initialization of current_wallet_info is useful if any
    # functions called during MainWindow.__init__ before self.initialize_wallet_data()
    # depend on it. Otherwise, initialize_wallet_data() handles it.
    if wallet_logic_available and not current_wallet_info: 
        print("Pre-GUI: Initializing current_wallet_info (should be done by MainWindow)...")
        try:
            temp_mnemonic = generate_mnemonic() 
            current_wallet_info = create_wallet_from_mnemonic(temp_mnemonic) 
            print(f"Pre-GUI Wallet Info Check (Address: {current_wallet_info.get('address')})")
        except Exception as e:
            print(f"Error in pre-GUI wallet init: {e}")
            # current_wallet_info might remain None or be a dummy from the global except block

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
