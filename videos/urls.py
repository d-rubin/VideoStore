from django.urls import path

from .views import UploadView, DownloadView, VideoListView, SegmentDownloadView

urlpatterns = [
    path("upload/", UploadView.as_view(), name="upload"),
    path("download/<str:video_title>/", DownloadView.as_view(), name="download"),
    path("download/<str:video_title>/<str:segment_name>/", SegmentDownloadView.as_view(), name="segment_download"),
    path("", VideoListView.as_view(), name="list"),
]
