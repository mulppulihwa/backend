from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LocalPlace


class PlaceListView(APIView):
    def get(self, request):
        places = LocalPlace.objects.filter(is_active=True).order_by('name')
        from .serializers import LocalPlaceSerializer
        return Response(LocalPlaceSerializer(places, many=True).data)
