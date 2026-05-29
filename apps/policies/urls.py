from django.urls import path

from .views import PolicyChecklistView, PolicyMatchView, PolicyParseView, PolicyPreviewView

urlpatterns = [
    path('preview/', PolicyPreviewView.as_view()),
    path('match/', PolicyMatchView.as_view()),
    path('parse/', PolicyParseView.as_view()),
    path('<int:policy_id>/checklist/', PolicyChecklistView.as_view()),
]
