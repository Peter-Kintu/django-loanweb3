# mylendingapp_backend/kyc/urls.py
from django.urls import path
from .views import UserKYCView, AdminKYCListView, AdminKYCDetailView

urlpatterns = [
    # User-facing endpoints
    path('kyc/', UserKYCView.as_view(), name='user-kyc'), # GET (retrieve/check status), POST (create), PUT/PATCH (update)

    # Admin-facing endpoints
    path('admin/kyc/', AdminKYCListView.as_view(), name='admin-kyc-list'),
    path('admin/kyc/<int:pk>/', AdminKYCDetailView.as_view(), name='admin-kyc-detail'),
]