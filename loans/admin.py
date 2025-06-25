# mylendingapp_backend/loans/admin.py
from django.contrib import admin
from .models import Loan
from django.utils import timezone # Ensure this is imported for timezone.now()

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'borrower',
        'lender',
        'amount',
        'duration_months',
        'interest_rate',
        'status',
        'contract_address', # NEW: Display the contract address
        'created_at',
        'approved_by',
        'approved_date',
        'disbursement_date',
        'repaid_amount',
        'last_repayment_date',
        'updated_at',
    )
    list_filter = (
        'status',
        'created_at',
        'duration_months',
        'lender',
        'borrower',
        'approved_by',
    )
    search_fields = (
        'borrower__username',
        'lender__username',
        'status',
        'amount',
        'purpose',
        'contract_address', # NEW: Allow searching by contract address
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'approved_by',
        'approved_date',
        'disbursement_date',
        'end_date',
        'repaid_amount', # This might be updated by smart contract events
        'last_repayment_date', # This might be updated by smart contract events
        # NEW: Blockchain related fields should typically be read-only in admin
        'contract_address',
        'loan_asset_contract_address',
        'collateral_asset_contract_address',
        'deployment_tx_hash',
        'disbursement_tx_hash',
        'repayment_tx_hash',
        'liquidation_tx_hash',
    )
    actions = ['mark_as_approved', 'mark_as_active', 'mark_as_repaid', 'mark_as_rejected', 'mark_as_overdue', 'mark_as_liquidated']

    def mark_as_approved(self, request, queryset):
        queryset.update(status='approved', approved_by=request.user, approved_date=timezone.now())
        self.message_user(request, "Selected loans marked as Approved.")
    mark_as_approved.short_description = "Mark selected loans as Approved"

    def mark_as_active(self, request, queryset):
        # This action would typically be triggered by a contract event listener, not manual admin action.
        # Included for completeness/manual override if needed for testing.
        queryset.update(status='active', disbursement_date=timezone.now())
        self.message_user(request, "Selected loans marked as Active (Disbursed).")
    mark_as_active.short_description = "Mark selected loans as Active (Disbursed)"

    def mark_as_repaid(self, request, queryset):
        # This action would typically be triggered by a contract event listener.
        queryset.update(status='repaid', last_repayment_date=timezone.now())
        self.message_user(request, "Selected loans marked as Repaid.")
    mark_as_repaid.short_description = "Mark selected loans as Repaid"

    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, "Selected loans marked as Rejected.")
    mark_as_rejected.short_description = "Mark selected loans as Rejected"

    def mark_as_overdue(self, request, queryset):
        queryset.update(status='overdue')
        self.message_user(request, "Selected loans marked as Overdue.")
    mark_as_overdue.short_description = "Mark selected loans as Overdue"

    def mark_as_liquidated(self, request, queryset):
        # This action would typically be triggered by a contract event listener.
        queryset.update(status='liquidated')
        self.message_user(request, "Selected loans marked as Liquidated.")
    mark_as_liquidated.short_description = "Mark selected loans as Liquidated"