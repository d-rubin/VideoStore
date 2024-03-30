from django.urls import path

from .views import UploadView, DownloadView, VideoListView

urlpatterns = [
    path("upload/", UploadView.as_view(), name="upload"),
    path("download/<str:video_title>/", DownloadView.as_view(), name="download"),
    path("", VideoListView.as_view(), name="list"),
]
