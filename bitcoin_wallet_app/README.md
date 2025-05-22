# PyQt Bitcoin Wallet

## Description
PyQt Bitcoin Wallet is a desktop application developed in Python using the PyQt5 GUI framework. It provides functionalities for managing Bitcoin assets, including wallet creation, viewing transaction history, and a unique inheritance planning feature. Currently, the application operates with mock transactions and is intended for demonstration and development purposes.

## Features
*   **Wallet Creation:** Generates new Bitcoin wallets using BIP39 mnemonic phrases and derives addresses using BIP44.
*   **Send/Receive (Mock):** UI components for sending and receiving Bitcoin. Transaction creation and broadcasting are currently mocked.
*   **Transaction History (Mock):** Displays a list of mock transactions for the current wallet.
*   **Inheritance Configuration:** Allows users to configure an inheritance plan, specifying a beneficiary address, an inactivity period, and an amount to be transferred upon prolonged wallet inactivity.
*   **Activity Tracking for Inheritance:** Logs user activity (like sending transactions or saving settings) to facilitate the inheritance feature's inactivity check.
*   **Settings Persistence:** Inheritance settings and activity logs are saved locally (currently in JSON files).

## Setup and Running

### 1. Create a Virtual Environment
It's recommended to use a virtual environment to manage project dependencies.
```bash
python -m venv venv
```

### 2. Activate the Virtual Environment
*   **On Windows:**
    ```bash
    .\venv\Scripts\activate
    ```
*   **On macOS and Linux:**
    ```bash
    source venv/bin/activate
    ```

### 3. Install Dependencies
Install all required packages using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 4. Run the Application
Execute the `main.py` script from the `bitcoin_wallet_app` root directory:
```bash
python app/main.py
```
If you are not in the `bitcoin_wallet_app` root directory, adjust the path accordingly (e.g., `python bitcoin_wallet_app/app/main.py`).

## Disclaimer
**Important:** This application is a development project and is **NOT intended for use with real Bitcoin or on the main Bitcoin network.** All Bitcoin-related operations (sending, receiving, balance checking, history) are currently mocked and do not interact with the actual Bitcoin blockchain. Do not use this wallet with real private keys or for actual financial transactions.

## Project Structure
```
bitcoin_wallet_app/
├── app/
│   ├── __init__.py
│   ├── main.py               # Main application entry point and UI logic
│   ├── wallet_logic/         # Core wallet functionalities
│   │   ├── __init__.py
│   │   ├── activity.py       # Activity tracking for inheritance
│   │   ├── settings.py       # Saving/loading inheritance settings
│   │   ├── transactions.py   # Mock transaction and balance logic
│   │   └── wallet.py         # Wallet creation and key management
│   └── ui/                   # (Currently, UI is in main.py, can be refactored here)
│       └── __init__.py
├── requirements.txt          # Python package dependencies
├── README.md                 # This file
└── wallet_data/              # Directory for storing settings and activity logs (created automatically)
    ├── activity/
    └── settings/
```
