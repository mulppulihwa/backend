from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lib.services.geocoding import geocode_address

from .models import LocalPlace
from .serializers import LocalPlaceSerializer, LocalPlaceWriteSerializer


class PlaceListView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        places = LocalPlace.objects.filter(is_active=True).order_by('name')
        return Response(
            LocalPlaceSerializer(places, many=True, context={'request': request}).data
        )

    def post(self, request):
        serializer = LocalPlaceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data.get('lat')
        lng = serializer.validated_data.get('lng')
        if lat is None or lng is None:
            coords = geocode_address(serializer.validated_data['address'])
            lat, lng = coords if coords else (None, None)

        place = serializer.save(created_by=request.user, lat=lat, lng=lng)
        return Response(
            LocalPlaceSerializer(place, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class PlaceDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_object(self, pk):
        try:
            return LocalPlace.objects.get(pk=pk, is_active=True)
        except LocalPlace.DoesNotExist:
            return None

    def get(self, request, pk):
        place = self._get_object(pk)
        if place is None:
            return Response(
                {'error': '사용처를 찾을 수 없습니다.', 'code': 'place_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(LocalPlaceSerializer(place, context={'request': request}).data)

    def patch(self, request, pk):
        place = self._get_object(pk)
        if place is None:
            return Response(
                {'error': '사용처를 찾을 수 없습니다.', 'code': 'place_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if place.created_by_id != request.user.id:
            return Response(
                {'error': '본인이 등록한 사용처만 수정할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = LocalPlaceWriteSerializer(place, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_address = serializer.validated_data.get('address')
        address_changed = new_address and new_address != place.address
        client_supplied_coords = 'lat' in serializer.validated_data or 'lng' in serializer.validated_data
        if address_changed and not client_supplied_coords:
            coords = geocode_address(new_address)
            place.lat, place.lng = coords if coords else (None, None)

        serializer.save()
        return Response(LocalPlaceSerializer(place, context={'request': request}).data)

    def delete(self, request, pk):
        place = self._get_object(pk)
        if place is None:
            return Response(
                {'error': '사용처를 찾을 수 없습니다.', 'code': 'place_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if place.created_by_id != request.user.id:
            return Response(
                {'error': '본인이 등록한 사용처만 삭제할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )

        place.is_active = False
        place.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)
