# mylendingapp_backend/loans/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.conf import settings
from web3 import Web3, exceptions as web3_exceptions
from eth_account import Account
import os

from .models import Loan
from .serializers import LoanRequestSerializer, LoanListSerializer, LoanApprovalSerializer # Use LoanApprovalSerializer


from mylendingapp.contract_abis import P2P_LOAN_ABI, ERC20_ABI # Ensure this path is correct


WEB3_PROVIDER_URL = os.environ.get('WEB3_PROVIDER_URL')
WEB3_CHAIN_ID = int(os.environ.get('WEB3_CHAIN_ID', 11155111)) # Default to Sepolia
DEPLOYER_PRIVATE_KEY = os.environ.get('DEPLOYER_PRIVATE_KEY') # Private key of your platform's deploying/funding account
P2P_LOAN_BYTECODE = os.environ.get('P2P_LOAN_BYTECODE') # Bytecode for your P2PLoan contract

# IMPORTANT: Replace these with ACTUAL Sepolia Testnet ERC-20 token addresses
# you control or have deployed. These should ideally come from .env too.
LOAN_ASSET_TOKEN_ADDRESS = os.environ.get('LOAN_ASSET_TOKEN_ADDRESS') # e.g., Test DAI, Test USDC
COLLATERAL_ASSET_TOKEN_ADDRESS = os.environ.get('COLLATERAL_ASSET_TOKEN_ADDRESS') # e.g., Test WETH, another stablecoin

_w3 = None # Global Web3 instance

def get_web3_instance():
    global _w3
    if _w3 is None or not _w3.is_connected():
        if not WEB3_PROVIDER_URL:
            print("ERROR: WEB3_PROVIDER_URL not set in environment variables.")
            return None
        try:
            _w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
            # For Sepolia (Proof-of-Stake), geth_poa_middleware is NOT typically needed.
            # If you were on a private/PoA chain (like Ganache), you'd inject it here.
            if not _w3.is_connected(): # Final check after init
                print(f"WARNING: Web3 still not connected to {WEB3_PROVIDER_URL}.")
                _w3 = None # Reset to None if connection truly failed
            else:
                print(f"Web3 successfully connected to {WEB3_PROVIDER_URL}.")
        except Exception as e:
            print(f"Failed to connect to Web3 provider at {WEB3_PROVIDER_URL}: {e}")
            _w3 = None
    return _w3

# Initialize global web3 instance on startup (or on first call)
get_web3_instance()

# --- Helper functions for Blockchain Interaction ---

def _build_and_send_transaction(w3_instance, private_key, transaction_builder):
    """
    Builds, signs, and sends a transaction.
    transaction_builder is a contract function call, e.g., `contract.functions.myFunction(arg1)`.
    """
    if not w3_instance.is_connected():
        raise ConnectionError("Web3 instance is not connected to the blockchain.")

    account = Account.from_key(private_key)
    try:
        nonce = w3_instance.eth.get_transaction_count(account.address)
        gas_price = w3_instance.eth.gas_price

        tx_params = {
            'from': account.address,
            'chainId': WEB3_CHAIN_ID,
            'gasPrice': gas_price,
            'nonce': nonce,
        }

        # Estimate gas and add a buffer (important for complex transactions)
        try:
            gas_estimate = transaction_builder.estimate_gas(tx_params)
            tx_params['gas'] = int(gas_estimate * 1.2) # Add 20% buffer
        except web3_exceptions.ContractLogicError as e:
            # If estimation fails due to contract revert, get the revert reason
            revert_reason = getattr(e, 'args', [''])[0]
            if isinstance(revert_reason, dict) and 'message' in revert_reason:
                revert_reason = revert_reason['message']
            print(f"Contract reverted during gas estimation: {revert_reason}")
            raise ValueError(f"Transaction would revert: {revert_reason}")
        except Exception as e:
            print(f"Error estimating gas: {e}. Using default gas limit if available or falling back to a safe value.")
            tx_params['gas'] = 500000 # Fallback gas limit, adjust as needed based on common transaction costs

        # Finalize and sign the transaction
        transaction_with_options = transaction_builder.build_transaction(tx_params)
        signed_tx = w3_instance.eth.account.sign_transaction(transaction_with_options, private_key)
        tx_hash = w3_instance.eth.send_raw_transaction(signed_tx.rawTransaction)
        # Wait for transaction to be mined and get receipt
        receipt = w3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=300) # Increased timeout
        return receipt

    except web3_exceptions.TransactionNotFound:
        raise ValueError("Transaction was not found on the network (might be pending or dropped).")
    except web3_exceptions.ContractLogicError as e:
        revert_reason = getattr(e, 'args', [''])[0]
        if isinstance(revert_reason, dict) and 'message' in revert_reason:
            revert_reason = revert_reason['message']
        raise ValueError(f"Blockchain contract logic error: {revert_reason}")
    except Exception as e:
        print(f"Unhandled error during transaction: {e}")
        raise ValueError(f"Failed to send blockchain transaction: {str(e)}")


