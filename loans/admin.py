# mylendingapp_backend/loans/admin.py
from django.contrib import admin
from .models import Loan
from django.utils import timezone # Ensure this is imported for timezone.now()

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        'borrower',
        'lender',          # Now exists in models.py
        'amount',
        'duration_months', # Matches models.py
        'interest_rate',
        'status',
        'created_at',      # Matches models.py
        'approved_by',
        'approved_date',   # Matches models.py
        'disbursement_date', # Matches models.py
        'repaid_amount',
        'last_repayment_date', # Matches models.py
        'updated_at',
    )
    list_filter = (
        'status',
        'created_at',       # Matches models.py
        'duration_months',  # Matches models.py
        'lender',           # Now exists in models.py
        'borrower',
        'approved_by',
    )
    search_fields = (
        'borrower__username',
        'lender__username', # Now exists in models.py
        'status',
        'amount',
        'purpose',
    )
    readonly_fields = (
        'created_at',           # Matches models.py
        'updated_at',
        'approved_date',        # Matches models.py
        'disbursement_date',    # Matches models.py
        'repaid_amount',
        'last_repayment_date',  # Matches models.py
    )

    # Admin actions for status changes
    actions = ['mark_as_approved', 'mark_as_repaid', 'mark_as_rejected', 'mark_as_overdue', 'mark_as_liquidated']

    def mark_as_approved(self, request, queryset):
        # Update status, approved_by, and approved_date
        queryset.update(status='approved', approved_by=request.user, approved_date=timezone.now())
        self.message_user(request, "Selected loans marked as Approved.")
    mark_as_approved.short_description = "Mark selected loans as Approved"

    def mark_as_repaid(self, request, queryset):
        # When marking as repaid, set status and the last_repayment_date
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
        queryset.update(status='liquidated')
        self.message_user(request, "Selected loans marked as Liquidated.")
    mark_as_liquidated.short_description = "Mark selected loans as Liquidated"