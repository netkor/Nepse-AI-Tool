from django.urls import path
from .views import WatchlistListCreateView, WatchlistDestroyView

urlpatterns = [
    path('', WatchlistListCreateView.as_view(), name='watchlist_list'),
    path('<str:symbol>/', WatchlistDestroyView.as_view(), name='watchlist_destroy'),
]
