document.addEventListener('DOMContentLoaded', () => {
    // API Status Elements
    const statusMessageElement = document.getElementById('status-message');
    const versionMessageElement = document.getElementById('version-message');

    // Wallet Action Elements
    const createWalletBtn = document.getElementById('create_wallet_btn');
    const importWalletBtn = document.getElementById('import_wallet_btn');
    const mnemonicInput = document.getElementById('mnemonic_input');
    const importErrorMsg = document.getElementById('import_error_msg');

    // Wallet Info Display Elements
    const walletInfoArea = document.getElementById('wallet_info_area');
    const mnemonicDisplay = document.getElementById('mnemonic_display');
    const walletAddressDisplay = document.getElementById('wallet_address');
    const walletBalanceDisplay = document.getElementById('wallet_balance');
    const copyMnemonicBtn = document.getElementById('copy_mnemonic_btn');
    const copyAddressBtn = document.getElementById('copy_address_btn');
    const qrCodeContainer = document.getElementById('qr_code_container');
    let qrCodeInstance = null; 

    // Send Bitcoin Elements
    const sendBitcoinArea = document.getElementById('send_bitcoin_area');
    const recipientAddressInput = document.getElementById('recipient_address');
    const sendAmountInput = document.getElementById('send_amount');
    const feeInfoDisplay = document.getElementById('fee_info');
    const feeRateInput = document.getElementById('fee_rate');
    const sendTxBtn = document.getElementById('send_tx_btn');
    const sendStatusMsg = document.getElementById('send_status_msg');

    // Ensure bitcoinjs-lib and bip39 are loaded
    if (typeof bitcoin === 'undefined' || typeof bip39 === 'undefined') {
        console.error("bitcoinjs-lib or bip39 library not loaded!");
        if(walletInfoArea) walletInfoArea.innerHTML = "<p class='error-message'>Error: Bitcoin libraries not loaded. Wallet functionality is unavailable.</p>";
        if(statusMessageElement) statusMessageElement.textContent = "Library Load Error";
        if(createWalletBtn) createWalletBtn.disabled = true;
        if(importWalletBtn) importWalletBtn.disabled = true;
        if(sendTxBtn) sendTxBtn.disabled = true;
        return; 
    }
    if (typeof QRCode === 'undefined') {
        console.error("QRCode library not loaded!");
        if (qrCodeContainer) qrCodeContainer.innerHTML = "<p class='error-message'>QR Code library error.</p>";
    }
    
    const bitcoinNetwork = bitcoin.networks.bitcoin; // Mainnet
    const SATOSHIS_PER_BTC = 100000000;

    // --- API Status Fetch ---
    if (statusMessageElement && versionMessageElement) {
        const apiUrl = '/api/status'; 
        fetch(apiUrl)
            .then(response => response.ok ? response.json() : Promise.reject(`HTTP error! status: ${response.status}`))
            .then(data => {
                statusMessageElement.textContent = data.status || 'Status N/A';
                versionMessageElement.textContent = data.version || 'Version N/A';
            })
            .catch(error => {
                console.error('Error fetching API status:', error);
                statusMessageElement.textContent = 'Failed to fetch';
                versionMessageElement.textContent = 'N/A';
            });
    }

    // --- Wallet Logic ---
    function derive_wallet_details(mnemonic) {
        try {
            if (!bip39.validateMnemonic(mnemonic)) {
                return { error: "Invalid mnemonic phrase. Please check your words." };
            }
            const seed = bip39.mnemonicToSeedSync(mnemonic);
            const root = bitcoin.bip32.fromSeed(seed, bitcoinNetwork);
            const path = "m/44'/0'/0'/0/0"; // P2PKH path
            const child = root.derivePath(path);
            const { address } = bitcoin.payments.p2pkh({ pubkey: child.publicKey, network: bitcoinNetwork });

            if (!address) {
                return { error: "Could not derive address from mnemonic." };
            }
            const privateKeyWif = child.toWIF();
            // Storing the ECPair object derived from WIF for signing
            const keyPair = bitcoin.ECPair.fromWIF(privateKeyWif, bitcoinNetwork);
            return { mnemonic, address, privateKeyWif, keyPair: keyPair };
        } catch (e) {
            console.error("Error deriving wallet details:", e);
            return { error: e.message || "An unknown error occurred during wallet derivation." };
        }
    }

    function display_wallet_info(details) {
        if (details.error) {
            if (importErrorMsg) importErrorMsg.textContent = details.error;
            if (walletInfoArea) walletInfoArea.classList.add('hidden');
            if (sendBitcoinArea) sendBitcoinArea.classList.add('hidden');
            return;
        }
        if (importErrorMsg) importErrorMsg.textContent = ''; 

        if (mnemonicDisplay) mnemonicDisplay.textContent = details.mnemonic;
        if (walletAddressDisplay) walletAddressDisplay.textContent = details.address;
        if (walletBalanceDisplay) {
            walletBalanceDisplay.textContent = "Fetching balance...";
            fetch_and_display_balance(details.address);
        }
        
        window.currentWallet = details; // Store current wallet globally

        if (walletInfoArea) walletInfoArea.classList.remove('hidden');
        if (sendBitcoinArea) sendBitcoinArea.classList.remove('hidden');

        if (qrCodeContainer && typeof QRCode !== 'undefined' && details.address) {
            qrCodeContainer.innerHTML = ""; 
            qrCodeInstance = new QRCode(qrCodeContainer, {
                text: `bitcoin:${details.address}`, width: 128, height: 128,
                colorDark : "#000000", colorLight : "#ffffff", correctLevel : QRCode.CorrectLevel.H
            });
        }
        fetch_and_display_fees(); 
    }

    async function fetch_and_display_balance(address) {
        if (!walletBalanceDisplay) return;
        try {
            const response = await fetch(`/api/blockchain/address/${address}/utxos`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const utxosApiResponse = await response.json();
            if (utxosApiResponse.error) throw new Error(utxosApiResponse.error.details || utxosApiResponse.error);
            
            const utxos = utxosApiResponse; 
            const totalBalanceSats = utxos.reduce((sum, utxo) => sum + utxo.value, 0);
            const totalBalanceBTC = totalBalanceSats / SATOSHIS_PER_BTC;
            walletBalanceDisplay.textContent = `${totalBalanceBTC.toFixed(8)} BTC`;
        } catch (error) {
            console.error('Error fetching balance:', error);
            walletBalanceDisplay.textContent = "Error fetching balance";
        }
    }

    if (createWalletBtn) {
        createWalletBtn.addEventListener('click', () => {
            const newMnemonic = bip39.generateMnemonic(); 
            const details = derive_wallet_details(newMnemonic);
            display_wallet_info(details);
        });
    }

    if (importWalletBtn) {
        importWalletBtn.addEventListener('click', () => {
            if (!mnemonicInput) {
                if(importErrorMsg) importErrorMsg.textContent = "Mnemonic input field not found.";
                return;
            }
            const mnemonic = mnemonicInput.value.trim();
            if (!mnemonic) {
                if(importErrorMsg) importErrorMsg.textContent = "Please enter a mnemonic phrase.";
                return;
            }
            const details = derive_wallet_details(mnemonic);
            display_wallet_info(details);
        });
    }

    async function copyToClipboard(textToCopy, buttonElement, originalText) {
        if (!navigator.clipboard) {
            alert("Clipboard API not available. Please copy manually.");
            return;
        }
        try {
            await navigator.clipboard.writeText(textToCopy);
            if (buttonElement) {
                buttonElement.textContent = 'Copied!';
                setTimeout(() => { buttonElement.textContent = originalText; }, 2000);
            }
        } catch (err) {
            console.error('Failed to copy: ', err);
            alert("Failed to copy text. Please try again or copy manually.");
        }
    }

    if (copyMnemonicBtn && mnemonicDisplay) { 
        copyMnemonicBtn.addEventListener('click', () => {
            copyToClipboard(mnemonicDisplay.textContent, copyMnemonicBtn, "Copy");
        });
    }
    if (copyAddressBtn && walletAddressDisplay) { 
        copyAddressBtn.addEventListener('click', () => {
            copyToClipboard(walletAddressDisplay.textContent, copyAddressBtn, "Copy");
        });
    }

    function fetch_and_display_fees() {
        if (!feeInfoDisplay || !feeRateInput) { return; }
        feeInfoDisplay.textContent = "Fetching fee estimates...";
        fetch('/api/network-fees')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(fees => {
                if (fees.error) throw new Error(fees.error.details || fees.error);
                feeInfoDisplay.innerHTML = `Fastest: ${fees.fastestFee} sat/vB<br>Medium (30m): ${fees.halfHourFee} sat/vB<br>Slow (1hr): ${fees.hourFee} sat/vB`;
                feeRateInput.value = fees.halfHourFee || '';
            })
            .catch(error => {
                console.error('Error fetching network fees:', error);
                feeInfoDisplay.textContent = `Failed to fetch fees: ${error.message}`;
                feeRateInput.value = '';
            });
    }

    if (sendTxBtn) {
        sendTxBtn.addEventListener('click', async () => {
            sendStatusMsg.textContent = ''; 
            sendStatusMsg.className = 'message'; // Reset class name
            if (!window.currentWallet || !window.currentWallet.address || !window.currentWallet.keyPair) {
                sendStatusMsg.textContent = "Error: Wallet not loaded or keyPair missing.";
                sendStatusMsg.classList.add('error');
                return;
            }

            const recipient = recipientAddressInput.value.trim();
            const amountBTCStr = sendAmountInput.value.trim();
            const feeRateStr = feeRateInput.value.trim();

            // 1. Validate Inputs
            if (!recipient) { sendStatusMsg.textContent = "Recipient address is required."; sendStatusMsg.classList.add('error'); return; }
            try { bitcoin.address.toOutputScript(recipient, bitcoinNetwork); } 
            catch (e) { sendStatusMsg.textContent = `Invalid recipient address: ${e.message}`; sendStatusMsg.classList.add('error'); return; }

            if (!amountBTCStr) { sendStatusMsg.textContent = "Amount is required."; sendStatusMsg.classList.add('error'); return; }
            let amountSats;
            try {
                const amountBTC = parseFloat(amountBTCStr);
                if (isNaN(amountBTC) || amountBTC <= 0) throw new Error("Amount must be positive.");
                amountSats = Math.round(amountBTC * SATOSHIS_PER_BTC);
            } catch(e) { sendStatusMsg.textContent = "Invalid amount: " + e.message; sendStatusMsg.classList.add('error'); return; }


            if (!feeRateStr) { sendStatusMsg.textContent = "Fee rate is required."; sendStatusMsg.classList.add('error'); return; }
            const feeRate = parseInt(feeRateStr, 10);
            if (isNaN(feeRate) || feeRate <= 0) { sendStatusMsg.textContent = "Invalid fee rate. Must be a positive integer."; sendStatusMsg.classList.add('error'); return; }

            sendStatusMsg.textContent = "Processing transaction...";
            sendTxBtn.disabled = true;

            try {
                // 2. Fetch UTXOs
                const utxoResponse = await fetch(`/api/blockchain/address/${window.currentWallet.address}/utxos`);
                if (!utxoResponse.ok) throw new Error(`Failed to fetch UTXOs: ${utxoResponse.statusText} (${utxoResponse.status})`);
                const availableUtxosApi = await utxoResponse.json();
                if (availableUtxosApi.error) throw new Error(`UTXO API Error: ${availableUtxosApi.error.details || availableUtxosApi.error}`);
                
                const confirmedUtxos = availableUtxosApi.filter(utxo => utxo.confirmed);
                if (confirmedUtxos.length === 0) throw new Error("No confirmed UTXOs available to spend.");

                // 3. Coin Selection & Fee Calculation (Simplified)
                const psbt = new bitcoin.Psbt({ network: bitcoinNetwork });
                let totalInputSats = 0;
                const inputsToSignDetails = []; 
                
                // Fetch raw hex for each UTXO to be used (for nonWitnessUtxo as we are using P2PKH)
                for (const utxo of confirmedUtxos) {
                    const txHexResponse = await fetch(`/api/blockchain/tx/${utxo.txid}/hex`);
                    if (!txHexResponse.ok) {
                        const errText = await txHexResponse.text(); // Get error text from plain text response
                        throw new Error(`Failed to fetch raw tx hex for ${utxo.txid}: ${errText} (Status: ${txHexResponse.status})`);
                    }
                    const rawTxHex = await txHexResponse.text();
                     // Basic validation for hex string
                    if (!rawTxHex || !/^[0-9a-fA-F]+$/.test(rawTxHex) || rawTxHex.length % 2 !== 0) {
                         throw new Error(`Invalid or empty raw tx hex for ${utxo.txid}. Received: ${rawTxHex.substring(0,100)}...`);
                    }
                    
                    inputsToSignDetails.push({ 
                        hash: utxo.txid,
                        index: utxo.vout,
                        value: utxo.value, // value in satoshis
                        nonWitnessUtxo: Buffer.from(rawTxHex, 'hex'),
                    });
                    totalInputSats += utxo.value;
                    // Naive coin selection: add inputs until amount is covered (fee not yet considered here)
                    // A more robust fee estimation would happen *before* selecting all inputs, or iteratively.
                    if (totalInputSats >= amountSats) break; 
                }
                
                if (totalInputSats < amountSats) throw new Error("Insufficient funds to cover amount (before fees).");

                // Estimate fee (P2PKH: ~148 bytes/input, ~34 bytes/output, +10 bytes overhead)
                // This is a very rough estimation.
                const numInputs = inputsToSignDetails.length;
                const numOutputs = 2; // One for recipient, one for potential change
                const estimatedTxVBytes = (numInputs * 148) + (numOutputs * 34) + 10; 
                const estimatedFeeSats = estimatedTxVBytes * feeRate;

                if (totalInputSats < amountSats + estimatedFeeSats) {
                    throw new Error(`Insufficient funds. Need approx. ${((amountSats + estimatedFeeSats) / SATOSHIS_PER_BTC).toFixed(8)} BTC (incl. estimated fee ${estimatedFeeSats} sats), have ${(totalInputSats / SATOSHIS_PER_BTC).toFixed(8)} BTC.`);
                }
                
                // Add inputs to PSBT
                inputsToSignDetails.forEach(inputDetail => {
                    psbt.addInput(inputDetail); // inputDetail already contains nonWitnessUtxo
                });
                
                // Add outputs
                psbt.addOutput({ address: recipient, value: amountSats });
                const DUST_THRESHOLD = 546; // Min value for P2PKH output to be non-dust
                const changeAmountSats = totalInputSats - amountSats - estimatedFeeSats;
                if (changeAmountSats >= DUST_THRESHOLD) {
                    psbt.addOutput({ address: window.currentWallet.address, value: changeAmountSats });
                }
                // If change is dust, it effectively becomes part of the fee (not explicitly added to fee, just not returned).

                // Sign Transaction
                const keyPair = window.currentWallet.keyPair; // ECPair object stored in derive_wallet_details
                inputsToSignDetails.forEach((_, index) => { // Sign each input
                    psbt.signInput(index, keyPair);
                });
                
                // Finalize Transaction
                psbt.finalizeAllInputs(); // Validate all inputs are signed
                const txHex = psbt.extractTransaction().toHex();

                // Broadcast via Backend
                sendStatusMsg.textContent = "Broadcasting transaction...";
                const broadcastResponse = await fetch('/api/broadcast-tx', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rawTxHex: txHex }),
                });
                const broadcastResult = await broadcastResponse.json(); // Expecting JSON from our backend

                if (!broadcastResponse.ok || broadcastResult.error) { // Check our backend's error structure
                    throw new Error(`Broadcast failed: ${broadcastResult.error?.details || broadcastResult.error || broadcastResponse.statusText}`);
                }

                sendStatusMsg.textContent = `Transaction broadcasted successfully! TXID: ${broadcastResult.txid}`;
                sendStatusMsg.classList.remove('error'); sendStatusMsg.classList.add('success');
                
                // Clear form and update balance
                recipientAddressInput.value = ''; 
                sendAmountInput.value = '';
                // Consider not clearing feeRateInput if user wants to make another tx with same rate
                setTimeout(() => fetch_and_display_balance(window.currentWallet.address), 2000); // Delay to allow mempool update

            } catch (error) {
                console.error("Transaction error:", error);
                sendStatusMsg.textContent = `Error: ${error.message}`;
                sendStatusMsg.classList.add('error');
            } finally {
                sendTxBtn.disabled = false; // Re-enable send button
            }
        });
    }
});
