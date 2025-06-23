# mylendingapp_backend/wallet/admin.py
from django.contrib import admin
from .models import UserWallet

@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'address')
    search_fields = ('user__username', 'address')
    list_filter = ('user',)