from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.users.urls import auth_urlpatterns, profile_urlpatterns, user_policy_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include(auth_urlpatterns)),
    path('api/profile/', include(profile_urlpatterns)),
    path('api/users/me/policies/', include(user_policy_urlpatterns)),
    path('api/policies/', include('apps.policies.urls')),
    path('api/places/', include('apps.places.urls')),
    path('api/regions/', include('apps.regions.urls')),
    path('api/board/', include('apps.board.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
