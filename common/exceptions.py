# common/exceptions.py

import logging

from rest_framework import status
from rest_framework.views import exception_handler

from .responses import APIResponse


logger = logging.getLogger(__name__)


def api_exception_handler(exception, context):
    """Convert DRF exceptions into the project's standard error envelope."""
    response = exception_handler(exception, context)
    request = context.get("request")

    if response is None:
        logger.error(
            "Unhandled API exception",
            exc_info=(
                type(exception),
                exception,
                exception.__traceback__,
            ),
        )

        return APIResponse.error(
            message="An unexpected error occurred.",
            errors=None,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request=request,
        )

    original_data = response.data
    message = "Request failed."
    errors = original_data

    if (
        isinstance(original_data, dict)
        and set(original_data) == {"detail"}
    ):
        message = str(original_data["detail"])
        errors = None
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        message = "Validation failed."

    wrapped_response = APIResponse.error(
        message=message,
        errors=errors,
        status_code=response.status_code,
        request=request,
    )

    for header_name, header_value in response.headers.items():
        wrapped_response[header_name] = header_value

    return wrapped_response