# mylendingapp/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT Authentication Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Include app-specific URLs
    path('api/users/', include('users.urls')),
    path('api/wallet/', include('wallet.urls')), # Make sure this is included
    path('api/loans/', include('loans.urls')),   # Make sure this is included
    path('api/kyc/', include('kyc.urls')),
]