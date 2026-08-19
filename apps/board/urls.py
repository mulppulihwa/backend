from django.urls import path

from .views import (
    HousingPostDetailView, HousingPostListView,
    JobApplicationListView, JobApplyView, JobPostDetailView, JobPostListView,
)

urlpatterns = [
    path('jobs/', JobPostListView.as_view()),
    path('jobs/<int:pk>/', JobPostDetailView.as_view()),
    path('jobs/<int:pk>/apply/', JobApplyView.as_view()),
    path('jobs/<int:pk>/applications/', JobApplicationListView.as_view()),
    path('housing/', HousingPostListView.as_view()),
    path('housing/<int:pk>/', HousingPostDetailView.as_view()),
]
