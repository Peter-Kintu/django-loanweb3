# mylendingapp_backend/kyc/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import KYCSubmission
from .serializers import KYCSubmissionSerializer, KYCStatusUpdateSerializer
from django.utils import timezone # For setting reviewed_at timestamp

class UserKYCView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for an authenticated user to submit, retrieve, or update their own KYC.
    - POST (create): Submit new KYC data if none exists.
    - GET (retrieve): Get current KYC submission details.
    - PUT/PATCH (update): Update existing KYC, typically if status is 'rejected' or 'resubmit_required'.
    """
    serializer_class = KYCSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Get the KYC submission for the current authenticated user
        obj, created = KYCSubmission.objects.get_or_create(user=self.request.user)
        # If it's a new empty object, set its status to pending so user can fill it
        if created:
            obj.status = 'pending'
            obj.save()
        return obj

    def post(self, request, *args, **kwargs):
        # This view handles both creation and update via GET/PUT/PATCH.
        # For simplicity, if a user tries to POST and a KYC already exists,
        # we'll tell them to use PUT/PATCH.
        try:
            kyc_submission = self.request.user.kyc_submission
            return Response(
                {"detail": "You already have a KYC submission. Use PUT/PATCH to update it."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except KYCSubmission.DoesNotExist:
            return self.create(request, *args, **kwargs)

class AdminKYCListView(generics.ListAPIView):
    """
    API endpoint for administrators to list all KYC submissions.
    """
    queryset = KYCSubmission.objects.all().order_by('-created_at')
    serializer_class = KYCSubmissionSerializer
    permission_classes = [permissions.IsAdminUser] # Only admin users can view all KYC

class AdminKYCDetailView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for administrators to view and update the status of a specific KYC submission.
    """
    queryset = KYCSubmission.objects.all()
    serializer_class = KYCStatusUpdateSerializer # Use a separate serializer for status update
    permission_classes = [permissions.IsAdminUser] # Only admin users can approve/reject

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request # Pass request to serializer for 'reviewed_by'
        return context

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)