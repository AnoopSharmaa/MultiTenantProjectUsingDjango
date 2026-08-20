from django.urls import path

from .views import (
    CurrentTenantDetailView,
    TenantRegistrationView,
)


urlpatterns = [
    path(
        "register/",
        TenantRegistrationView.as_view(),
        name="tenant-register",
    ),
    path(
        "current/",
        CurrentTenantDetailView.as_view(),
        name="current-tenant",
    ),
]