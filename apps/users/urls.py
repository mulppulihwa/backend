from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import KakaoAuthView, ProfileView

auth_urlpatterns = [
    path('kakao/', KakaoAuthView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
]

profile_urlpatterns = [
    path('', ProfileView.as_view()),
]
