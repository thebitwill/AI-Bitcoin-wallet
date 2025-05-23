import os
import requests # Added for making HTTP requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Base URL for the Mempool.space API (Mainnet)
# For Testnet, use: https://mempool.space/testnet/api
MEMPOOL_API_URL = "https://mempool.space/api"

# Determine the path to the frontend directory
FRONTEND_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_FOLDER, static_url_path='')
CORS(app) 

# --- Static File Serving ---

@app.route('/')
def serve_index():
    """Serves the main index.html file from the frontend."""
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/<path:filename>')
def serve_frontend_files(filename):
    """Serves other static files (like CSS, JS) from the frontend directory."""
    return send_from_directory(FRONTEND_FOLDER, filename)


# --- API Endpoints ---

@app.route('/api/status', methods=['GET'])
def get_status():
    """Basic API endpoint to check if the backend is running."""
    return jsonify({'status': 'Backend is running!', 'version': '0.1.1'}) # Incremented version

@app.route('/api/network-fees', methods=['GET'])
def get_network_fees():
    """
    Fetches current Bitcoin network fee estimations from Mempool.space API.
    """
    try:
        response = requests.get(f"{MEMPOOL_API_URL}/v1/fees/recommended")
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        fees_data = response.json()
        # We can directly return the data from mempool.space if its structure is suitable,
        # or transform it if needed. For now, returning directly.
        return jsonify(fees_data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching network fees: {e}")
        return jsonify({"error": "Failed to fetch network fees", "details": str(e)}), 500
    except Exception as e:
        print(f"An unexpected error occurred while fetching fees: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@app.route('/api/blockchain/address/<address>/utxos', methods=['GET'])
def get_address_utxos(address: str):
    """
    Fetches Unspent Transaction Outputs (UTXOs) for a given Bitcoin address
    from the Mempool.space API.
    """
    if not address:
        return jsonify({"error": "Address parameter is required"}), 400

    try:
        print(f"Fetching UTXOs for address: {address} from Mempool.space API")
        response = requests.get(f"{MEMPOOL_API_URL}/address/{address}/utxo")
        
        # Mempool.space API returns 400 for invalid address, or an empty list for valid address with no UTXOs.
        # It might return 200 with empty list for address not found or with no UTXOs.
        if response.status_code == 400:
             return jsonify({"error": "Invalid Bitcoin address format or address not found.", "address": address}), 400
        
        response.raise_for_status() # Handles other HTTP errors (e.g., 5xx from API)
        
        utxos_data = response.json()
        
        # Transform data to a consistent format if needed, e.g., add 'confirmed' field based on status
        # Mempool.space UTXO items have a 'status' object with a 'confirmed' boolean.
        # The value is already in satoshis.
        transformed_utxos = [
            {
                "txid": utxo.get("txid"),
                "vout": utxo.get("vout"),
                "value": utxo.get("value"), # This is in satoshis
                "confirmed": utxo.get("status", {}).get("confirmed", False) 
            }
            for utxo in utxos_data
        ]
        return jsonify(transformed_utxos)
        
    except requests.exceptions.HTTPError as e:
        # Specific handling for HTTP errors if needed, e.g. rate limiting (429)
        print(f"HTTP error fetching UTXOs for {address}: {e}. Response: {e.response.text}")
        if e.response.status_code == 404: # Though mempool might return [] for not found
            return jsonify({"error": "Address not found or no UTXOs", "address": address, "details": e.response.text}), 404
        return jsonify({"error": f"API error fetching UTXOs", "address": address, "details": str(e)}), e.response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching UTXOs for {address}: {e}")
        return jsonify({"error": "Network error fetching UTXOs", "address": address, "details": str(e)}), 503 # Service Unavailable
    except Exception as e:
        print(f"An unexpected error occurred while fetching UTXOs for {address}: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

@app.route('/api/broadcast-tx', methods=['POST'])
def broadcast_transaction_endpoint():
    """
    API endpoint to broadcast a raw Bitcoin transaction hex.
    Accepts a JSON payload with "rawTxHex".
    Broadcasts using Mempool.space API.
    """
    if not request.is_json:
        return jsonify({"error": "Invalid request: Content-Type must be application/json"}), 415

    data = request.get_json()
    raw_tx_hex = data.get('rawTxHex')

    if not raw_tx_hex or not isinstance(raw_tx_hex, str):
        return jsonify({"error": "Missing or invalid rawTxHex in request body"}), 400

    # Validate hex format (basic check: only hex characters, even length)
    if not all(c in '0123456789abcdefABCDEF' for c in raw_tx_hex) or len(raw_tx_hex) % 2 != 0:
        return jsonify({"error": "Invalid rawTxHex format"}), 400
    
    try:
        print(f"Broadcasting raw transaction hex (first 60 chars): {raw_tx_hex[:60]}...")
        # Mempool.space API expects the raw transaction hex as plain text in the request body
        headers = {'Content-Type': 'text/plain'}
        response = requests.post(f"{MEMPOOL_API_URL}/tx", data=raw_tx_hex, headers=headers)
        
        # Mempool API returns:
        # - 200 OK with txid string on success
        # - 400 Bad Request with error message string on failure (e.g., "sendrawtransaction RPC error: ...")
        # - Other error codes for server issues etc.
        
        if response.status_code == 200:
            txid = response.text # The body is the txid
            print(f"Transaction successfully broadcasted. TXID: {txid}")
            return jsonify({"txid": txid}), 200
        else:
            error_message = response.text
            print(f"Failed to broadcast transaction. Status: {response.status_code}, Response: {error_message}")
            # Try to parse error if it's JSON, otherwise return as text
            try:
                error_json = response.json()
                return jsonify({"error": "Failed to broadcast transaction", "details": error_json}), response.status_code
            except ValueError: # Not JSON
                return jsonify({"error": "Failed to broadcast transaction", "details": error_message}), response.status_code

    except requests.exceptions.RequestException as e:
        print(f"Network error broadcasting transaction: {e}")
        return jsonify({"error": "Network error broadcasting transaction", "details": str(e)}), 503
    except Exception as e:
        print(f"An unexpected error occurred during transaction broadcast: {e}")
        return jsonify({"error": "An unexpected error occurred during broadcast", "details": str(e)}), 500

@app.route('/api/blockchain/tx/<txid>/hex', methods=['GET'])
def get_transaction_hex(txid: str):
    """
    Fetches the raw transaction hex for a given transaction ID
    from the Mempool.space API.
    Returns the hex as plain text.
    """
    if not txid or not all(c in '0123456789abcdefABCDEF' for c in txid) or len(txid) != 64: # Basic TXID validation
        return jsonify({"error": "Invalid transaction ID format"}), 400
    
    try:
        print(f"Fetching raw transaction hex for TXID: {txid} from Mempool.space API")
        response = requests.get(f"{MEMPOOL_API_URL}/tx/{txid}/hex")
        response.raise_for_status() # Check for HTTP errors
        
        # Return as plain text, as this is usually how raw tx hex is consumed
        return response.text, 200, {'Content-Type': 'text/plain'}
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error fetching tx hex for {txid}: {e}. Response: {e.response.text}")
        # Mempool returns 404 if tx not found, with body "Transaction not found"
        if e.response.status_code == 404:
            return jsonify({"error": "Transaction not found", "txid": txid, "details": e.response.text}), 404
        return jsonify({"error": f"API error fetching tx hex", "txid": txid, "details": str(e)}), e.response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching tx hex for {txid}: {e}")
        return jsonify({"error": "Network error fetching tx hex", "txid": txid, "details": str(e)}), 503
    except Exception as e:
        print(f"An unexpected error occurred while fetching tx hex for {txid}: {e}")
        return jsonify({"error": "An unexpected error occurred while fetching tx hex", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
