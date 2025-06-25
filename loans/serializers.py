# mylendingapp_backend/loans/serializers.py
from rest_framework import serializers
from .models import Loan
from users.models import User # Import User model to be used in LoanApprovalSerializer

class LoanRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ('amount', 'duration_months', 'purpose')

class LoanListSerializer(serializers.ModelSerializer):
    borrower_username = serializers.CharField(source='borrower.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    lender_username = serializers.CharField(source='lender.username', read_only=True, allow_null=True)

    # New fields for blockchain integration
    contract_address = serializers.CharField(read_only=True, allow_null=True, help_text="Address of the deployed P2PLoan smart contract")
    # p2p_loan_id is removed as contract_address is unique and serves as the primary identifier on-chain.
    # If your P2PLoanFactory assigns an ID, you might put it here.
    # For now, we'll assume the contract_address is sufficient for linking.


    class Meta:
        model = Loan
        fields = (
            'id', 'borrower_username', 'lender_username', 'amount', 'duration_months', 'purpose',
            'interest_rate', 'status', 'approved_by_username', 'approved_date',
            'disbursement_date', 'end_date', 'repaid_amount', 'created_at', 'updated_at',
            'is_approved', 'is_repaid', 'is_active', # Added is_active property
            'contract_address', # Include the new field
            'loan_asset_contract_address', # Include loan asset address
            'collateral_asset_contract_address', # Include collateral asset address
            'deployment_tx_hash',
            'disbursement_tx_hash',
            'repayment_tx_hash',
            'liquidation_tx_hash',
        )

class LoanApprovalSerializer(serializers.ModelSerializer):
    """
    Serializer for admin to approve a loan request.
    This includes setting the lender if an admin chooses to be the lender.
    """
    # Lender can be set by the admin during approval
    lender = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=True), # Or filter by users that can be lenders
        allow_null=True, required=False
    )
    # Allow admin to set interest rate during approval
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)

    class Meta:
        model = Loan
        fields = ['status', 'lender', 'interest_rate']
        read_only_fields = ['borrower', 'amount', 'duration_months', 'purpose']

    def validate(self, data):
        if 'status' in data and data['status'] == 'approved':
            if 'interest_rate' not in data or data['interest_rate'] is None:
                raise serializers.ValidationError("Interest rate is required when approving a loan.")
            if data['interest_rate'] <= 0:
                raise serializers.ValidationError("Interest rate must be positive.")
        return data

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        if 'lender' in validated_data:
            instance.lender = validated_data.get('lender', instance.lender)
        instance.interest_rate = validated_data.get('interest_rate', instance.interest_rate)
        instance.save()
        return instance