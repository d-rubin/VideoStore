import os

import environ
from pathlib import Path

from boto3 import Session
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from minio import Minio
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR, \
    HTTP_404_NOT_FOUND
from .serializers import VideoSerializer
from .tasks import convert_video
from .models import Video
from wsgiref.util import FileWrapper

env = environ.Env()
# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")
environ.Env.read_env()


@method_decorator(csrf_exempt, name="dispatch")
class UploadView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request, *args, **kwargs):
        file = request.FILES.get("file")
        title: str = request.POST.get("title")
        description: str = request.POST.get("description")

        if (file is None) or (title is None) or (description is None):
            return Response({"status": 400, "message": "Bad request", "data": None}, status=HTTP_400_BAD_REQUEST)


        # Save the original file locally
        with open("original.mp4", "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        convert_video(title, description)

        return Response({
            "status": 201,
            "message": "Video uploaded and converted successfully",
            "data": None}, status=HTTP_201_CREATED)


class DownloadView(APIView):
    """
    IMPORTANT: The video_title needs to be in the format {title}_{resolution}
    """
    @staticmethod
    def get(request, *args, **kwargs):
        video_title = kwargs.get("video_title")

        if not video_title:
            return Response({"status": 400, "message": "Bad request: Missing video_title", "data": None},
                            status=HTTP_400_BAD_REQUEST)

        # Connect to MinIO
        try:
            session = Session(
                aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY"),
                aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY")
            )
            s3 = session.client(
                "s3",
                endpoint_url=f'https://{os.environ.get("MINIO_URL")}'  # Example: "http://s3.daniel-rubin.de"
            )
        except Exception as e:
            return Response(
                {"status": 500, "message": f"Connection to MinIO could not be established: {str(e)}", "data": None},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Fetch the video file from MinIO
        bucket_name = os.environ.get("BUCKET_NAME")
        if not bucket_name:
            return Response(
                {"status": 500, "message": "BUCKET_NAME environment variable is not set", "data": None},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            file = s3.get_object(Bucket=bucket_name, Key=f"{video_title}p.m3u8")
        except s3.exceptions.NoSuchKey:
            return Response({"status": 404, "message": "Video not found", "data": None}, status=HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"status": 500, "message": f"An error occurred while fetching the video: {str(e)}", "data": None},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create a file wrapper for streaming
        wrapper = FileWrapper(file["Body"])

        # Create a streaming response
        response = StreamingHttpResponse(wrapper, content_type="application/vnd.apple.mpegurl")

        # Set content disposition for correct file naming
        response["Content-Disposition"] = f'attachment; filename="{video_title}p.m3u8"'

        return response


class SegmentDownloadView(APIView):
    """
    IMPORTANT: The segment_name needs to be in the format {title}_{resolution}p{segment_number}.ts
    """
    @method_decorator(cache_page(None))  # Disable caching by setting None
    def get(self, request, *args, **kwargs):
        segment_name = kwargs.get("segment_name")

        if not segment_name:
            return Response({"status": 400, "message": "Bad request: Missing segment_name", "data": None},
                            status=HTTP_400_BAD_REQUEST)

        # Connect to MinIO
        try:
            minio_client = Minio(
                os.environ.get("MINIO_URL"),
                access_key=os.environ.get("MINIO_ACCESS_KEY"),
                secret_key=os.environ.get("MINIO_SECRET_KEY"),
                secure=True
            )
        except Exception as e:
            return Response(
                {"status": 500, "message": f"Connection to MinIO could not be established: {str(e)}", "data": None},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Fetch the video segment from MinIO
        bucket_name = os.environ.get("MINIO_BUCKET_NAME")
        if not bucket_name:
            return Response(
                {"status": 500, "message": "MINIO_BUCKET_NAME environment variable is not set", "data": None},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            response_data = minio_client.get_object(bucket_name, segment_name)
        except Exception as e:
            if "NoSuchKey" in str(e):
                return Response({"status": 404, "message": "Video segment not found", "data": None},
                                status=HTTP_404_NOT_FOUND)
            return Response(
                {"status": 500, "message": f"An error occurred while fetching the video segment: {str(e)}", "data": None},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create a file wrapper for streaming
        wrapper = FileWrapper(response_data)

        # Create a streaming response
        response = StreamingHttpResponse(wrapper, content_type="video/MP2T")

        # Set content disposition for correct file naming
        response["Content-Disposition"] = f'attachment; filename="{segment_name}"'

        return response


class VideoListView(ListAPIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(None))
    def get(self, request, *args, **kwargs):
        video_list = Video.objects.all()
        serializer = VideoSerializer(video_list, many=True)
        return Response({"status": 200,
                         "message": "Videos retrieved successfully",
                         "data": serializer.data},
                        status=HTTP_200_OK)
