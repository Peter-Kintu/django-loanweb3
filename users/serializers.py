from rest_framework import serializers
from .models import User  # Ensure your custom User model is imported

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    # Added password confirmation for better user experience and validation
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        # Include phone_number as a required field for registration
        # wallet_address and kyc_status will be null/default upon registration
        fields = ('username', 'email', 'password', 'password_confirm', 'phone_number')
        extra_kwargs = {
            'email': {'required': True}, # Often required for registration
            'phone_number': {'required': True}
        }

    def validate(self, data):
        """
        Check that the two password fields match.
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "New passwords must match."})
        return data

    def create(self, validated_data):
        # Remove password_confirm as it's not a model field
        validated_data.pop('password_confirm')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number'),
            # kyc_status and wallet_address will use their default values from the model
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Added 'kyc_status' and 'wallet_address' to fields to be displayed
        # 'is_staff' is included as per your request
        fields = ('username', 'email', 'phone_number', 'kyc_status', 'wallet_address', 'is_staff')
        # Username and email are generally not updated through a public profile endpoint
        # kyc_status is typically updated through a dedicated KYC endpoint (KYCVerifyView)
        # wallet_address might be set once and then not directly changeable by the user via profile update
        read_only_fields = ('username', 'email', 'kyc_status', 'wallet_address', 'is_staff')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(required=True, style={'input_type': 'password'})

    def validate(self, data):
        """
        Check that the two new password fields match.
        """
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "New passwords must match."})
        return data