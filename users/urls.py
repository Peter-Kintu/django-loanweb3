# django-backend/users/urls.py

from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token # For login, if using TokenAuthentication
from .views import (
    RegisterView,
    ProfileView,
    ProfileUpdateView,
    ChangePasswordView,
)

urlpatterns = [
    # User Authentication & Registration
    path('register/', RegisterView.as_view(), name='register'),
    # Use DRF's default token obtain view for login (if using TokenAuthentication)
    # If you're solely relying on Simple JWT, you can remove this login path
    path('login/', obtain_auth_token, name='login'),

    # User Profile Management
    path('profile/', ProfileView.as_view(), name='profile-detail'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # No wallet, KYC, or loan-related paths here
]