def _get_contract_instance(w3_instance, contract_address, abi):
    """Returns a contract instance given its address and ABI."""
    try:
        return w3_instance.eth.contract(address=w3_instance.to_checksum_address(contract_address), abi=abi)
    except Exception as e:
        print(f"Error getting contract instance for {contract_address}: {e}")
        raise

def _get_erc20_contract(w3_instance, token_address):
    """Returns an ERC-20 contract instance."""
    return _get_contract_instance(w3_instance, token_address, ERC20_ABI)

# --- Django REST Framework Views ---

class LoanRequestView(generics.CreateAPIView):
    queryset = Loan.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LoanRequestSerializer

    def perform_create(self, serializer):
        serializer.save(borrower=self.request.user, status='pending')

class LoanListView(generics.ListAPIView):
    serializer_class = LoanListSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Loan.objects.all().order_by('-created_at')
        else:
            return Loan.objects.filter(borrower=user).order_by('-created_at')

class LoanApprovalView(generics.UpdateAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanApprovalSerializer # Use the specific LoanApprovalSerializer
    permission_classes = (permissions.IsAdminUser,)

    def update(self, request, *args, **kwargs):
        loan = self.get_object()

        if loan.status != 'pending':
            return Response({"detail": "Loan is not in 'pending' status."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate incoming data with the approval serializer
        serializer = self.get_serializer(loan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        w3 = get_web3_instance()
        if not w3:
            return Response({"detail": "Blockchain connection not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not DEPLOYER_PRIVATE_KEY:
            return Response({"detail": "DEPLOYER_PRIVATE_KEY is not set in environment variables."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if not P2P_LOAN_BYTECODE:
            return Response({"detail": "P2P_LOAN_BYTECODE is not set in environment variables."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if not LOAN_ASSET_TOKEN_ADDRESS or not COLLATERAL_ASSET_TOKEN_ADDRESS:
            return Response({"detail": "Loan or Collateral Asset Token Addresses are not set in environment variables."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        try:
            # Get borrower and lender wallet addresses
            borrower_wallet_address = loan.borrower.wallet_address
            # If lender is explicitly set by admin in serializer, use their wallet.
            # Otherwise, the DEPLOYER_ACCOUNT will act as the lender.
            lender_instance = serializer.validated_data.get('lender')
            lender_wallet_address = (
                lender_instance.wallet_address if lender_instance else Account.from_key(DEPLOYER_PRIVATE_KEY).address
            )

            if not borrower_wallet_address:
                return Response({"detail": "Borrower does not have a wallet address set."}, status=status.HTTP_400_BAD_REQUEST)
            if not w3.is_checksum_address(borrower_wallet_address):
                borrower_wallet_address = w3.to_checksum_address(borrower_wallet_address)

            if not w3.is_checksum_address(lender_wallet_address):
                lender_wallet_address = w3.to_checksum_address(lender_wallet_address)

            # Convert Django Decimal amounts to smallest unit (Wei for ETH, or scaled for ERC20s with 18 decimals)
            # Assuming loan.amount and loan.collateral_amount are in 'ether' equivalent units for now.
            # In a real app, you'd handle specific token decimals using ERC20_ABI to query `decimals()`
            loan_amount_wei = w3.to_wei(loan.amount, 'ether')
            # Assuming collateral is 1.5x the loan amount value, or fetch from loan model if you add it.
            # For this example, let's make collateral amount dynamic, perhaps loan.amount * 1.5
            collateral_amount_wei = w3.to_wei(loan.amount * 1.5, 'ether') # Example calculation for collateral

            # Interest rate needs to be scaled as per your contract (e.g., 5% = 500)
            interest_rate_for_contract = int(serializer.validated_data['interest_rate'] * 100) # 0.05 * 100 = 5

            # Loan duration in seconds (Django's duration_months * 30 days * 24 hours * 3600 seconds)
            loan_duration_seconds = loan.duration_months * 30 * 24 * 60 * 60

            # Ensure asset addresses are checksummed
            loan_asset_addr_checksum = w3.to_checksum_address(LOAN_ASSET_TOKEN_ADDRESS)
            collateral_asset_addr_checksum = w3.to_checksum_address(COLLATERAL_ASSET_TOKEN_ADDRESS)

            # Get contract factory (to deploy a new instance)
            P2PLoanContractFactory = w3.eth.contract(abi=P2P_LOAN_ABI, bytecode=P2P_LOAN_BYTECODE)

            # Build the deployment transaction
            deploy_txn_builder = P2PLoanContractFactory.constructor(
                lender_wallet_address,
                borrower_wallet_address,
                loan_amount_wei,
                collateral_amount_wei,
                interest_rate_for_contract,
                loan_duration_seconds,
                loan_asset_addr_checksum,
                collateral_asset_addr_checksum
            )

            # Send the deployment transaction
            tx_receipt = _build_and_send_transaction(w3, DEPLOYER_PRIVATE_KEY, deploy_txn_builder)

            if tx_receipt.status == 1: # Transaction successful
                contract_address = tx_receipt.contractAddress
                print(f"P2PLoan contract deployed at: {contract_address}")

                # Update Django model with contract details
                serializer.save(
                    status='approved', # Loan is now approved and contract deployed
                    approved_by=request.user,
                    approved_date=timezone.now(),
                    contract_address=contract_address,
                    deployment_tx_hash=tx_receipt.transactionHash.hex(),
                    loan_asset_contract_address=LOAN_ASSET_TOKEN_ADDRESS,
                    collateral_asset_contract_address=COLLATERAL_ASSET_TOKEN_ADDRESS
                )
                return Response({
                    "message": "Loan approved and P2PLoan contract deployed successfully.",
                    "loan": LoanListSerializer(loan).data,
                    "contract_address": contract_address,
                    "deployment_tx_hash": tx_receipt.transactionHash.hex()
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Contract deployment failed on blockchain.", "tx_hash": tx_receipt.transactionHash.hex()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ValueError as e:
            return Response({"detail": f"Error in transaction parameters or contract logic: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"detail": f"Blockchain connection error: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            print(f"Error during loan approval/contract deployment: {e}")
            return Response({"detail": f"Failed to approve loan or deploy contract: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProvideCollateralView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        loan = generics.get_object_or_404(Loan, pk=pk, borrower=request.user)
        w3 = get_web3_instance()
        if not w3:
            return Response({"detail": "Blockchain connection not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not loan.contract_address:
            return Response({"detail": "Loan contract address not set. Loan might not be approved yet."}, status=status.HTTP_400_BAD_REQUEST)

        if loan.status != 'approved': # Loan is 'approved' when contract is deployed
            return Response({"detail": f"Loan status is '{loan.status}', must be 'approved' to provide collateral."}, status=status.HTTP_400_BAD_REQUEST)

        # Signed transaction must come from the borrower's Flutter app
        signed_transaction_hex = request.data.get('signed_transaction')
        if not signed_transaction_hex:
            return Response({"detail": "Signed transaction hex is required in the request body."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # The backend just broadcasts the pre-signed transaction
            tx_hash_bytes = bytes.fromhex(signed_transaction_hex.replace('0x', ''))
            receipt = w3.eth.send_raw_transaction(tx_hash_bytes)
            tx_receipt = w3.eth.wait_for_transaction_receipt(receipt, timeout=300)

            if tx_receipt.status == 1:
                # Optionally, fetch contract state to confirm collateralProvided
                p2p_loan_contract = _get_contract_instance(w3, loan.contract_address, P2P_LOAN_ABI)
                collateral_provided_on_chain = p2p_loan_contract.functions.collateralProvided().call()

                if collateral_provided_on_chain:
                    # Update Django status if confirmed on-chain
                    loan.status = 'collateral_provided' # New status, if you want
                    loan.save()
                    message = "Collateral provided successfully and confirmed on-chain."
                else:
                    message = "Collateral transaction sent, but on-chain status not confirmed (might be pending)."

                return Response({
                    "message": message,
                    "tx_hash": tx_receipt.transactionHash.hex(),
                    "loan": LoanListSerializer(loan).data
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Collateral transaction failed on blockchain.", "tx_hash": tx_receipt.transactionHash.hex()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ValueError as e:
            return Response({"detail": f"Invalid signed transaction or blockchain error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"detail": f"Blockchain connection error: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            print(f"Error providing collateral: {e}")
            return Response({"detail": f"Failed to process collateral transaction: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FundLoanView(APIView):
    permission_classes = (permissions.IsAdminUser,) # Only admin/lender can fund

    def post(self, request, pk, *args, **kwargs):
        loan = generics.get_object_or_404(Loan, pk=pk)
        w3 = get_web3_instance()
        if not w3:
            return Response({"detail": "Blockchain connection not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not loan.contract_address:
            return Response({"detail": "Loan contract address not set."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if collateral is provided on-chain before funding (optional but good practice)
        try:
            p2p_loan_contract = _get_contract_instance(w3, loan.contract_address, P2P_LOAN_ABI)
            collateral_provided_on_chain = p2p_loan_contract.functions.collateralProvided().call()
            if not collateral_provided_on_chain:
                return Response({"detail": "Collateral has not been provided on-chain for this loan yet."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Warning: Could not verify collateral status on-chain: {e}")
            # Continue, but log this for debugging.

        if loan.status not in ['approved', 'collateral_provided']: # Allow funding if approved or collateral provided
            return Response({"detail": f"Loan status is '{loan.status}', must be 'approved' or 'collateral_provided' to fund."}, status=status.HTTP_400_BAD_REQUEST)

        if not DEPLOYER_PRIVATE_KEY:
            return Response({"detail": "DEPLOYER_PRIVATE_KEY not configured in .env."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # The backend acts as the sender for the funding transaction
            lender_private_key = DEPLOYER_PRIVATE_KEY # Assuming deployer is the default lender for backend-initiated funding
            lender_account = Account.from_key(lender_private_key)

            p2p_loan_contract = _get_contract_instance(w3, loan.contract_address, P2P_LOAN_ABI)
            loan_asset_contract = _get_erc20_contract(w3, LOAN_ASSET_TOKEN_ADDRESS)

            # Get loan amount from contract (best practice)
            contract_loan_amount_wei = p2p_loan_contract.functions.loanAmount().call()

            # Ensure lender has sufficient allowance for the contract to pull funds
            current_allowance = loan_asset_contract.functions.allowance(
                w3.to_checksum_address(lender_account.address),
                w3.to_checksum_address(loan.contract_address)
            ).call()

            if current_allowance < contract_loan_amount_wei:
                approve_tx_builder = loan_asset_contract.functions.approve(
                    w3.to_checksum_address(loan.contract_address),
                    contract_loan_amount_wei
                )
                approve_receipt = _build_and_send_transaction(w3, lender_private_key, approve_tx_builder)
                if approve_receipt.status != 1:
                    return Response({"detail": "Lender ERC-20 approve transaction failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                print(f"Lender ERC-20 Approve Transaction Hash: {approve_receipt.transactionHash.hex()}")

            # Build transaction to call fundLoan
            fund_loan_tx_builder = p2p_loan_contract.functions.fundLoan()

            tx_receipt = _build_and_send_transaction(w3, lender_private_key, fund_loan_tx_builder)

            if tx_receipt.status == 1:
                # Update loan status in Django after successful blockchain transaction
                loan.status = 'active'
                loan.lender = request.user # Assign the current admin/staff user as Django lender
                loan.disbursement_date = timezone.now()
                # Recalculate end_date based on *actual* disbursement_date from contract or current time
                loan.end_date = loan.disbursement_date + relativedelta(months=loan.duration_months)
                loan.disbursement_tx_hash = tx_receipt.transactionHash.hex()
                loan.save()

                return Response({
                    "message": "Loan funded successfully on blockchain and status updated.",
                    "tx_hash": tx_receipt.transactionHash.hex(),
                    "loan": LoanListSerializer(loan).data
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Loan funding transaction failed on blockchain.", "tx_hash": tx_receipt.transactionHash.hex()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ValueError as e:
            return Response({"detail": f"Transaction error during loan funding: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"detail": f"Blockchain connection error: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            print(f"Error funding loan: {e}")
            return Response({"detail": f"Failed to fund loan: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RepayLoanView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk, *args, **kwargs):
        loan = generics.get_object_or_404(Loan, pk=pk, borrower=request.user)
        w3 = get_web3_instance()
        if not w3:
            return Response({"detail": "Blockchain connection not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not loan.contract_address:
            return Response({"detail": "Loan contract address not set."}, status=status.HTTP_400_BAD_REQUEST)

        if loan.status not in ['active', 'overdue']:
            return Response({"detail": f"Loan status is '{loan.status}', must be 'active' or 'overdue' to repay."}, status=status.HTTP_400_BAD_REQUEST)

        # Signed transaction must come from the borrower's Flutter app
        signed_transaction_hex = request.data.get('signed_transaction')
        if not signed_transaction_hex:
            return Response({"detail": "Signed transaction hex is required in the request body."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tx_hash_bytes = bytes.fromhex(signed_transaction_hex.replace('0x', ''))
            receipt = w3.eth.send_raw_transaction(tx_hash_bytes)
            tx_receipt = w3.eth.wait_for_transaction_receipt(receipt, timeout=300)

            if tx_receipt.status == 1:
                # Optionally, read contract state to get repaid amount
                p2p_loan_contract = _get_contract_instance(w3, loan.contract_address, P2P_LOAN_ABI)
                # You might have a `getRepaidAmount()` or similar function in your contract
                # For now, update based on the Django model's original amount (adjust if partial payments)
                # Ensure you get the correct repaid amount from the contract or a reliable source
                loan.status = 'repaid'
                # For full repayment, `repaid_amount` could be total amount due from contract.
                # Example: total_due_from_contract = p2p_loan_contract.functions.calculateAmountDue().call()
                # loan.repaid_amount = w3.from_wei(total_due_from_contract, 'ether')
                loan.last_repayment_date = timezone.now()
                loan.repayment_tx_hash = tx_receipt.transactionHash.hex()
                loan.save()

                return Response({
                    "message": "Loan repaid successfully and confirmed on-chain.",
                    "tx_hash": tx_receipt.transactionHash.hex(),
                    "loan": LoanListSerializer(loan).data
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Repayment transaction failed on blockchain.", "tx_hash": tx_receipt.transactionHash.hex()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ValueError as e:
            return Response({"detail": f"Invalid signed transaction or blockchain error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"detail": f"Blockchain connection error: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            print(f"Error repaying loan: {e}")
            return Response({"detail": f"Failed to process repayment transaction: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LiquidateCollateralView(APIView):
    permission_classes = (permissions.IsAdminUser,) # Only admin/lender can liquidate

    def post(self, request, pk, *args, **kwargs):
        loan = generics.get_object_or_404(Loan, pk=pk)
        w3 = get_web3_instance()
        if not w3:
            return Response({"detail": "Blockchain connection not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not loan.contract_address:
            return Response({"detail": "Loan contract address not set."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if loan is overdue based on end_date from Django model, or ideally from contract
        # Your smart contract has `loanEndTime`. You could fetch and compare `block.timestamp`.
        try:
            p2p_loan_contract = _get_contract_instance(w3, loan.contract_address, P2P_LOAN_ABI)
            loan_end_time_on_chain = p2p_loan_contract.functions.loanEndTime().call()
            current_block_timestamp = w3.eth.get_block('latest').timestamp

            if current_block_timestamp < loan_end_time_on_chain:
                return Response({"detail": "Loan is not yet overdue on-chain."}, status=status.HTTP_400_BAD_REQUEST)
            if p2p_loan_contract.functions.isRepaid().call():
                return Response({"detail": "Loan is already repaid on-chain."}, status=status.HTTP_400_BAD_REQUEST)
            if p2p_loan_contract.functions.isLiquidated().call():
                return Response({"detail": "Collateral already liquidated on-chain."}, status=status.HTTP_400_BAD_REQUEST)

        except web3_exceptions.ContractLogicError as e:
            return Response({"detail": f"Blockchain contract error while checking loan status: {e.args}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Warning: Could not fully verify loan status on-chain for liquidation: {e}. Proceeding based on Django status.")
            # Fallback to Django status check if on-chain check fails
            if loan.status not in ['active', 'overdue']:
                return Response({"detail": f"Loan status is '{loan.status}', not eligible for liquidation."}, status=status.HTTP_400_BAD_REQUEST)
            if loan.status == 'repaid' or loan.status == 'liquidated':
                return Response({"detail": "Loan is already repaid or liquidated (Django status)."}, status=status.HTTP_400_BAD_REQUEST)
            if loan.end_date and timezone.now() < loan.end_date:
                 return Response({"detail": "Loan is not yet overdue (Django status)."}, status=status.HTTP_400_BAD_REQUEST)

        if not DEPLOYER_PRIVATE_KEY:
            return Response({"detail": "DEPLOYER_PRIVATE_KEY not configured in .env."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # The backend acts as the sender for the liquidation transaction
            lender_private_key = DEPLOYER_PRIVATE_KEY # Assuming deployer is the default lender for backend-initiated liquidation
            lender_account = Account.from_key(lender_private_key)

            p2p_loan_contract = _get_contract_instance(w3, loan.contract_address, P2P_LOAN_ABI)

            # Build transaction to call liquidateCollateral
            liquidate_tx_builder = p2p_loan_contract.functions.liquidateCollateral()

            tx_receipt = _build_and_send_transaction(w3, lender_private_key, liquidate_tx_builder)

            if tx_receipt.status == 1:
                loan.status = 'liquidated'
                loan.liquidation_tx_hash = tx_receipt.transactionHash.hex()
                loan.save()

                return Response({
                    "message": "Collateral liquidated successfully and confirmed on-chain.",
                    "tx_hash": tx_receipt.transactionHash.hex(),
                    "loan": LoanListSerializer(loan).data
                }, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Collateral liquidation transaction failed on blockchain.", "tx_hash": tx_receipt.transactionHash.hex()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ValueError as e:
            return Response({"detail": f"Transaction error during liquidation: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"detail": f"Blockchain connection error: {e}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            print(f"Error liquidating collateral: {e}")
            return Response({"detail": f"Failed to liquidate collateral: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)