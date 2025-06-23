# users/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserRegisterSerializer, UserProfileSerializer, ChangePasswordSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from web3 import Web3, exceptions
import os
from django.conf import settings
# from rest_framework import viewsets # Remove if LoanViewSet is also moved out
# from django.db import models # Remove as Loan model definition is moved out

# --- Web3 Configuration and Utilities ---
WEB3_PROVIDER_URL = os.environ.get('WEB3_PROVIDER_URL', 'http://127.0.0.1:8545')
CHAIN_ID = int(os.environ.get('WEB3_CHAIN_ID', 1337))

def custom_poa_middleware(make_request, w3):
    def middleware(method, params):
        if method == 'eth_chainId':
            return [None, CHAIN_ID]
        return make_request(method, params)
    return middleware

def get_web3_instance():
    w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))
    try:
        w3.middleware_onion.inject(custom_poa_middleware, layer=0)
    except Exception as e:
        pass
    if not w3.is_connected():
        raise ConnectionError(f"Web3 is not connected to {WEB3_PROVIDER_URL}. Please check your blockchain node.")
    return w3

# ---
## User Authentication and Profile Management (NO CHANGES)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Registration successful! Please log in."}, status=status.HTTP_201_CREATED)

class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data.get('old_password')
        new_password = serializer.validated_data.get('new_password')

        if not user.check_password(old_password):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)

# ---
## Wallet & Blockchain Interaction Views (NO CHANGES)

class WalletBalanceView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        wallet_address = request.query_params.get('address')
        if not wallet_address:
            wallet_address = request.user.wallet_address
            if not wallet_address:
                return Response({"error": "Wallet address not provided and not found for user."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            w3 = get_web3_instance()
            checksum_address = Web3.to_checksum_address(wallet_address)
            balance_wei = w3.eth.get_balance(checksum_address)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            return Response({'address': wallet_address, 'balance': str(balance_eth)}, status=status.HTTP_200_OK)
        except ConnectionError as e:
            return Response({'error': f'Blockchain connection error: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except exceptions.InvalidAddress:
            return Response({'error': 'Invalid Ethereum address provided.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An unexpected error occurred while fetching balance: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def token_balance(request):
    user_wallet_address = request.user.wallet_address
    if not user_wallet_address:
        return Response({"error": "Wallet address not set for user."}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"token_balance": 1000.50, "token_symbol": "ABC"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_unsigned_transaction(request):
    recipient_address = request.data.get('recipient_address')
    amount_eth = request.data.get('amount')
    sender_address = request.user.wallet_address
    if not sender_address:
        return Response({'error': 'Sender wallet address not found for this user.'}, status=status.HTTP_400_BAD_REQUEST)
    if not recipient_address or not amount_eth:
        return Response({'error': 'Recipient address and amount are required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        amount_wei = Web3.to_wei(float(amount_eth), 'ether')
        w3 = get_web3_instance()
        recipient_checksum_address = Web3.to_checksum_address(recipient_address)
        nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(sender_address))
        gas_price = w3.eth.gas_price
        transaction = {
            'from': Web3.to_checksum_address(sender_address),
            'to': recipient_checksum_address,
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': CHAIN_ID
        }
        return Response(transaction, status=status.HTTP_200_OK)
    except ValueError:
        return Response({'error': 'Invalid amount format or address.'}, status=status.HTTP_400_BAD_REQUEST)
    except ConnectionError as e:
        return Response({'error': f'Blockchain connection error: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except exceptions.InvalidAddress:
        return Response({'error': 'Invalid sender or recipient Ethereum address.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred while preparing transaction: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_signed_transaction(request):
    signed_transaction_hex = request.data.get('signed_transaction')
    if not signed_transaction_hex:
        return Response({'error': 'Signed transaction data is required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        w3 = get_web3_instance()
        signed_transaction_bytes = bytes.fromhex(signed_transaction_hex.lstrip('0x'))
        tx_hash = w3.eth.send_raw_transaction(signed_transaction_bytes)
        return Response({'message': 'Transaction sent!', 'tx_hash': tx_hash.hex()}, status=status.HTTP_200_OK)
    except exceptions.InvalidTransaction as e:
        return Response({'error': f'Invalid transaction: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except ConnectionError as e:
        return Response({'error': f'Blockchain connection error: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'error': f'An unexpected error occurred during transaction broadcast: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ---
## KYC Verification View (NO CHANGES)

class KYCVerifyView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        required_fields = ['full_name', 'id_document_url', 'selfie_url']
        for field in required_fields:
            if not request.data.get(field):
                return Response({"error": f"'{field}' is required for KYC submission."}, status=status.HTTP_400_BAD_REQUEST)
        user.kyc_status = 'submitted'
        user.save()
        return Response({"message": "KYC verification request submitted. Status: pending review."}, status=status.HTTP_202_ACCEPTED)

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({"kyc_status": user.kyc_status}, status=status.HTTP_200_OK)

# ---
## Loan ViewSet (Removed from here, assuming it's in loans app)
# You will need to import Loan and LoanSerializer from the loans app if you intend
# to use them here, but typically, the viewset would also be in the loans app.
# Example: from loans.models import Loan
# Example: from loans.serializers import LoanSerializer
# Example: from loans.views import LoanViewSet as ActualLoanViewSet