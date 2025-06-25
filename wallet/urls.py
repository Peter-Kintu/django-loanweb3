# mylendingapp_backend/wallet/urls.py
from django.urls import path
from .views import (
    UserWalletCreateView,
    UserWalletRetrieveUpdateView,
    WalletBalanceView,
    erc20_token_balance,
    get_transaction_params, # New
    broadcast_signed_transaction # New
)

urlpatterns = [
    # Endpoint to set/create a wallet address for the authenticated user
    path('wallet/set/', UserWalletCreateView.as_view(), name='wallet-set'),
    # Endpoint to retrieve/update the authenticated user's wallet address
    path('wallet/my-address/', UserWalletRetrieveUpdateView.as_view(), name='wallet-my-address'),
    # Endpoint to get the native token (ETH/Matic/etc.) balance of any address
    path('wallet/balance/', WalletBalanceView.as_view(), name='wallet-balance'),
    # Endpoint to get specific ERC-20 token balance
    path('wallet/token-balance/', erc20_token_balance, name='erc20-token-balance'),
    # Endpoint to get current gas price and sender's nonce
    path('wallet/transaction-params/', get_transaction_params, name='get-transaction-params'),
    # Endpoint to broadcast a raw, signed transaction from the client
    path('wallet/broadcast/', broadcast_signed_transaction, name='broadcast-signed-transaction'),
]