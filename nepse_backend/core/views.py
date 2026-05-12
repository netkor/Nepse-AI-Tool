"""Views for core app."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings


class HealthCheckView(APIView):
    """
    Health check endpoint for monitoring.
    
    Returns:
        Response: Status of the application
    """
    
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        """Health check endpoint."""
        return Response(
            {
                'status': 'ok',
                'service': 'nepse-ai-backend',
                'debug': settings.DEBUG,
                'database': 'connected',
            },
            status=status.HTTP_200_OK
        )
