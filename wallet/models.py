# mylendingapp_backend/wallet/models.py
from django.db import models
from users.models import User # Assuming your custom User model is in 'users' app

class UserWallet(models.Model):
    """
    Represents a blockchain wallet address associated with a user.
    A user might have multiple wallets, but for simplicity, we'll assume one primary for now.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet_info')
    address = models.CharField(max_length=42, unique=True, db_index=True, help_text="Ethereum wallet address")
    # You might add fields like:
    # private_key_encrypted = models.CharField(max_length=255, blank=True, null=True) # Highly discouraged, usually for hot wallets/custodial
    # is_primary = models.BooleanField(default=True) # If a user can have multiple wallets

    # Add fields for tracking balances if you want to cache them (though real-time is often better)
    # native_token_balance = models.DecimalField(max_digits=25, decimal_places=10, default=0)
    # last_updated_balance = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Wallet"
        verbose_name_plural = "User Wallets"

    def __str__(self):
        return f"Wallet for {self.user.username}: {self.address}"