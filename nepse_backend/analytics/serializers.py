from rest_framework import serializers
from analytics.models import AggregatedMetric


class AggregatedMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = AggregatedMetric
        fields = ('id','metric_name','period','period_start','period_end','value','extra')
