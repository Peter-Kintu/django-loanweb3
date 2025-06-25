# mylendingapp_backend/wallet/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from .models import UserWallet
from .serializers import UserWalletSerializer, WalletBalanceSerializer
from web3 import Web3, exceptions as web3_exceptions
import os
from dotenv import load_dotenv

# Import the shared Web3 instance setup from loans.views (or a new common utils file)
# It's better to refactor get_web3_instance into a common utils.py if multiple apps use it.
# For now, let's directly import or re-define if you prefer isolated web3 contexts.
# For simplicity and to avoid circular imports, let's copy the W3 setup here or create a common module.
# RECOMMENDED: Create a mylendingapp_backend/utils/web3_utils.py and put get_web3_instance there.
# For now, I'll put a placeholder for its setup to maintain this file's integrity.

WEB3_PROVIDER_URL = os.environ.get('WEB3_PROVIDER_URL')
WEB3_CHAIN_ID = int(os.environ.get('WEB3_CHAIN_ID', 11155111)) # Default to Sepolia

_w3 = None
def get_web3_instance_wallet(): # Renamed to avoid conflict if you copy it
    global _w3
    if _w3 is None or not _w3.is_connected():
        if not WEB3_PROVIDER_URL:
            print("ERROR: WEB3_PROVIDER_URL not set in environment variables.")
            return None
        try:
            _w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
            if not _w3.is_connected():
                print(f"WARNING: Web3 still not connected to {WEB3_PROVIDER_URL}.")
                _w3 = None
            else:
                print(f"Web3 successfully connected to {WEB3_PROVIDER_URL}.")
        except Exception as e:
            print(f"Failed to connect to Web3 provider at {WEB3_PROVIDER_URL}: {e}")
            _w3 = None
    return _w3

get_web3_instance_wallet() # Initialize web3 for this app

class UserWalletCreateView(generics.CreateAPIView):
    queryset = UserWallet.objects.all()
    serializer_class = UserWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure only one wallet per user
        if hasattr(self.request.user, 'userwallet') and self.request.user.userwallet:
            raise ValidationError({"detail": "User already has a wallet address set. Use update instead."})
        serializer.save(user=self.request.user)
        # Also update the wallet_address directly on the User model
        self.request.user.wallet_address = serializer.instance.address
        self.request.user.save()


class UserWalletRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Get the wallet for the current authenticated user
        obj, created = UserWallet.objects.get_or_create(user=self.request.user)
        return obj

    def perform_update(self, serializer):
        serializer.save()
        # Also update the wallet_address directly on the User model
        self.request.user.wallet_address = serializer.instance.address
        self.request.user.save()


