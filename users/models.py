# users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Added fields for user profile
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    # KYC Status with clear choices for better data integrity
    KYC_STATUS_CHOICES = [
        ('none', 'No KYC Submitted'),
        ('submitted', 'KYC Submitted - Pending Review'),
        ('verified', 'KYC Verified'),
        ('rejected', 'KYC Rejected'),
    ]
    kyc_status = models.CharField(
        max_length=50, # Increased max_length to accommodate longer choices
        choices=KYC_STATUS_CHOICES,
        default='none', # Default to 'none' for a new user
        help_text="Current Know Your Customer (KYC) verification status."
    )

    # Ethereum wallet address
    wallet_address = models.CharField(
        max_length=42, # Standard Ethereum address length (0x + 40 hex chars)
        unique=True,
        blank=True,
        null=True,
        help_text="Ethereum wallet address linked to this user's account."
    )

    # Add any other fields you might need in the future, e.g.,
    # date_of_birth = models.DateField(blank=True, null=True)
    # country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username