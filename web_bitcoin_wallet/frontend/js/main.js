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
    // const feeRateInput = document.getElementById('fee_rate'); // Old direct input, repurposed
    const sendTxBtn = document.getElementById('send_tx_btn');
    const sendStatusMsg = document.getElementById('send_status_msg');
    const feePrioritySelector = document.getElementById('fee_priority_selector');
    const customFeeRateGroup = document.getElementById('custom_fee_rate_group');
    const customFeeRateInput = document.getElementById('custom_fee_rate'); 

    // Transaction History Elements
    const transactionHistoryArea = document.getElementById('transaction_history_area');
    const refreshHistoryBtn = document.getElementById('refresh_history_btn');
    const historyStatusMsg = document.getElementById('history_status_msg');
    const txHistoryTableBody = document.querySelector('#tx_history_table tbody');

    // Inheritance Planning Elements
    const inheritancePlanningArea = document.getElementById('inheritance_planning_area');
    const beneficiaryAddressElem = document.getElementById('beneficiary_address');
    const inactivityPeriodElem = document.getElementById('intended_inactivity_period');
    const beneficiaryMessageElem = document.getElementById('beneficiary_message');
    const saveInheritancePlanBtn = document.getElementById('save_inheritance_plan_btn');
    const inheritancePlanStatusMsg = document.getElementById('inheritance_plan_status_msg');
    const prepareInheritancePackageBtn = document.getElementById('prepare_inheritance_package_btn');
    const inheritancePackageOutputContainer = document.getElementById('inheritance_package_output_container');
    const inheritancePackageOutput = document.getElementById('inheritance_package_output');
    const downloadInheritancePackageBtn = document.getElementById('download_inheritance_package_btn');


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
    const DUST_THRESHOLD_SATS = 546; 
    const P2PKH_INPUT_VBSIZE = 148; 
    const P2PKH_OUTPUT_VBSIZE = 34; 
    const BASE_TX_VBSIZE_OVERHEAD = 10; 

    window.currentFees = {}; 


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
            const path = "m/44'/0'/0'/0/0"; 
            const child = root.derivePath(path);
            const { address } = bitcoin.payments.p2pkh({ pubkey: child.publicKey, network: bitcoinNetwork });

            if (!address) {
                return { error: "Could not derive address from mnemonic." };
            }
            const privateKeyWif = child.toWIF();
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
            [walletInfoArea, sendBitcoinArea, transactionHistoryArea, inheritancePlanningArea].forEach(area => {
                if (area) area.classList.add('hidden');
            });
            return;
        }
        if (importErrorMsg) importErrorMsg.textContent = ''; 

        if (mnemonicDisplay) mnemonicDisplay.textContent = details.mnemonic;
        if (walletAddressDisplay) walletAddressDisplay.textContent = details.address;
        if (walletBalanceDisplay) {
            walletBalanceDisplay.textContent = "Fetching balance...";
            fetch_and_display_balance(details.address);
        }
        
        window.currentWallet = details; 

        [walletInfoArea, sendBitcoinArea, transactionHistoryArea, inheritancePlanningArea].forEach(area => {
            if (area) area.classList.remove('hidden');
        });

        if (qrCodeContainer && typeof QRCode !== 'undefined' && details.address) {
            qrCodeContainer.innerHTML = ""; 
            qrCodeInstance = new QRCode(qrCodeContainer, {
                text: `bitcoin:${details.address}`, width: 128, height: 128,
                colorDark : "#000000", colorLight : "#ffffff", correctLevel : QRCode.CorrectLevel.H
            });
        }
        fetch_and_display_fees(); 
        fetch_and_display_tx_history(details.address);
        load_inheritance_plan(); 
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

    async function fetch_and_display_tx_history(walletAddress) {
        if (!txHistoryTableBody || !historyStatusMsg) { return; }
        historyStatusMsg.textContent = "Loading transaction history...";
        historyStatusMsg.className = 'message';
        txHistoryTableBody.innerHTML = ''; 

        try {
            const response = await fetch(`/api/blockchain/address/${walletAddress}/txs`);
            if (!response.ok) {
                const errData = await response.json().catch(() => ({error: {details: response.statusText}}));
                throw new Error(errData.error.details || `HTTP error! status: ${response.status}`);
            }
            const txs = await response.json();
            if (txs.error) { throw new Error(txs.error.details || txs.error); }
            if (txs.length === 0) {
                historyStatusMsg.textContent = "No transactions found for this address.";
                const row = txHistoryTableBody.insertRow();
                const cell = row.insertCell();
                cell.colSpan = 6; cell.textContent = "No transactions yet."; cell.style.textAlign = "center";
                return;
            }
            txs.forEach(tx => {
                const row = txHistoryTableBody.insertRow();
                row.insertCell().textContent = tx.timestamp ? new Date(tx.timestamp * 1000).toLocaleString() : 'Unconfirmed';
                const typeCell = row.insertCell();
                typeCell.textContent = tx.type.charAt(0).toUpperCase() + tx.type.slice(1);
                typeCell.className = tx.type === 'send' ? 'sent' : 'received';
                const amountCell = row.insertCell();
                amountCell.textContent = `${(tx.net_amount_sats / SATOSHIS_PER_BTC).toFixed(8)}`;
                amountCell.className = tx.type === 'send' ? 'sent' : 'received';
                row.insertCell().textContent = tx.fee_sats;
                row.insertCell().textContent = tx.confirmations > 6 ? "6+" : tx.confirmations.toString();
                const txidCell = row.insertCell();
                const txidLink = document.createElement('a');
                txidLink.href = `https://mempool.space/tx/${tx.txid}`; 
                txidLink.textContent = `${tx.txid.substring(0, 10)}...${tx.txid.substring(tx.txid.length - 10)}`;
                txidLink.target = "_blank"; txidLink.title = tx.txid; 
                txidCell.appendChild(txidLink);
            });
            historyStatusMsg.textContent = "Transaction history updated.";
            historyStatusMsg.classList.add('success');
        } catch (error) {
            console.error('Error fetching transaction history:', error);
            historyStatusMsg.textContent = `Failed to load history: ${error.message}`;
            historyStatusMsg.classList.add('error');
        }
    }
    
    if (refreshHistoryBtn) {
        refreshHistoryBtn.addEventListener('click', () => {
            if (window.currentWallet && window.currentWallet.address) {
                fetch_and_display_tx_history(window.currentWallet.address);
            } else {
                if (historyStatusMsg) {
                     historyStatusMsg.textContent = "Please create or import a wallet first to view history.";
                     historyStatusMsg.className = 'message error';
                }
            }
        });
    }

    if (feePrioritySelector) {
        feePrioritySelector.addEventListener('change', (event) => {
            if (event.target.name === 'fee_priority') {
                customFeeRateGroup.classList.toggle('hidden', event.target.value !== 'custom');
                if (event.target.value === 'custom' && customFeeRateInput) {
                    customFeeRateInput.value = window.currentFees?.halfHourFee || ''; 
                }
            }
        });
    }
    
    function fetch_and_display_fees() { 
        if (!feeInfoDisplay) { return; }
        feeInfoDisplay.textContent = "Fetching fee estimates...";
        fetch('/api/network-fees')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then(fees => {
                if (fees.error) throw new Error(fees.error.details || fees.error);
                window.currentFees = fees; 
                if(document.getElementById('fastestFee_val')) document.getElementById('fastestFee_val').textContent = fees.fastestFee;
                if(document.getElementById('halfHourFee_val')) document.getElementById('halfHourFee_val').textContent = fees.halfHourFee;
                if(document.getElementById('hourFee_val')) document.getElementById('hourFee_val').textContent = fees.hourFee;
                const mediumFeeRadio = document.getElementById('fee_priority_medium');
                if (mediumFeeRadio) mediumFeeRadio.checked = true;
                customFeeRateGroup.classList.add('hidden'); 
                feeInfoDisplay.textContent = "Select a fee priority or enter custom rate:";
            })
            .catch(error => {
                console.error('Error fetching network fees:', error);
                feeInfoDisplay.textContent = `Failed to fetch fees: ${error.message}`;
                window.currentFees = {}; 
            });
    }

    function estimate_tx_vbytes(num_inputs, num_outputs) {
        return (num_inputs * P2PKH_INPUT_VBSIZE) + (num_outputs * P2PKH_OUTPUT_VBSIZE) + BASE_TX_VBSIZE_OVERHEAD;
    }

    function select_coins(utxos, target_amount_sats, fee_rate_sats_per_vb, num_outputs_for_fee_calc = 2) {
        if (!utxos || utxos.length === 0) {
            return { error: "No UTXOs provided for coin selection." };
        }
        let selected_utxos = [];
        let total_selected_value_sats = 0;
        const sorted_utxos_asc = [...utxos].sort((a, b) => a.value - b.value);
        const sorted_utxos_desc = [...utxos].sort((a, b) => b.value - a.value);

        for (const utxo of sorted_utxos_desc) {
            const fee_for_one_input = estimate_tx_vbytes(1, num_outputs_for_fee_calc) * fee_rate_sats_per_vb;
            if (utxo.value >= target_amount_sats + fee_for_one_input) {
                return {
                    selected_utxos: [utxo],
                    total_selected_value_sats: utxo.value,
                    final_estimated_fee_sats: fee_for_one_input 
                };
            }
        }
        for (const utxo of sorted_utxos_asc) {
            selected_utxos.push(utxo);
            total_selected_value_sats += utxo.value;
            const current_estimated_fee = estimate_tx_vbytes(selected_utxos.length, num_outputs_for_fee_calc) * fee_rate_sats_per_vb;
            if (total_selected_value_sats >= target_amount_sats + current_estimated_fee) {
                return {
                    selected_utxos: selected_utxos,
                    total_selected_value_sats: total_selected_value_sats,
                    final_estimated_fee_sats: current_estimated_fee
                };
            }
        }
        return { error: "Insufficient confirmed funds to cover amount and transaction fee." };
    }

    if (sendTxBtn) {
        sendTxBtn.addEventListener('click', async () => {
            sendStatusMsg.textContent = ''; 
            sendStatusMsg.className = 'message'; 
            if (!window.currentWallet || !window.currentWallet.address || !window.currentWallet.keyPair) {
                sendStatusMsg.textContent = "Error: Wallet not loaded or keyPair missing.";
                sendStatusMsg.classList.add('error'); return;
            }

            const recipient_address_trimmed = recipientAddressInput.value.trim();
            // **New Validation Logic Start**
            if (!recipient_address_trimmed) { 
                sendStatusMsg.textContent = "Recipient address cannot be empty."; 
                sendStatusMsg.classList.add('error'); return;
            }
            try {
                bitcoin.address.toOutputScript(recipient_address_trimmed, bitcoin.networks.bitcoin);
                // If valid, clear previous address-specific error, but keep other potential messages
                if (sendStatusMsg.textContent.includes("Invalid Bitcoin address format")) {
                    sendStatusMsg.textContent = ''; // Clear only if it was an address error
                    sendStatusMsg.className = 'message';
                }
            } catch (e) {
                console.error("Address validation error:", e);
                sendStatusMsg.textContent = 'Invalid Bitcoin address format. Please check the address and try again.';
                sendStatusMsg.classList.add('error'); return;
            }
            // **New Validation Logic End**
            
            const amountBTCStr = sendAmountInput.value.trim();
            if (!amountBTCStr) { sendStatusMsg.textContent = "Amount is required."; sendStatusMsg.classList.add('error'); return; }
            let amountSats;
            try {
                const amountBTC = parseFloat(amountBTCStr);
                if (isNaN(amountBTC) || amountBTC <= 0) throw new Error("Amount must be positive and numeric.");
                amountSats = Math.round(amountBTC * SATOSHIS_PER_BTC);
                if (amountSats < DUST_THRESHOLD_SATS) { 
                    throw new Error(`Amount is too small (less than dust threshold of ${DUST_THRESHOLD_SATS} sats).`);
                }
            } catch(e) { sendStatusMsg.textContent = "Invalid amount: " + e.message; sendStatusMsg.classList.add('error'); return; }

            let actual_fee_rate_sats_per_vb;
            const selected_priority_radio = document.querySelector('input[name="fee_priority"]:checked');
            if (!selected_priority_radio) {
                sendStatusMsg.textContent = "Please select a fee priority."; sendStatusMsg.classList.add('error'); return;
            }
            const fee_priority_value = selected_priority_radio.value;

            if (fee_priority_value === 'custom') {
                const customRateStr = customFeeRateInput.value.trim();
                if (!customRateStr) { sendStatusMsg.textContent = "Custom fee rate is required."; sendStatusMsg.classList.add('error'); return; }
                actual_fee_rate_sats_per_vb = parseInt(customRateStr, 10);
                if (isNaN(actual_fee_rate_sats_per_vb) || actual_fee_rate_sats_per_vb <= 0) {
                    sendStatusMsg.textContent = "Invalid custom fee rate."; sendStatusMsg.classList.add('error'); return;
                }
            } else {
                actual_fee_rate_sats_per_vb = window.currentFees ? window.currentFees[fee_priority_value] : null;
                if (!actual_fee_rate_sats_per_vb) {
                    sendStatusMsg.textContent = "Selected fee priority data not available. Try refreshing fees or select custom.";
                    sendStatusMsg.classList.add('error'); return;
                }
            }
            
            sendStatusMsg.textContent = "Processing transaction...";
            sendTxBtn.disabled = true;

            try {
                const utxoResponse = await fetch(`/api/blockchain/address/${window.currentWallet.address}/utxos`);
                if (!utxoResponse.ok) throw new Error(`Failed to fetch UTXOs: ${utxoResponse.statusText} (${utxoResponse.status})`);
                const availableUtxosApi = await utxoResponse.json();
                if (availableUtxosApi.error) throw new Error(`UTXO API Error: ${availableUtxosApi.error.details || availableUtxosApi.error}`);
                const confirmedUtxos = availableUtxosApi.filter(utxo => utxo.confirmed);
                if (confirmedUtxos.length === 0) throw new Error("No confirmed UTXOs available.");
                
                const num_outputs_for_fee_est = 2; 
                const coinSelectionResult = select_coins(confirmedUtxos, amountSats, actual_fee_rate_sats_per_vb, num_outputs_for_fee_est);
                if (coinSelectionResult.error) throw new Error(coinSelectionResult.error);
                
                let { selected_utxos, total_selected_value_sats, final_estimated_fee_sats } = coinSelectionResult;

                const inputsToSignDetails = [];
                for (const utxo of selected_utxos) {
                    const txHexResponse = await fetch(`/api/blockchain/tx/${utxo.txid}/hex`);
                    if (!txHexResponse.ok) {
                        const errText = await txHexResponse.text();
                        throw new Error(`Failed to fetch raw tx hex for ${utxo.txid}: ${errText} (Status: ${txHexResponse.status})`);
                    }
                    const rawTxHex = await txHexResponse.text();
                    if (!rawTxHex || !/^[0-9a-fA-F]+$/.test(rawTxHex) || rawTxHex.length % 2 !== 0) {
                        throw new Error(`Invalid or empty raw tx hex for ${utxo.txid}.`);
                    }
                    inputsToSignDetails.push({ hash: utxo.txid, index: utxo.vout, nonWitnessUtxo: Buffer.from(rawTxHex, 'hex') });
                }
                
                const psbt = new bitcoin.Psbt({ network: bitcoinNetwork });
                inputsToSignDetails.forEach(inputDetail => psbt.addInput(inputDetail));
                
                psbt.addOutput({ address: recipient_address_trimmed, value: amountSats });
                
                const potential_change_sats = total_selected_value_sats - amountSats - final_estimated_fee_sats;
                if (potential_change_sats >= DUST_THRESHOLD_SATS) {
                    psbt.addOutput({ address: window.currentWallet.address, value: potential_change_sats });
                }

                const keyPair = window.currentWallet.keyPair;
                inputsToSignDetails.forEach((_, index) => psbt.signInput(index, keyPair));
                
                psbt.finalizeAllInputs();
                const txHex = psbt.extractTransaction().toHex();

                sendStatusMsg.textContent = "Broadcasting transaction...";
                const broadcastResponse = await fetch('/api/broadcast-tx', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rawTxHex: txHex }),
                });
                const broadcastResult = await broadcastResponse.json();

                if (!broadcastResponse.ok || broadcastResult.error) {
                    throw new Error(`Broadcast failed: ${broadcastResult.error?.details || broadcastResult.error || broadcastResponse.statusText}`);
                }

                sendStatusMsg.textContent = `Transaction broadcasted successfully! TXID: ${broadcastResult.txid}`;
                sendStatusMsg.classList.remove('error'); sendStatusMsg.classList.add('success');
                
                recipientAddressInput.value = ''; sendAmountInput.value = '';
                setTimeout(() => {
                    fetch_and_display_balance(window.currentWallet.address);
                    fetch_and_display_tx_history(window.currentWallet.address);
                }, 2000);

            } catch (error) {
                console.error("Transaction error:", error);
                sendStatusMsg.textContent = `Error: ${error.message}`;
                sendStatusMsg.classList.add('error');
            } finally {
                sendTxBtn.disabled = false;
            }
        });
    }

    // --- Inheritance Planning Logic ---
    const inheritancePlanningArea = document.getElementById('inheritance_planning_area');
    const beneficiaryAddressElem = document.getElementById('beneficiary_address');
    const inactivityPeriodElem = document.getElementById('intended_inactivity_period');
    const beneficiaryMessageElem = document.getElementById('beneficiary_message');
    const saveInheritancePlanBtn = document.getElementById('save_inheritance_plan_btn');
    const inheritancePlanStatusMsg = document.getElementById('inheritance_plan_status_msg');
    const prepareInheritancePackageBtn = document.getElementById('prepare_inheritance_package_btn');
    const inheritancePackageOutputContainer = document.getElementById('inheritance_package_output_container');
    const inheritancePackageOutput = document.getElementById('inheritance_package_output');
    const downloadInheritancePackageBtn = document.getElementById('download_inheritance_package_btn');

    function get_inheritance_plan_storage_key() {
        if (window.currentWallet && window.currentWallet.address) {
            return `inheritance_plan_${window.currentWallet.address}`;
        }
        return null;
    }

    function save_inheritance_plan() {
        if (!window.currentWallet) {
            inheritancePlanStatusMsg.textContent = "Wallet not loaded.";
            inheritancePlanStatusMsg.className = 'message error';
            return;
        }
        const storageKey = get_inheritance_plan_storage_key();
        if (!storageKey) return;

        const plan = {
            beneficiaryAddress: beneficiaryAddressElem.value.trim(),
            inactivityPeriod: inactivityPeriodElem.value.trim(),
            message: beneficiaryMessageElem.value.trim(),
        };

        if (plan.beneficiaryAddress) {
            try {
                bitcoin.address.toOutputScript(plan.beneficiaryAddress, bitcoinNetwork);
            } catch (e) {
                inheritancePlanStatusMsg.textContent = "Invalid beneficiary Bitcoin address.";
                inheritancePlanStatusMsg.className = 'message error';
                return;
            }
        }

        localStorage.setItem(storageKey, JSON.stringify(plan));
        inheritancePlanStatusMsg.textContent = "Inheritance plan saved locally.";
        inheritancePlanStatusMsg.className = 'message success';
    }

    function load_inheritance_plan() {
        if (!window.currentWallet || !inheritancePlanningArea) return; 
        const storageKey = get_inheritance_plan_storage_key();
        if (!storageKey) return;

        const savedPlan = localStorage.getItem(storageKey);
        if (savedPlan) {
            const plan = JSON.parse(savedPlan);
            beneficiaryAddressElem.value = plan.beneficiaryAddress || '';
            inactivityPeriodElem.value = plan.inactivityPeriod || '';
            beneficiaryMessageElem.value = plan.message || '';
        } else { 
            beneficiaryAddressElem.value = '';
            inactivityPeriodElem.value = '';
            beneficiaryMessageElem.value = '';
        }
        // inheritancePlanningArea.classList.remove('hidden'); // Already handled in display_wallet_info
    }
    
    // --- Event Listeners & Initial Calls (Create, Import, Copy, Send, Inheritance) ---
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
    if (saveInheritancePlanBtn) {
        saveInheritancePlanBtn.addEventListener('click', save_inheritance_plan);
    }

    if (prepareInheritancePackageBtn) {
        prepareInheritancePackageBtn.addEventListener('click', () => {
            if (!window.currentWallet || !window.currentWallet.mnemonic) {
                inheritancePackageOutput.textContent = "Wallet not loaded or mnemonic is unavailable.";
                inheritancePackageOutputContainer.classList.remove('hidden');
                return;
            }
            
            const planData = JSON.parse(localStorage.getItem(get_inheritance_plan_storage_key())) || {};
            const packageText = `
    --- BITCOIN WALLET INHERITANCE INFORMATION ---

    Date Prepared: ${new Date().toLocaleString()}

    IMPORTANT: This document contains sensitive information. Store it securely 
    and share it only with your trusted beneficiary through a secure method. 
    This information is intended to help your beneficiary access your Bitcoin
    wallet in the event of your prolonged inactivity or incapacitation.

    Wallet Mnemonic (Recovery Phrase):
    ${window.currentWallet.mnemonic}

    Wallet Primary Address (for reference):
    ${window.currentWallet.address}
    
    Private Key (WIF - Wallet Import Format - VERY SENSITIVE):
    ${window.currentWallet.privateKeyWif} 

    --- Beneficiary Information & Instructions ---

    Intended Beneficiary Bitcoin Address:
    ${planData.beneficiaryAddress || "Not specified"}

    Intended Inactivity Period Before Access:
    ${planData.inactivityPeriod || "Not specified"}

    Your Message & Instructions:
    ${planData.message || "No specific message provided."}

    --- How to Use This Information ---
    1.  Understand Bitcoin: The beneficiary should have a basic understanding of Bitcoin 
        and how to use a Bitcoin wallet. Many online resources are available.
    2.  Import the Wallet: Use the Mnemonic (Recovery Phrase) above to import this wallet 
        into a compatible Bitcoin wallet software (e.g., Electrum, BlueWallet, or this web wallet).
        The Private Key (WIF) can also be used for import in some wallets but is less common for full wallet recovery.
    3.  Access Funds: Once imported, the beneficiary will have control over the funds 
        associated with this wallet.
    4.  Consider Security: Advise the beneficiary to move the funds to their own secure wallet 
        once they have access, especially if this document's security could be compromised.

    --- Disclaimer ---
    This information is provided as-is. The creator of this package is responsible for 
    its accuracy and secure handling. This web wallet provides this tool as a utility 
    and holds no responsibility for the management, security, or distribution of this package.
    It is strongly recommended to consult with legal and financial professionals for 
    comprehensive estate planning.
            `;
            inheritancePackageOutput.textContent = packageText.trim();
            inheritancePackageOutputContainer.classList.remove('hidden');
        });
    }

    if (downloadInheritancePackageBtn) {
        downloadInheritancePackageBtn.addEventListener('click', () => {
            const text = inheritancePackageOutput.textContent;
            let filename = "bitcoin_wallet_inheritance_info.txt";
            if (window.currentWallet && window.currentWallet.address) {
                 filename = `bitcoin_wallet_inheritance_info_${window.currentWallet.address.substring(0,8)}.txt`;
            }
            const element = document.createElement('a');
            element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
            element.setAttribute('download', filename);
            element.style.display = 'none';
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
        });
    }
    
    // Initial UI setup: Hide sections that require a wallet
    if (walletInfoArea) walletInfoArea.classList.add('hidden');
    if (sendBitcoinArea) sendBitcoinArea.classList.add('hidden');
    if (transactionHistoryArea) transactionHistoryArea.classList.add('hidden');
    if (inheritancePlanningArea) inheritancePlanningArea.classList.add('hidden');
    if (customFeeRateGroup) customFeeRateGroup.classList.add('hidden'); 

});