class WalletBalanceView(APIView):
    """
    API endpoint to get the native token (ETH/Matic/etc.) balance of an address.
    Can be used for any address, or the authenticated user's linked wallet.
    """
    permission_classes = [permissions.AllowAny] # Can be public or IsAuthenticated

    def get(self, request, *args, **kwargs):
        wallet_address = request.query_params.get('address')
        if not wallet_address:
            # If no address provided, try to get the authenticated user's wallet
            if request.user.is_authenticated and hasattr(request.user, 'userwallet'):
                wallet_address = request.user.userwallet.address
            else:
                return Response({"detail": "Wallet address is required, or user must be authenticated with a linked wallet."}, status=status.HTTP_400_BAD_REQUEST)

        w3 = get_web3_instance_wallet()
        if not w3:
            return Response({"detail": "Blockchain connection not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            checksum_address = w3.to_checksum_address(wallet_address)
            balance_wei = w3.eth.get_balance(checksum_address)
            balance_ether = w3.from_wei(balance_wei, 'ether')

            serializer = WalletBalanceSerializer(data={
                "wallet_address": checksum_address,
                "balance": str(balance_ether) # Return as string to avoid precision issues
            })
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except web3_exceptions.InvalidAddress as e:
            return Response({"detail": f"Invalid Ethereum address: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny]) # Can be public or IsAuthenticated
def erc20_token_balance(request):
    """
    API endpoint to get ERC-20 token balance for a given wallet and token contract address.
    Requires 'wallet_address' and 'token_contract_address' as query parameters.
    """
    wallet_address = request.query_params.get('wallet_address')
    token_contract_address = request.query_params.get('token_contract_address')

    if not wallet_address or not token_contract_address:
        return Response({"detail": "Both 'wallet_address' and 'token_contract_address' are required query parameters."}, status=status.HTTP_400_BAD_REQUEST)

    w3 = get_web3_instance_wallet()
    if not w3:
        return Response({"detail": "Blockchain connection not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        # Example ERC-20 ABI snippet for balanceOf, decimals, symbol
        # For simplicity, we can use the ERC20_ABI from contract_abis.py
        from mylendingapp_backend.contract_abis import ERC20_ABI # Ensure this is imported correctly

        token_contract = w3.eth.contract(address=w3.to_checksum_address(token_contract_address), abi=ERC20_ABI)
        token_balance_raw = token_contract.functions.balanceOf(w3.to_checksum_address(wallet_address)).call()
        token_decimals = token_contract.functions.decimals().call()
        token_symbol = token_contract.functions.symbol().call()

        token_balance_formatted = token_balance_raw / (10**token_decimals)

        return Response({
            "wallet_address": wallet_address,
            "token_address": token_contract_address,
            "symbol": token_symbol,
            "balance": str(token_balance_formatted) # Return as string for large numbers
        }, status=status.HTTP_200_OK)

    except web3_exceptions.InvalidAddress as e:
        return Response({"detail": f"Invalid wallet or token contract address: {e}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Handle cases where contract might not have decimals/symbol or other issues
        return Response({"detail": f"Error fetching ERC-20 balance: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_transaction_params(request):
    """
    Provides current gas price and sender's nonce for transaction building.
    The sender is the authenticated user's linked wallet.
    """
    w3 = get_web3_instance_wallet()
    if not w3:
        return Response({"error": "Blockchain connection not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        user_wallet = request.user.userwallet
        wallet_address = w3.to_checksum_address(user_wallet.address)

        gas_price_wei = w3.eth.gas_price
        nonce = w3.eth.get_transaction_count(wallet_address)

        return Response({
            "gas_price_wei": str(gas_price_wei),
            "nonce": nonce
        }, status=status.HTTP_200_OK)
    except UserWallet.DoesNotExist:
        return Response({"error": "User does not have a wallet linked."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred while fetching transaction parameters: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def broadcast_signed_transaction(request):
    """
    Receives a raw, signed transaction (hex string) from the client and broadcasts it to the blockchain.
    This allows the client to sign transactions securely without sending private keys to the backend.
    """
    signed_transaction_hex = request.data.get('signed_transaction')
    if not signed_transaction_hex:
        return Response({'error': 'Signed transaction hex is required in the request body.'}, status=status.HTTP_400_BAD_REQUEST)

    w3 = get_web3_instance_wallet()
    if not w3:
        return Response({"error": "Blockchain connection not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        # The hex string might come with or without '0x' prefix
        tx_hash_bytes = bytes.fromhex(signed_transaction_hex.replace('0x', ''))
        receipt = w3.eth.send_raw_transaction(tx_hash_bytes)
        tx_receipt = w3.eth.wait_for_transaction_receipt(receipt, timeout=300) # Increased timeout

        if tx_receipt.status == 1:
            return Response({
                'message': 'Transaction broadcast successfully.',
                'tx_hash': tx_receipt.transactionHash.hex(),
                'receipt_status': tx_receipt.status
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Transaction failed on blockchain.',
                'tx_hash': tx_receipt.transactionHash.hex(),
                'receipt_status': tx_receipt.status
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ValueError as e:
        return Response({'error': f'Invalid signed transaction format or blockchain error: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except web3_exceptions.TransactionNotFound:
         return Response({'error': 'Transaction was not found on the network (might be pending or dropped).'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred during transaction broadcast: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)