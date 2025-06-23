# mylendingapp_backend/kyc/models.py
from django.db import models
from users.models import User # Assuming your custom User model is in 'users' app

class KYCSubmission(models.Model):
    """
    Represents a user's Know Your Customer (KYC) submission.
    """
    KYC_STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('submitted', 'Submitted for Review'), # A user might submit, then it's pending internal processing
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('resubmit_required', 'Resubmission Required'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc_submission')
    status = models.CharField(
        max_length=20,
        choices=KYC_STATUS_CHOICES,
        default='pending'
    )

    # Personal Information
    full_name = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Document Information
    # IMPORTANT: In a real-world app, you would upload documents to secure cloud storage (e.g., AWS S3, Google Cloud Storage, IPFS)
    # and store only the secure URL or reference here, NOT the document itself.
    document_type = models.CharField(max_length=50, blank=True, null=True,
        choices=[
            ('passport', 'Passport'),
            ('national_id', 'National ID'),
            ('drivers_license', 'Driver\'s License'),
            ('other', 'Other'),
        ]
    )
    document_number = models.CharField(max_length=100, blank=True, null=True)
    document_front_url = models.URLField(max_length=500, blank=True, null=True,
        help_text="Secure URL to the front side of the identity document.")
    document_back_url = models.URLField(max_length=500, blank=True, null=True,
        help_text="Secure URL to the back side of the identity document (if applicable).")
    # For selfie/proof of life
    selfie_url = models.URLField(max_length=500, blank=True, null=True,
        help_text="Secure URL to a selfie or proof-of-life image.")

    # Reviewer Information
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kyc_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "KYC Submission"
        verbose_name_plural = "KYC Submissions"

    def __str__(self):
        return f"KYC for {self.user.username} - Status: {self.status}"