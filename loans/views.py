# mylendingapp_backend/loans/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Loan
from .serializers import LoanRequestSerializer, LoanListSerializer
from django.utils import timezone # For approved_date, disbursement_date
from dateutil.relativedelta import relativedelta # For accurate month addition

class LoanRequestView(generics.CreateAPIView):
    queryset = Loan.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = LoanRequestSerializer

    def perform_create(self, serializer):
        serializer.save(borrower=self.request.user, status='pending')

class LoanListView(generics.ListAPIView):
    serializer_class = LoanListSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        # If the user is staff/admin, they can see all loans.
        # Otherwise, users only see their own loans.
        if user.is_staff or user.is_superuser: # Check for staff or superuser status
            return Loan.objects.all().order_by('-created_at')
        else:
            return Loan.objects.filter(borrower=user).order_by('-created_at')

# Example: View for approving a loan (Admin/Staff only)
class LoanApprovalView(generics.UpdateAPIView):
    queryset = Loan.objects.all()
    serializer_class = LoanListSerializer
    permission_classes = (permissions.IsAdminUser,) # Only admin users can approve loans

    def update(self, request, *args, **kwargs):
        loan = self.get_object()
        # Ensure only pending loans can be approved
        if loan.status != 'pending':
            return Response({"detail": "Loan is not in 'pending' status."}, status=status.HTTP_400_BAD_REQUEST)

        loan.status = 'approved'
        loan.approved_by = request.user
        loan.approved_date = timezone.now()
        loan.disbursement_date = timezone.now() # Loan funds are disbursed upon approval

        # Calculate end_date based on disbursement_date and duration_months
        try:
            loan.end_date = loan.disbursement_date + relativedelta(months=loan.duration_months)
        except NameError:
            # Fallback if dateutil.relativedelta is not installed/imported
            loan.end_date = loan.disbursement_date + timezone.timedelta(days=loan.duration_months * 30)

        loan.save()
        return Response({"message": "Loan approved successfully.", "loan": LoanListSerializer(loan).data}, status=status.HTTP_200_OK)

# ... (Other loan views like LoanDetailView, LoanRepayView etc. would go here)