# mylendingapp_backend/wallet/serializers.py
from rest_framework import serializers
from .models import UserWallet

class UserWalletSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and retrieving a user's wallet address.
    """
    class Meta:
        model = UserWallet
        fields = ['address'] # Users can submit their address
        read_only_fields = ['user'] # User is set by the view

    def create(self, validated_data):
        # This custom create method is necessary because we are using OneToOneField
        # and we need to link it to the current authenticated user.
        user = self.context['request'].user
        if hasattr(user, 'wallet_info') and user.wallet_info:
            raise serializers.ValidationError("This user already has a wallet address set.")
        wallet = UserWallet.objects.create(user=user, **validated_data)
        return wallet

class WalletBalanceSerializer(serializers.Serializer):
    """
    Serializer for displaying wallet balance.
    The balance field is not directly from a model.
    """
    wallet_address = serializers.CharField(max_length=42)
    balance = serializers.CharField(max_length=50) # Use CharField as it could be a large decimal string
    # token_balances = serializers.JSONField(required=False) # For multiple token balances