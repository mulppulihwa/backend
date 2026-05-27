from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import KakaoAuthView, ProfileView, UserView, UserPolicyListView, UserPolicySaveView, UserPolicyStatusView

auth_urlpatterns = [
    path('kakao/', KakaoAuthView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
]

profile_urlpatterns = [
    path('', ProfileView.as_view()),
    path('me/', UserView.as_view()),
]

user_policy_urlpatterns = [
    path('', UserPolicyListView.as_view()),
    path('<int:policy_id>/save/', UserPolicySaveView.as_view()),
    path('<int:policy_id>/status/', UserPolicyStatusView.as_view()),
]
