from django.urls import path

from .views import PlaceDetailView, PlaceEndorseView, PlaceListView

urlpatterns = [
    path('', PlaceListView.as_view()),
    path('<int:pk>/', PlaceDetailView.as_view()),
    path('<int:pk>/endorse/', PlaceEndorseView.as_view()),
]
