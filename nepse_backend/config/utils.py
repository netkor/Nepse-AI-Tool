"""
Utility functions and custom exception handlers for the NEPSE Backend.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that returns consistent error responses.
    """
    response = exception_handler(exc, context)
    
    if response is None:
        return Response(
            {
                'success': False,
                'message': str(exc),
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    if response.status_code == status.HTTP_403_FORBIDDEN:
        response.data = {
            'success': False,
            'message': 'You do not have permission to perform this action.',
            'status': status.HTTP_403_FORBIDDEN
        }
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        response.data = {
            'success': False,
            'message': 'Authentication credentials were not provided or are invalid.',
            'status': status.HTTP_401_UNAUTHORIZED
        }
    
    return response
