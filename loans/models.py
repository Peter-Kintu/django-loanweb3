# mylendingapp_backend/loans/models.py
from django.db import models
from users.models import User # Assuming User model is in the users app
from django.utils import timezone # Import for default values if needed, or in views

class Loan(models.Model):
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans_as_borrower')
    # RECOMMENDED ADDITION: A lender is crucial for a lending app
    lender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans_as_lender',
                               help_text="The user or entity providing the loan funds.")

    amount = models.DecimalField(max_digits=18, decimal_places=2) # e.g., in USDC or USD equivalent
    duration_months = models.PositiveIntegerField(default=12, help_text="Duration of the loan in months.")
    purpose = models.TextField(blank=True, null=True, help_text="Purpose of the loan.")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.05,
                                         help_text="Annual interest rate (e.g., 0.05 for 5%).")

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('active', 'Active Loan'), # Loan disbursed, payments expected
            ('repaid', 'Repaid'),
            ('overdue', 'Overdue'),
            ('liquidated', 'Liquidated'), # Collateral seized or loan written off
        ],
        default='pending'
    )

    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans',
                                     help_text="Admin/Staff user who approved the loan.")
    approved_date = models.DateTimeField(null=True, blank=True, help_text="Date and time when the loan was approved.")

    # RENAMED for clarity: 'start_date' -> 'disbursement_date'
    # This field should be set when the loan moves to 'active' status.
    disbursement_date = models.DateTimeField(null=True, blank=True,
                                             help_text="Date and time when the loan funds were disbursed.")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Expected date for full loan repayment.")

    repaid_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0.00,
                                         help_text="Total amount repaid so far.")
    # RECOMMENDED ADDITION: To track when the last repayment occurred
    last_repayment_date = models.DateTimeField(null=True, blank=True,
                                               help_text="Date of the most recent repayment.")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when the loan application was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Date and time when the loan record was last updated.")

    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
        ordering = ['-created_at'] # Order by newest first

    def __str__(self):
        return f"Loan {self.id} for {self.borrower.username} - {self.amount}"

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_repaid(self):
        return self.status == 'repaid'

    # You might want to add methods here for calculating remaining balance,
    # payment schedule, etc.