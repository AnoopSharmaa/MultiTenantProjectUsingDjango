from django.db import connection
from django_tenants.utils import get_public_schema_name
from rest_framework.permissions import BasePermission


class IsTenantRequest(BasePermission):
    message = "This endpoint is available only on a tenant domain."

    def has_permission(self, request, view):
        return connection.schema_name != get_public_schema_name()