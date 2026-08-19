from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobPost
from .serializers import JobPostSerializer, JobPostWriteSerializer


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
