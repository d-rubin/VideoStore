import os
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import boto3
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_200_OK
from .serializers import VideoSerializer
from .tasks import convert_video
from .models import Video


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

        Video.objects.create(title=title, description=description)

        # Save the original file locally
        local_file_path = f"{title}.mp4"
        with open(local_file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        convert_video(local_file_path, title)
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
            file = s3.get_object(Bucket="videoflix", Key=f"{video_title}p.m3u8")
        except Exception:
            return Response({"status": 404, "message": "Video not found", "data": None}, status=HTTP_400_BAD_REQUEST)

        return FileResponse(file["Body"], content_type="octet-stream")


class VideoListView(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        video_list = Video.objects.all()
        serializer = VideoSerializer(video_list, many=True)
        return Response({"status": 200, "message": "Videos retrieved successfully", "data": serializer.data}, status=HTTP_200_OK)
