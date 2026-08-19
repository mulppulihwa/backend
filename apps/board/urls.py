from django.urls import path

from .views import JobPostDetailView, JobPostListView

urlpatterns = [
    path('jobs/', JobPostListView.as_view()),
    path('jobs/<int:pk>/', JobPostDetailView.as_view()),
]
