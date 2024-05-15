import os
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import boto3
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_200_OK
from .serializers import VideoSerializer
from .tasks import convert_video
from .models import Video
from wsgiref.util import FileWrapper


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

        convert_video.delay(title, description)

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
        video_title = kwargs["video_title"]

        if video_title is None:
            return Response({"status": 400, "message": "Bad request", "data": None}, status=HTTP_400_BAD_REQUEST)

        # Connect to S3
        try:
            s3 = boto3.client("s3", aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                              aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))
        except Exception:
            return Response({"status": 500, "message": "Connection to S3 could not be established", "data": None},
                            status=HTTP_400_BAD_REQUEST)

        # Get the video file from S3
        try:
            file = s3.get_object(Bucket=f"videoflix", Key=f"{video_title}p.m3u8")
        except Exception:
            return Response({"status": 404, "message": "Video not found", "data": None}, status=HTTP_400_BAD_REQUEST)

        # Create a file wrapper for streaming
        wrapper = FileWrapper(file["Body"])

        # Create a streaming response
        response = StreamingHttpResponse(wrapper, content_type='application/vnd.apple.mpegurl')


        # Set content disposition for correct file naming
        response['Content-Disposition'] = f'attachment; filename={video_title}p.m3u8'

        return response


class SegmentDownloadView(APIView):
    """
    IMPORTANT: The segment_name needs to be in the format {title}_{resolution}p{segment_number}.ts
    """
    @staticmethod
    def get(request, *args, **kwargs):
        segment_name = kwargs["segment_name"]

        if segment_name is None:
            return Response({"status": 400, "message": "Bad request", "data": None}, status=HTTP_400_BAD_REQUEST)

        # Connect to S3
        try:
            s3 = boto3.client("s3", aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                              aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))
        except Exception:
            return Response({"status": 500, "message": "Connection to S3 could not be established", "data": None},
                            status=HTTP_400_BAD_REQUEST)

        # Get the video segment from S3
        try:
            file = s3.get_object(Bucket=f"videoflix", Key=f"{segment_name}")
        except Exception:
            return Response({"status": 404, "message": "Video segment not found", "data": None}, status=HTTP_400_BAD_REQUEST)

        # Create a file wrapper for streaming
        wrapper = FileWrapper(file["Body"])

        # Create a streaming response
        response = StreamingHttpResponse(wrapper, content_type='video/MP2T')

        # Set content disposition for correct file naming
        response['Content-Disposition'] = f'attachment; filename={segment_name}'

        return response


class VideoListView(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        video_list = Video.objects.all()
        serializer = VideoSerializer(video_list, many=True)
        return Response({"status": 200,
                         "message": "Videos retrieved successfully",
                         "data": serializer.data},
                        status=HTTP_200_OK)
