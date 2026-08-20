# common/responses.py

from rest_framework import status
from rest_framework.response import Response


class APIResponse:
    """Factory for consistent API response envelopes."""

    @staticmethod
    def success(
        *,
        data=None,
        message="Request completed successfully.",
        status_code=status.HTTP_200_OK,
        request=None,
        meta=None,
    ):
        payload = {
            "success": True,
            "message": message,
            "data": data,
        }

        if meta is not None:
            payload["meta"] = meta

        request_id = getattr(request, "request_id", None)

        if request_id:
            payload["request_id"] = request_id

        return Response(payload, status=status_code)

    @staticmethod
    def error(
        *,
        errors=None,
        message="Request failed.",
        status_code=status.HTTP_400_BAD_REQUEST,
        request=None,
    ):
        payload = {
            "success": False,
            "message": message,
            "errors": errors,
        }

        request_id = getattr(request, "request_id", None)

        if request_id:
            payload["request_id"] = request_id

        return Response(payload, status=status_code)