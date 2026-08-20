# tenants/views.py

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from common.responses import APIResponse

from .serializers import TenantRegistrationSerializer


import logging

logger = logging.getLogger(__name__)


class TenantRegistrationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(
            "Tenant registration started: method=%s path=%s",
            request.method,
            request.path,
        )

        serializer = TenantRegistrationSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)
        logger.info("Tenant registration validated")

        tenant = serializer.save()
        logger.info(
            "Tenant registration saved: tenant_id=%s schema_name=%s",
            tenant.pk,
            tenant.schema_name,
        )

        response_serializer = TenantRegistrationSerializer(
            tenant,
            context={"request": request},
        )

        response = APIResponse.success(
            data=response_serializer.data,
            message="Tenant registered successfully.",
            status_code=status.HTTP_201_CREATED,
            request=request,
        )

        logger.info(
            "Tenant registration completed: tenant_id=%s status=%s",
            tenant.pk,
            response.status_code,
        )

        return response



from rest_framework.generics import RetrieveAPIView

from .permissions import IsTenantRequest
from .serializers import CurrentTenantSerializer


class CurrentTenantDetailView(RetrieveAPIView):
    serializer_class = CurrentTenantSerializer
    permission_classes = [IsTenantRequest]

    def get_object(self):
        return self.request.tenant
