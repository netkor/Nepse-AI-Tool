from django.http import JsonResponse
from subscriptions.services.subscription_service import SubscriptionService


class RequireFeatureMiddleware:
    """Middleware to enforce that certain views require subscription features.

    Set `request.required_feature = '<feature_name>'` in view or use decorator to mark.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.service = SubscriptionService()

    def __call__(self, request):
        feature = getattr(request, 'required_feature', None)
        if feature:
            if not request.user or not request.user.is_authenticated:
                return JsonResponse({'detail': 'Authentication required'}, status=401)
            if not self.service.check_access(request.user, feature):
                return JsonResponse({'detail': 'Subscription required'}, status=402)
        return self.get_response(request)
