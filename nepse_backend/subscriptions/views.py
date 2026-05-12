from rest_framework import generics, permissions
from subscriptions.models import SubscriptionPlan, Subscription
from subscriptions.serializers import SubscriptionPlanSerializer, SubscriptionSerializer
from subscriptions.services.subscription_service import SubscriptionService
from rest_framework.response import Response
from rest_framework.views import APIView


class SubscriptionPlanListView(generics.ListAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer


class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, plan_slug):
        plan = SubscriptionPlan.objects.filter(slug=plan_slug).first()
        if not plan:
            return Response({'detail':'plan not found'}, status=404)
        svc = SubscriptionService()
        sub = svc.subscribe_user(request.user, plan)
        return Response(SubscriptionSerializer(sub).data)


class CancelSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, subscription_id):
        sub = Subscription.objects.filter(id=subscription_id, user=request.user).first()
        if not sub:
            return Response({'detail':'subscription not found'}, status=404)
        svc = SubscriptionService()
        svc.cancel_subscription(sub)
        return Response({'ok': True})
