# tenants/models.py

from django.db import models
from django.db.models.functions import Lower
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    class OrganizationType(models.TextChoices):
        COACHING = "coaching", "Coaching Institute"
        SCHOOL = "school", "School"

    # Different organizations may have the same display name.
    name = models.CharField(max_length=150)

    organization_type = models.CharField(
        max_length=20,
        choices=OrganizationType.choices,
    )

    email = models.EmailField()

    # Phone is normalized by the registration serializer before saving.
    phone = models.CharField(
        max_length=20,
        unique=True,
    )

    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        constraints = [
            # Prevents both Test@example.com and test@example.com.
            models.UniqueConstraint(
                Lower("email"),
                name="unique_tenant_email_case_insensitive",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
    def __str__(self):
        return self.domain