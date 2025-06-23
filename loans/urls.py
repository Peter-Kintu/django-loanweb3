from django.urls import path
from .views import LoanRequestView, LoanListView, LoanApprovalView

urlpatterns = [
    path('request/', LoanRequestView.as_view(), name='loan-request'),
    path('list/', LoanListView.as_view(), name='loan-list'),
    path('<int:pk>/approve/', LoanApprovalView.as_view(), name='loan-approve'), # Example for admin
    # path('<int:pk>/', LoanDetailView.as_view(), name='loan-detail'),
    # path('<int:pk>/repay/', LoanRepayView.as_view(), name='loan-repay'),
]