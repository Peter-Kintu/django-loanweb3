# mylendingapp_backend/loans/models.py
from django.db import models
from users.models import User
from dateutil.relativedelta import relativedelta
from django.utils import timezone

class Loan(models.Model):
    LOAN_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved - Awaiting Collateral/Funding'), # Contract deployed, waiting for borrower to provide collateral or lender to fund
        ('active', 'Active - Loan Disbursed'), # Loan has been funded by a lender and is active
        ('repaid', 'Repaid'),
        ('overdue', 'Overdue'),
        ('rejected', 'Rejected'),
        ('liquidated', 'Liquidated'), # Collateral claimed by lender
    ]

    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowed_loans')
    lender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lent_loans')

    amount = models.DecimalField(max_digits=10, decimal_places=2) # Amount in local currency or USD equivalent
    duration_months = models.PositiveIntegerField() # Duration in months
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00) # Annual interest rate (e.g., 0.05 for 5%)
    purpose = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=30, choices=LOAN_STATUS_CHOICES, default='pending') # Increased max_length for new status

    # --- NEW BLOCKCHAIN-RELATED FIELDS ---
    contract_address = models.CharField(
        max_length=42,
        unique=True,
        null=True,
        blank=True,
        help_text="Address of the deployed P2PLoan smart contract."
    )
    # Store the actual loan and collateral asset addresses used on-chain
    # These might be different from the global configured ones for specific loans
    loan_asset_contract_address = models.CharField(max_length=42, null=True, blank=True,
                                                help_text="Address of the ERC-20 token used for the loan (e.g., DAI).")
    collateral_asset_contract_address = models.CharField(max_length=42, null=True, blank=True,
                                                      help_text="Address of the ERC-20 token used for collateral (e.g., WETH).")

    # Optional: store transaction hashes for critical operations
    deployment_tx_hash = models.CharField(max_length=66, unique=True, null=True, blank=True,
                                          help_text="Transaction hash of contract deployment.")
    disbursement_tx_hash = models.CharField(max_length=66, unique=True, null=True, blank=True,
                                            help_text="Transaction hash of loan disbursement.")
    repayment_tx_hash = models.CharField(max_length=66, unique=True, null=True, blank=True,
                                         help_text="Transaction hash of loan repayment.")
    liquidation_tx_hash = models.CharField(max_length=66, unique=True, null=True, blank=True,
                                          help_text="Transaction hash of collateral liquidation.")
    # --- END NEW FIELDS ---

    # Dates and approvals
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    approved_date = models.DateTimeField(null=True, blank=True)
    disbursement_date = models.DateTimeField(null=True, blank=True) # When funds are actually sent to borrower
    end_date = models.DateTimeField(null=True, blank=True) # Expected end date of the loan

    # Repayment tracking
    repaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_repayment_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Loan #{self.id} to {self.borrower.username} for {self.amount} ({self.status})"

    @property
    def is_approved(self):
        return self.status == 'approved' or self.status == 'active'

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_repaid(self):
        return self.status == 'repaid'

    def save(self, *args, **kwargs):
        # Calculate end_date when loan is active/disbursed
        if self.disbursement_date and not self.end_date:
            self.end_date = self.disbursement_date + relativedelta(months=self.duration_months)
        super().save(*args, **kwargs)