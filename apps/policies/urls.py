from django.urls import path

from .views import PolicyMatchView, PolicyParseView, PolicyPreviewView

urlpatterns = [
    path('preview/', PolicyPreviewView.as_view()),
    path('match/', PolicyMatchView.as_view()),
    path('parse/', PolicyParseView.as_view()),
]
