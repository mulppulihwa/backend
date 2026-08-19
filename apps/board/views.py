from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lib.services.geocoding import geocode_address

from .models import HousingPhoto, HousingPost, JobApplication, JobPost
from .serializers import (
    HousingPostSerializer, HousingPostWriteSerializer,
    JobApplicationSerializer, JobApplicationWriteSerializer,
    JobPostSerializer, JobPostWriteSerializer,
)

MAX_HOUSING_IMAGES = 10
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


class JobPostListView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        posts = JobPost.objects.filter(is_active=True).order_by('-created_at')
        category = request.query_params.get('category')
        if category:
            posts = posts.filter(category=category)
        region = request.query_params.get('region')
        if region:
            posts = posts.filter(region=region)
        return Response(JobPostSerializer(posts, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = JobPostWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(created_by=request.user)
        return Response(
            JobPostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class JobPostDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_object(self, pk):
        try:
            return JobPost.objects.get(pk=pk, is_active=True)
        except JobPost.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(JobPostSerializer(post, context={'request': request}).data)

    def patch(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 수정할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = JobPostWriteSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(JobPostSerializer(post, context={'request': request}).data)

    def delete(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 삭제할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )
        post.is_active = False
        post.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class JobApplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            job_post = JobPost.objects.get(pk=pk, is_active=True)
        except JobPost.DoesNotExist:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if JobApplication.objects.filter(job_post=job_post, applicant=request.user).exists():
            return Response(
                {'error': '이미 지원한 모집글입니다.', 'code': 'already_applied'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        apply_serializer = JobApplicationWriteSerializer(data=request.data)
        apply_serializer.is_valid(raise_exception=True)
        validated_data = apply_serializer.validated_data

        name = validated_data.get('name') or request.user.profile.applicant_name
        phone = validated_data.get('phone') or request.user.phone
        if not name or not phone:
            return Response(
                {'error': '이름과 전화번호를 입력해주세요.', 'code': 'missing_applicant_info'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application = JobApplication.objects.create(
                job_post=job_post, applicant=request.user,
                name=name, phone=phone, message=validated_data.get('message', ''),
            )
        except IntegrityError:
            return Response(
                {'error': '이미 지원한 모집글입니다.', 'code': 'already_applied'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = request.user.profile
        if profile.applicant_name != name:
            profile.applicant_name = name
            profile.save(update_fields=['applicant_name'])
        if request.user.phone != phone:
            request.user.phone = phone
            request.user.save(update_fields=['phone'])

        return Response(JobApplicationSerializer(application).data, status=status.HTTP_201_CREATED)


class JobApplicationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            job_post = JobPost.objects.get(pk=pk, is_active=True)
        except JobPost.DoesNotExist:
            return Response(
                {'error': '모집글을 찾을 수 없습니다.', 'code': 'job_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if job_post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 지원자 목록을 볼 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )

        applications = job_post.applications.order_by('-applied_at')
        return Response(JobApplicationSerializer(applications, many=True).data)


class HousingPostListView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        posts = HousingPost.objects.filter(is_active=True).order_by('-created_at')
        room_type = request.query_params.get('room_type')
        if room_type:
            posts = posts.filter(room_type=room_type)
        region = request.query_params.get('region')
        if region:
            posts = posts.filter(region=region)
        return Response(HousingPostSerializer(posts, many=True, context={'request': request}).data)

    def post(self, request):
        serializer = HousingPostWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        images = request.FILES.getlist('images')
        if len(images) > MAX_HOUSING_IMAGES:
            return Response(
                {'error': f'사진은 최대 {MAX_HOUSING_IMAGES}장까지 업로드할 수 있습니다.', 'code': 'too_many_images'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        image_field = drf_serializers.ImageField()
        for img in images:
            if img.size > MAX_IMAGE_SIZE_BYTES:
                return Response(
                    {'error': '이미지 파일은 10MB 이하여야 합니다.', 'code': 'image_too_large'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                image_field.run_validation(img)
            except (drf_serializers.ValidationError, DjangoValidationError):
                return Response(
                    {'error': '올바른 이미지 파일이 아닙니다.', 'code': 'invalid_image'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            img.seek(0)

        coords = geocode_address(serializer.validated_data['detail_address'])
        lat, lng = coords if coords else (None, None)

        with transaction.atomic():
            post = serializer.save(created_by=request.user, lat=lat, lng=lng)
            HousingPhoto.objects.bulk_create([
                HousingPhoto(housing_post=post, image=img, order=i)
                for i, img in enumerate(images)
            ])

        return Response(
            HousingPostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class HousingPostDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def _get_object(self, pk):
        try:
            return HousingPost.objects.get(pk=pk, is_active=True)
        except HousingPost.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '매물을 찾을 수 없습니다.', 'code': 'housing_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(HousingPostSerializer(post, context={'request': request}).data)

    def patch(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '매물을 찾을 수 없습니다.', 'code': 'housing_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 수정할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = HousingPostWriteSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_address = serializer.validated_data.get('detail_address')
        if new_address and new_address != post.detail_address:
            coords = geocode_address(new_address)
            post.lat, post.lng = coords if coords else (None, None)

        serializer.save()
        return Response(HousingPostSerializer(post, context={'request': request}).data)

    def delete(self, request, pk):
        post = self._get_object(pk)
        if post is None:
            return Response(
                {'error': '매물을 찾을 수 없습니다.', 'code': 'housing_post_not_found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if post.created_by_id != request.user.id:
            return Response(
                {'error': '작성자만 삭제할 수 있습니다.', 'code': 'not_owner'},
                status=status.HTTP_403_FORBIDDEN,
            )
        post.is_active = False
        post.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)
