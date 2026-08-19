from django.urls import path

from .views import (
    JobApplicationListView, JobApplyView, JobPostDetailView, JobPostListView,
)

urlpatterns = [
    path('jobs/', JobPostListView.as_view()),
    path('jobs/<int:pk>/', JobPostDetailView.as_view()),
    path('jobs/<int:pk>/apply/', JobApplyView.as_view()),
    path('jobs/<int:pk>/applications/', JobApplicationListView.as_view()),
]
