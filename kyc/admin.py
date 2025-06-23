# mylendingapp_backend/kyc/admin.py
from django.contrib import admin
from .models import KYCSubmission

@admin.register(KYCSubmission)
class KYCSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'status', 'full_name', 'document_type',
        'reviewed_by', 'reviewed_at', 'created_at'
    )
    list_filter = ('status', 'document_type', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'full_name', 'document_number', 'address')
    readonly_fields = ('user', 'created_at', 'updated_at') # User should not be changed directly in admin

    # Customize form fields for admin view
    fieldsets = (
        (None, {
            'fields': ('user', 'status', 'rejection_reason')
        }),
        ('Personal Information', {
            'fields': ('full_name', 'date_of_birth', 'nationality', 'address')
        }),
        ('Document Information', {
            'fields': ('document_type', 'document_number', 'document_front_url', 'document_back_url', 'selfie_url')
        }),
        ('Review Details', {
            'fields': ('reviewed_by', 'reviewed_at'),
            'classes': ('collapse',) # Collapse this section by default
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Allow changing status directly in admin
    # This might be redundant if using AdminKYCDetailView, but good for quick changes
    actions = ['mark_verified', 'mark_rejected', 'mark_resubmission_required']

    def mark_verified(self, request, queryset):
        queryset.update(status='verified', reviewed_by=request.user, reviewed_at=timezone.now(), rejection_reason=None)
        # Update user's kyc_status as well
        for kyc_obj in queryset:
            user = kyc_obj.user
            user.kyc_status = 'verified'
            user.save()
        self.message_user(request, "Selected KYC submissions marked as Verified.")
    mark_verified.short_description = "Mark selected KYC submissions as Verified"

    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected', reviewed_by=request.user, reviewed_at=timezone.now())
        # Update user's kyc_status as well
        for kyc_obj in queryset:
            user = kyc_obj.user
            user.kyc_status = 'rejected'
            user.save()
        self.message_user(request, "Selected KYC submissions marked as Rejected. Provide reasons in detail view if needed.")
    mark_rejected.short_description = "Mark selected KYC submissions as Rejected"

    def mark_resubmission_required(self, request, queryset):
        queryset.update(status='resubmit_required', reviewed_by=request.user, reviewed_at=timezone.now())
        # Update user's kyc_status as well
        for kyc_obj in queryset:
            user = kyc_obj.user
            user.kyc_status = 'resubmit_required'
            user.save()
        self.message_user(request, "Selected KYC submissions marked as Resubmission Required.")
    mark_resubmission_required.short_description = "Mark selected KYC submissions as Resubmission Required"