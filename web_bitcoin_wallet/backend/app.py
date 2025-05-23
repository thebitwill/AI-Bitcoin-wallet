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

@app.route('/api/blockchain/address/<address>/txs', methods=['GET'])
def get_address_transactions(address: str):
    """
    Fetches transaction history for a given Bitcoin address from Mempool.space API,
    processes it to determine send/receive relative to the address, and extracts relevant details.
    """
    if not address:
        return jsonify({"error": "Address parameter is required"}), 400

    try:
        print(f"Fetching transaction history for address: {address} from Mempool.space API")
        response = requests.get(f"{MEMPOOL_API_URL}/address/{address}/txs")
        
        if response.status_code == 400: # Mempool API might return 400 for invalid address format
            return jsonify({"error": "Invalid Bitcoin address format provided.", "address": address, "details": response.text}), 400
        response.raise_for_status() # Handles other HTTP errors (e.g., 5xx from API)
        
        raw_txs_data = response.json()
        processed_txs = []

        if not raw_txs_data: # Address exists but has no transactions
            return jsonify(processed_txs) # Return empty list

        # Fetch current block height once for confirmation calculation
        height_response = requests.get(f"{MEMPOOL_API_URL}/blocks/tip/height")
        height_response.raise_for_status()
        current_block_height = height_response.json()

        for tx in raw_txs_data:
            total_vin_for_address = 0
            is_sender = False
            for vin in tx.get("vin", []):
                if vin.get("prevout") and vin["prevout"].get("scriptpubkey_address") == address:
                    total_vin_for_address += vin["prevout"].get("value", 0)
                    is_sender = True # If any input is from our address, it's a send (or part of complex tx)

            total_vout_for_address = 0
            for vout in tx.get("vout", []):
                if vout.get("scriptpubkey_address") == address:
                    total_vout_for_address += vout.get("value", 0)
            
            net_amount_sats = total_vout_for_address - total_vin_for_address
            tx_type = "receive" if net_amount_sats > 0 else ("send" if net_amount_sats < 0 else "self-transfer/complex")
            if net_amount_sats == 0 and is_sender: # If net is 0 but our address was an input, likely a send to self or consolidation
                 tx_type = "send" # Consider it a send for simplicity unless it's purely consolidation with no external output

            confirmations = 0
            block_time = tx.get("status", {}).get("block_time")
            if tx.get("status", {}).get("confirmed"):
                block_height = tx.get("status", {}).get("block_height")
                if block_height:
                    confirmations = current_block_height - block_height + 1
            
            processed_txs.append({
                "txid": tx.get("txid"),
                "type": tx_type,
                "net_amount_sats": net_amount_sats, # Positive for receive, negative for send
                "confirmations": confirmations,
                "timestamp": block_time, # Unix timestamp
                "fee_sats": tx.get("fee", 0)
            })
        
        return jsonify(processed_txs)

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error fetching tx history for {address}: {e}. Response: {e.response.text if e.response else 'N/A'}")
        status_code = e.response.status_code if e.response is not None else 500
        return jsonify({"error": f"API error fetching transaction history", "address": address, "details": str(e)}), status_code
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching tx history for {address}: {e}")
        return jsonify({"error": "Network error fetching transaction history", "address": address, "details": str(e)}), 503
    except Exception as e:
        print(f"An unexpected error occurred while fetching tx history for {address}: {e}")
        return jsonify({"error": "An unexpected error occurred while fetching transaction history", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
