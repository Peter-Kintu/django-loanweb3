# users/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
# from rest_framework.authtoken.models import Token # Only if using TokenAuth
# from django.contrib.auth import authenticate # Only if implementing manual login logic
from .models import User
from .serializers import UserRegisterSerializer, UserProfileSerializer, ChangePasswordSerializer

class KYCVerifyView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        # This is a simplified placeholder for a KYC submission.
        # Your kyc app has more detailed logic.
        # This view would typically just set user.kyc_status to 'submitted'
        # and rely on the kyc app's AdminKYCDetailView to change it to 'verified', 'rejected', etc.

        # For a full KYC submission from the frontend, use the KYC app's UserKYCView (POST/PUT).
        # This view's role here is minimal, possibly just a trigger.
        required_fields = ['full_name', 'id_document_url', 'selfie_url'] # Example fields
        for field in required_fields:
            if not request.data.get(field):
                return Response({"error": f"'{field}' is required for KYC submission."}, status=status.HTTP_400_BAD_REQUEST)
        user.kyc_status = 'submitted'
        user.save()
        return Response({"message": "KYC verification request submitted. Status: pending review."}, status=status.HTTP_202_ACCEPTED)

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({"kyc_status": user.kyc_status}, status=status.HTTP_200_OK)


# General User Registration View
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,) # Allow unauthenticated users to register

# User Profile View
class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

# User Profile Update View
class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        serializer.save()

# Change Password View
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.validated_data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password hashes the password
            self.object.set_password(serializer.validated_data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }
            return Response(response)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)