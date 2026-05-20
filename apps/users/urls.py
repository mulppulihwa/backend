from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import KakaoAuthView

urlpatterns = [
    path('kakao/', KakaoAuthView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
]
