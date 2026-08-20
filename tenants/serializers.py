import re

from django.conf import settings
from django.db import IntegrityError,transaction
from django.utils.text import slugify
from rest_framework import serializers

from .models import Domain, Tenant


SCHEMA_NAME_MAX_LENGTH = Tenant._meta.get_field(
    "schema_name"
).max_length


def normalize_phone(phone):
    normalized = re.sub(r"[\s()\-]", "", phone)

    if normalized.startswith("+91"):
        normalized = normalized[3:]
    elif normalized.startswith("91") and len(normalized) == 12:
        normalized = normalized[2:]

    if (
        not re.fullmatch(r"[6-9]\d{9}", normalized)
        or len(set(normalized)) == 1
    ):
        raise serializers.ValidationError("Invalid phone number.")

    return normalized


def organization_slug(name):
    """
    Convert an organization name into a subdomain-safe value.

    Bright Academy -> bright-academy
    """
    value = slugify(name) or "institute"

    # Leave space for suffixes such as -2, -3.
    value = value[:50].strip("-")

    return value or "institute"


def generate_unique_tenant_identifiers(name):
    """
    Generate a unique schema name and domain.

    First Bright Academy:
        schema = bright_academy
        domain = bright-academy.localhost

    Second Bright Academy:
        schema = bright_academy_2
        domain = bright-academy-2.localhost
    """
    base_slug = organization_slug(name)
    number = 1

    while True:
        if number == 1:
            domain_label = base_slug
        else:
            domain_label = f"{base_slug}-{number}"

        schema_name = domain_label.replace("-", "_")
        schema_name = schema_name[:SCHEMA_NAME_MAX_LENGTH]

        domain_name = (
            f"{domain_label}.{settings.TENANT_BASE_DOMAIN}"
        )

        schema_exists = Tenant.objects.filter(
            schema_name__iexact=schema_name
        ).exists()

        domain_exists = Domain.objects.filter(
            domain__iexact=domain_name
        ).exists()

        if not schema_exists and not domain_exists:
            return schema_name, domain_name

        number += 1


class TenantRegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=150,
        allow_blank=False,
    )

    organization_type = serializers.ChoiceField(
        choices=Tenant.OrganizationType.choices,
    )

    email = serializers.EmailField()

    phone = serializers.CharField(
        max_length=20,
        allow_blank=False,
    )

    def validate_name(self, value):
        # Convert repeated spaces into one space.
        value = " ".join(value.split())

        if len(value) < 2:
            raise serializers.ValidationError(
                "Organization name must contain at least 2 characters."
            )

        return value

    def validate_email(self, value):
        email = value.strip().lower()

        if Tenant.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "A tenant is already registered with this email."
            )

        return email

    def validate_phone(self, value):
        phone = normalize_phone(value)

        if Tenant.objects.filter(phone=phone).exists():
            raise serializers.ValidationError(
                "A tenant is already registered with this phone number."
            )

        return phone

    def create(self, validated_data):
        schema_name, domain_name = (
            generate_unique_tenant_identifiers(
                validated_data["name"]
            )
        )

        tenant = None

        try:
            # TenantMixin.save() creates the PostgreSQL schema because
            # Tenant.auto_create_schema is True.
            with transaction.atomic():
                tenant = Tenant.objects.create(
                    schema_name=schema_name,
                    **validated_data,
                )

                # DomainMixin supplies:
                # - domain
                # - tenant ForeignKey
                # - is_primary
                domain = Domain.objects.create(
                    domain=domain_name,
                    tenant=tenant,
                    is_primary=True,
                )

        except IntegrityError as exception:
            # This protects against two concurrent requests attempting to
            # register the same email, phone, schema or domain.
            if tenant is not None and tenant.pk:
                tenant.delete(force_drop=True)

            raise serializers.ValidationError(
                {
                    "detail": (
                        "A tenant with the same email, phone or "
                        "generated domain already exists."
                    )
                }
            ) from exception

        tenant.registration_domain = domain

        return tenant

    def to_representation(self, tenant):
        domain = getattr(
            tenant,
            "registration_domain",
            tenant.get_primary_domain(),
        )

        request = self.context.get("request")

        scheme = "https"
        port_suffix = ""

        if request and not request.is_secure():
            scheme = "http"

        if request:
            port = request.get_port()

            if port not in {"80", "443"}:
                port_suffix = f":{port}"

        application_url = (
            f"{scheme}://{domain.domain}{port_suffix}"
            if domain
            else None
        )

        return {
            "id": tenant.pk,
            "name": tenant.name,
            "organization_type": tenant.organization_type,
            "email": tenant.email,
            "phone": tenant.phone,
            "schema_name": tenant.schema_name,
            "domain": domain.domain if domain else None,
            "application_url": application_url,
            "on_trial": tenant.on_trial,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at,
        }




class CurrentTenantSerializer(serializers.ModelSerializer):
    primary_domain = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "organization_type",
            "schema_name",
            "primary_domain",
            "on_trial",
            "paid_until",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields

    def get_primary_domain(self, tenant):
        domain = tenant.get_primary_domain()

        if domain is None:
            return None

        return domain.domain