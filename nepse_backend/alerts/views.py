from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Watchlist, Alert
from .serializers import WatchlistSerializer, AlertSerializer
from stocks.models import Stock

class WatchlistListCreateView(generics.ListCreateAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user).order_by('-added_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WatchlistDestroyView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = 'stock__symbol'
    lookup_url_kwarg = 'symbol'

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        symbol = self.kwargs.get('symbol')
        try:
            instance = Watchlist.objects.get(user=request.user, stock__symbol=symbol)
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Watchlist.DoesNotExist:
            return Response(
                {"detail": f"Stock {symbol} not found in your watchlist."},
                status=status.HTTP_404_NOT_FOUND
            )

class AlertListCreateView(generics.ListCreateAPIView):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)
