from rest_framework import serializers
from subscriptions.models import SubscriptionPlan, Subscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ('id','slug','name','price_cents','currency','interval','features')


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer()
    class Meta:
        model = Subscription
        fields = ('id','user','plan','status','current_period_start','current_period_end')
