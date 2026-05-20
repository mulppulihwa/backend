from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Region


class RegionListView(APIView):
    def get(self, request):
        regions = Region.objects.all().order_by('code')
        from .serializers import RegionSerializer
        return Response(RegionSerializer(regions, many=True).data)
