# mylendingapp_backend/loans/serializers.py
from rest_framework import serializers
from .models import Loan # This is correct, Loan is in loans.models
# REMOVED: from users.models import UserProfile # This line is not needed here

class LoanRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ('amount', 'duration_months', 'purpose')

class LoanListSerializer(serializers.ModelSerializer):
    borrower_username = serializers.CharField(source='borrower.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    lender_username = serializers.CharField(source='lender.username', read_only=True, allow_null=True)


    class Meta:
        model = Loan
        fields = (
            'id', 'borrower_username', 'lender_username', 'amount', 'duration_months', 'purpose',
            'interest_rate', 'status', 'approved_by_username', 'approved_date',
            'disbursement_date', 'end_date', 'repaid_amount', 'created_at', 'updated_at',
            'is_approved', 'is_repaid'
        )