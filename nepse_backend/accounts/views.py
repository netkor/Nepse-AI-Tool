"""
Views for Accounts app.
Handles authentication and user profile management.
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

from config.auth import TokenManager, get_tokens_for_user
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user data.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['username'] = user.username
        return token

    def validate(self, attrs):
        """
        Allow users to authenticate using email or username.
        If the provided identifier looks like an email and matches a user,
        replace the username field with that user's username so the
        parent serializer will authenticate correctly.
        """
        username_field = self.username_field
        identifier = attrs.get(username_field)
        if identifier and '@' in identifier:
            try:
                user = User.objects.get(email__iexact=identifier)
                # set the username value to the user's actual username
                attrs[username_field] = user.get_username()
            except User.DoesNotExist:
                # leave attrs as-is; parent will handle authentication failure
                pass
        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view using custom serializer.
    """
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    User registration endpoint.
    POST /api/auth/register/
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                'success': True,
                'message': 'User registered successfully.',
                'data': {
                    'email': serializer.data['email'],
                    'username': serializer.data['username'],
                }
            },
            status=status.HTTP_201_CREATED
        )
    return Response(
        {
            'success': False,
            'message': 'Registration failed.',
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get or update user profile.
    GET /api/auth/profile/ - Get user profile
    PATCH /api/auth/profile/ - Update user profile
    """
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(
            {
                'success': True,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'PATCH':
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'success': True,
                    'message': 'Profile updated successfully.',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                'success': False,
                'message': 'Profile update failed.',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password.
    POST /api/auth/change-password/
    """
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        if not user.check_password(serializer.data.get('old_password')):
            return Response(
                {
                    'success': False,
                    'message': 'Old password is incorrect.',
                    'errors': {'old_password': 'Wrong password.'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.data.get('new_password'))
        user.save()
        return Response(
            {
                'success': True,
                'message': 'Password changed successfully.'
            },
            status=status.HTTP_200_OK
        )
    return Response(
        {
            'success': False,
            'message': 'Password change failed.',
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting their refresh token.
    POST /api/auth/logout/
    
    Request body:
    {
        "refresh": "refresh_token_string"
    }
    """
    try:
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {
                    'success': False,
                    'message': 'Refresh token is required.',
                    'errors': {'refresh': 'This field is required.'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Blacklist the refresh token
        TokenManager.blacklist_token(refresh_token)
        
        logger.info(f"User {request.user.username} logged out")
        
        return Response(
            {
                'success': True,
                'message': 'Logout successful.'
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return Response(
            {
                'success': False,
                'message': 'Logout failed.',
                'errors': {'detail': str(e)}
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh access token using refresh token.
    POST /api/auth/refresh/
    
    Request body:
    {
        "refresh": "refresh_token_string"
    }
    """
    try:
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {
                    'success': False,
                    'message': 'Refresh token is required.',
                    'errors': {'refresh': 'This field is required.'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new access token
        new_access_token = TokenManager.refresh_access_token(refresh_token)
        
        return Response(
            {
                'success': True,
                'access': new_access_token
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        return Response(
            {
                'success': False,
                'message': 'Token refresh failed.',
                'errors': {'detail': str(e)}
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
