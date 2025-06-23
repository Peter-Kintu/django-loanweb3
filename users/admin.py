from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    # Fields to display in the list view
    list_display = ('username', 'email', 'phone_number', 'kyc_status', 'is_staff', 'is_active', 'date_joined')
    # Fields to filter by in the sidebar
    list_filter = ('is_staff', 'is_active', 'kyc_status', 'date_joined')
    # Fields to search by
    search_fields = ('username', 'email', 'phone_number', 'wallet_address')
    # Default ordering
    ordering = ('username',)

    # Customize the fieldsets for adding/changing users
    fieldsets = BaseUserAdmin.fieldsets + (
        (('Custom Fields'), {'fields': ('phone_number', 'kyc_status', 'wallet_address')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (('Custom Fields'), {'fields': ('phone_number', 'kyc_status', 'wallet_address')}),
    )