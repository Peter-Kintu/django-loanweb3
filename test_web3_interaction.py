import json
import os
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware


# --- CONFIGURATION ---
# 1. Ganache RPC URL (ganache-cli default)

GANACHE_URL = "http://127.0.0.1:8545"

# 2. Deployed P2PLoan Contract Address
# IMPORTANT: REPLACE WITH YOUR ACTUAL DEPLOYED CONTRACT ADDRESS from Hardhat output!
CONTRACT_ADDRESS = "0x91dAa47C42DB41F034C01943F46F7f183e12DE0c" # REPLACE THIS

# 3. Contract ABI (Application Binary Interface)
# IMPORTANT: PASTE THE ENTIRE ABI ARRAY CONTENT HERE
# Get this from blockchain/artifacts/contracts/P2PLoan.sol/P2PLoan.json
CONTRACT_ABI = [
    {
      "inputs": [
        {
          "internalType": "address payable",
          "name": "_lender",
          "type": "address"
        },
        {
          "internalType": "address payable",
          "name": "_borrower",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "_loanAmount",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "_collateralAmount",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "_interestRate",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "_loanDuration",
          "type": "uint256"
        },
        {
          "internalType": "address payable",
          "name": "_loanAssetAddress",
          "type": "address"
        },
        {
          "internalType": "address payable",
          "name": "_collateralAssetAddress",
          "type": "address"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "_lender",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_collateralAmount",
          "type": "uint256"
        }
      ],
      "name": "CollateralLiquidated",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "_borrower",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_collateralAmount",
          "type": "uint256"
        }
      ],
      "name": "CollateralReleased",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "_borrower",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "_lender",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_amount",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_disbursementTime",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_endTime",
          "type": "uint256"
        }
      ],
      "name": "LoanDisbursed",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "_borrower",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_loanAmount",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_collateralAmount",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_duration",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_interestRate",
          "type": "uint256"
        }
      ],
      "name": "LoanRequested",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "_borrower",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_amountPaid",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "_remainingDue",
          "type": "uint256"
        }
      ],
      "name": "RepaymentMade",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "borrower",
      "outputs": [
        {
          "internalType": "address payable",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "calculateAmountDue",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "collateralAmount",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "collateralAssetAddress",
      "outputs": [
        {
          "internalType": "address payable",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "fundLoan",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "interestRate",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "isDisbursed",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "isLiquidated",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "isRepaid",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "lender",
      "outputs": [
        {
          "internalType": "address payable",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "liquidateCollateral",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "loanAmount",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "loanAssetAddress",
      "outputs": [
        {
          "internalType": "address payable",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "loanDuration",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "loanEndTime",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "loanStartTime",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "provideCollateral",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "repayLoan",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "withdrawAccidentalEth",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "stateMutability": "payable",
      "type": "receive"
    }
]

# --- ACCOUNT CONFIGURATION FOR TRANSACTIONS ---
# IMPORTANT: Use the private keys of accounts from your ganache-cli output.
# These should correspond to the accounts used in your Hardhat deployment script for the lender and borrower.
# NEVER HARDCODE PRIVATE KEYS IN PRODUCTION! Use environment variables or secure storage.

# Example: Using account (0) from your ganache-cli output, which funded the deployment.
# You could use lenderAccount's private key from your hardhat deployment logs.
# Replace with YOUR actual Lender's Private Key and Address
LENDER_PRIVATE_KEY = "0xe53196860391c12b123e8df33950d6851ab92af23475f885160531f7835f32ee"
LENDER_ADDRESS = "0x5fe7645dF07dce01C59520BC1efcbe4D23c7c5DA"

# Replace with YOUR actual Borrower's Private Key and Address
BORROWER_PRIVATE_KEY = "0x2fdaff72284f37e31fbb1752c9ce7cfd6555d150b446f7b79b41a30aec1149ba"
BORROWER_ADDRESS = "0x7DCDAd4087Ed4bA4b4b293ACE4B63F773996c65d"


def connect_and_load_contract():
    """
    Establishes connection to the Ganache blockchain and loads the P2PLoan contract.
    Returns the Web3 instance and the contract object, or None if connection fails.
    """
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

    # Add Geth PoA middleware for Ganache (often needed)
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    if not w3.is_connected():
        print(f"Failed to connect to Ganache at {GANACHE_URL}. Make sure ganache-cli is running!")
        return None, None

    print(f"Successfully connected to Ganache at {GANACHE_URL}")
    print(f"Current block number: {w3.eth.block_number}")

    # Load the contract using its address and ABI
    try:
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
        print(f"Successfully loaded P2PLoan contract at address: {CONTRACT_ADDRESS}")
        return w3, contract
    except Exception as e:
        print(f"Error loading contract: {e}")
        return None, None


def get_contract_details(contract):
    """
    Calls various view functions on the P2PLoan contract and prints their values.
    """
    if contract is None:
        return

    print("\n--- Current Contract Details (Read-Only) ---")
    try:
        lender = contract.functions.lender().call()
        borrower = contract.functions.borrower().call()
        loan_amount_wei = contract.functions.loanAmount().call() # Amount in Wei
        collateral_amount_wei = contract.functions.collateralAmount().call() # Amount in Wei
        interest_rate = contract.functions.interestRate().call()
        loan_duration = contract.functions.loanDuration().call()
        is_disbursed = contract.functions.isDisbursed().call()
        is_repaid = contract.functions.isRepaid().call()
        is_liquidated = contract.functions.isLiquidated().call()
        loan_start_time = contract.functions.loanStartTime().call()
        loan_end_time = contract.functions.loanEndTime().call()
        loan_asset_address = contract.functions.loanAssetAddress().call()
        collateral_asset_address = contract.functions.collateralAssetAddress().call()


        # Convert Wei to Ether for human readability where applicable
        loan_amount_eth = Web3.from_wei(loan_amount_wei, 'ether')
        collateral_amount_eth = Web3.from_wei(collateral_amount_wei, 'ether')

        print(f"  Lender: {lender}")
        print(f"  Borrower: {borrower}")
        print(f"  Loan Amount: {loan_amount_eth} ETH")
        print(f"  Collateral Amount: {collateral_amount_eth} ETH")
        print(f"  Interest Rate: {interest_rate / 100}% (assuming 500 = 5% for 5%)")
        print(f"  Loan Duration: {loan_duration} seconds")
        print(f"  Loan Start Time (Unix): {loan_start_time} (0 if not disbursed)")
        print(f"  Loan End Time (Unix): {loan_end_time} (0 if not disbursed)")
        print(f"  Loan Asset Address: {loan_asset_address}")
        print(f"  Collateral Asset Address: {collateral_asset_address}")
        print(f"  Is Disbursed: {is_disbursed}")
        print(f"  Is Repaid: {is_repaid}")
        print(f"  Is Liquidated: {is_liquidated}")

    except Exception as e:
        print(f"Error calling contract view functions: {e}")


def fund_loan(w3, contract, sender_private_key, amount_eth_to_send):
    """
    Sends a transaction to call the 'fundLoan' function on the contract.
    The sender must be the lender.
    """
    sender_account = w3.eth.account.from_key(sender_private_key)
    sender_address = sender_account.address

    print(f"\n--- Funding Loan from: {sender_address} ---")
    print(f"Amount to send: {amount_eth_to_send} ETH")

    try:
        # Get current nonce for the sender account (important for transaction ordering)
        nonce = w3.eth.get_transaction_count(sender_address)

        # Build the transaction to call fundLoan
        # 'value' is used to send Ether along with the function call
        tx = contract.functions.fundLoan().build_transaction({
            'from': sender_address,
            'value': w3.to_wei(amount_eth_to_send, 'ether'),
            'gas': 3000000, # A reasonable gas limit for development, adjust if needed
            'gasPrice': w3.eth.gas_price, # Use current network gas price
            'nonce': nonce,
        })

        # Sign the transaction with the sender's private key
        signed_tx = w3.eth.account.sign_transaction(tx, sender_private_key)

        # Send the signed transaction to the blockchain
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f"Transaction sent! Hash: {tx_hash.hex()}")
        print("Waiting for transaction receipt...")

        # Wait for the transaction to be mined and get the receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Transaction Mined! Block: {tx_receipt.blockNumber}, Status: {tx_receipt.status}")
        if tx_receipt.status == 1:
            print("Loan funded successfully!")
        else:
            print(f"Transaction failed. Tx Hash: {tx_hash.hex()}")
            print(f"Transaction receipt: {tx_receipt}")
    except Exception as e:
        print(f"Error funding loan: {e}")


def provide_collateral(w3, contract, sender_private_key, amount_eth_to_send):
    """
    Sends a transaction to call the 'provideCollateral' function on the contract.
    The sender must be the borrower.
    """
    sender_account = w3.eth.account.from_key(sender_private_key)
    sender_address = sender_account.address

    print(f"\n--- Providing Collateral from: {sender_address} ---")
    print(f"Amount to send: {amount_eth_to_send} ETH")

    try:
        nonce = w3.eth.get_transaction_count(sender_address)

        tx = contract.functions.provideCollateral().build_transaction({
            'from': sender_address,
            'value': w3.to_wei(amount_eth_to_send, 'ether'),
            'gas': 3000000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, sender_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f"Transaction sent! Hash: {tx_hash.hex()}")
        print("Waiting for transaction receipt...")

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Transaction Mined! Block: {tx_receipt.blockNumber}, Status: {tx_receipt.status}")
        if tx_receipt.status == 1:
            print("Collateral provided successfully!")
        else:
            print(f"Transaction failed. Tx Hash: {tx_hash.hex()}")
            print(f"Transaction receipt: {tx_receipt}")
    except Exception as e:
        print(f"Error providing collateral: {e}")


def repay_loan(w3, contract, sender_private_key, amount_eth_to_send):
    """
    Sends a transaction to call the 'repayLoan' function on the contract.
    The sender must be the borrower.
    """
    sender_account = w3.eth.account.from_key(sender_private_key)
    sender_address = sender_account.address

    print(f"\n--- Repaying Loan from: {sender_address} ---")
    print(f"Amount to send: {amount_eth_to_send} ETH (includes interest)")

    try:
        nonce = w3.eth.get_transaction_count(sender_address)

        tx = contract.functions.repayLoan().build_transaction({
            'from': sender_address,
            'value': w3.to_wei(amount_eth_to_send, 'ether'),
            'gas': 3000000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, sender_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f"Transaction sent! Hash: {tx_hash.hex()}")
        print("Waiting for transaction receipt...")

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Transaction Mined! Block: {tx_receipt.blockNumber}, Status: {tx_receipt.status}")
        if tx_receipt.status == 1:
            print("Loan repaid successfully!")
        else:
            print(f"Transaction failed. Tx Hash: {tx_hash.hex()}")
            print(f"Transaction receipt: {tx_receipt}")
    except Exception as e:
        print(f"Error repaying loan: {e}")


def liquidate_collateral(w3, contract, sender_private_key):
    """
    Sends a transaction to call the 'liquidateCollateral' function on the contract.
    The sender must be the lender, and conditions for liquidation must be met.
    (i.e., loan is not repaid and loan duration has passed).
    """
    sender_account = w3.eth.account.from_key(sender_private_key)
    sender_address = sender_account.address

    print(f"\n--- Liquidating Collateral from: {sender_address} ---")

    try:
        nonce = w3.eth.get_transaction_count(sender_address)

        tx = contract.functions.liquidateCollateral().build_transaction({
            'from': sender_address,
            'gas': 3000000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, sender_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f"Transaction sent! Hash: {tx_hash.hex()}")
        print("Waiting for transaction receipt...")

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Transaction Mined! Block: {tx_receipt.blockNumber}, Status: {tx_receipt.status}")
        if tx_receipt.status == 1:
            print("Collateral liquidated successfully!")
        else:
            print(f"Transaction failed. Tx Hash: {tx_hash.hex()}")
            print(f"Transaction receipt: {tx_receipt}")
    except Exception as e:
        print(f"Error liquidating collateral: {e}")


if __name__ == "__main__":
    w3_instance, p2p_loan_contract = connect_and_load_contract()

    if p2p_loan_contract:
        # Initial state of the contract
        get_contract_details(p2p_loan_contract)

        print("\n--- Initiating Loan Flow Simulation ---")
        print("NOTE: You may need to reset your Ganache chain (Ctrl+C, then restart ganache-cli)")
        print("      between full test runs to ensure a clean state for each simulation.")

        # 1. Lender funds the loan
        # This amount MUST match the _loanAmount provided during contract deployment
        loan_amount_to_fund_eth = Web3.from_wei(p2p_loan_contract.functions.loanAmount().call(), 'ether')
        fund_loan(w3_instance, p2p_loan_contract, LENDER_PRIVATE_KEY, loan_amount_to_fund_eth)
        get_contract_details(p2p_loan_contract) # Check state after funding

        # 2. Borrower provides collateral
        # This amount MUST match the _collateralAmount provided during contract deployment
        collateral_amount_to_provide_eth = Web3.from_wei(p2p_loan_contract.functions.collateralAmount().call(), 'ether')
        provide_collateral(w3_instance, p2p_loan_contract, BORROWER_PRIVATE_KEY, collateral_amount_to_provide_eth)
        get_contract_details(p2p_loan_contract) # Check state after providing collateral

        # --- Advanced Loan Flow (Uncomment to test) ---
        # For these steps, you might need to manually advance Ganache's time
        # if your contract has time-based logic (e.g., loan duration, grace periods).
        # You can do this with `ganache-cli --blockTime 1` (for 1 second per block)
        # or by manually calling `evm_increaseTime` and `evm_mine` via RPC.

        # 3. Borrower repays the loan
        # You'd typically call calculateAmountDue() first to get the exact amount including interest.
        # Ensure the repaying amount is sufficient.
        # try:
        #     amount_due_wei = p2p_loan_contract.functions.calculateAmountDue().call()
        #     amount_due_eth = w3_instance.from_wei(amount_due_wei, 'ether')
        #     print(f"\nCalculated amount due: {amount_due_eth} ETH")
        #     repay_loan(w3_instance, p2p_loan_contract, BORROWER_PRIVATE_KEY, amount_due_eth)
        #     get_contract_details(p2p_loan_contract) # Check state after repayment
        # except Exception as e:
        #     print(f"Could not calculate or repay loan (might need to wait for disbursement): {e}")

        # 4. Lender liquidates collateral (only if loan is not repaid AND duration passed)
        # This will likely fail unless you manually advance Ganache's time past loanDuration
        # try:
        #     # Advance Ganache time example (requires ganache-cli, or specific RPC method)
        #     # w3_instance.provider.make_request("evm_increaseTime", [p2p_loan_contract.functions.loanDuration().call() + 100])
        #     # w3_instance.provider.make_request("evm_mine", [])
        #     # print(f"Advanced Ganache time. Current block time: {w3_instance.eth.get_block('latest').timestamp}")

        #     liquidate_collateral(w3_instance, p2p_loan_contract, LENDER_PRIVATE_KEY)
        #     get_contract_details(p2p_loan_contract) # Check state after liquidation
        # except Exception as e:
        #     print(f"Could not liquidate collateral (might need to wait for loan duration to pass): {e}")


        print("\n--- Web3 Interaction Test Script End ---")
        print("Next steps: Integrate this logic into your Django views or services.")