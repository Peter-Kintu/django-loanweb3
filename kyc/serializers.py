# mylendingapp_backend/kyc/serializers.py
from rest_framework import serializers
from .models import KYCSubmission
from users.models import User # For updating user's kyc_status field

class KYCSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for users to submit/view their KYC information.
    """
    class Meta:
        model = KYCSubmission
        fields = [
            'id', 'status', 'full_name', 'date_of_birth', 'nationality', 'address',
            'document_type', 'document_number', 'document_front_url', 'document_back_url',
            'selfie_url', 'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'rejection_reason', 'created_at', 'updated_at'
            # 'reviewed_by', 'reviewed_at' are for admin, not user submission
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        # Check if user already has a pending/verified KYC
        if hasattr(user, 'kyc_submission') and user.kyc_submission:
            raise serializers.ValidationError("User already has an existing KYC submission. Please update or wait for review.")

        kyc_submission = KYCSubmission.objects.create(user=user, status='submitted', **validated_data)
        # Also update the user's kyc_status in the User model
        user.kyc_status = 'submitted'
        user.save()
        return kyc_submission

    def update(self, instance, validated_data):
        # Allow users to update their submission if it's rejected or resubmission required
        if instance.status not in ['rejected', 'resubmit_required', 'pending']:
            raise serializers.ValidationError("KYC submission cannot be updated in its current status.")

        # Set status back to 'submitted' upon update
        validated_data['status'] = 'submitted'
        instance.rejection_reason = None # Clear rejection reason on resubmission

        # Update all fields in validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update user's kyc_status again
        instance.user.kyc_status = 'submitted'
        instance.user.save()
        return instance

class KYCStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for administrators to update KYC status.
    """
    class Meta:
        model = KYCSubmission
        fields = ['status', 'rejection_reason']
        read_only_fields = [] # All fields are writable for admin update

    def validate(self, data):
        # Ensure status is one of the valid admin-set statuses
        valid_statuses = ['verified', 'rejected', 'resubmit_required']
        if data['status'] not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status for update. Must be one of: {', '.join(valid_statuses)}")

        if data['status'] in ['rejected', 'resubmit_required'] and not data.get('rejection_reason'):
            raise serializers.ValidationError("Rejection reason is required for 'rejected' or 'resubmit_required' statuses.")

        return data

    def update(self, instance, validated_data):
        # Update KYC status and related fields
        instance.status = validated_data.get('status', instance.status)
        instance.rejection_reason = validated_data.get('rejection_reason', instance.rejection_reason)
        instance.reviewed_by = self.context['request'].user
        instance.reviewed_at = serializers.DateTimeField(read_only=True).to_internal_value(serializers.DateTimeField().now()) # Set current time
        instance.save()

        # Update the user's kyc_status in the User model as well
        user = instance.user
        user.kyc_status = instance.status
        user.save()

        return instance