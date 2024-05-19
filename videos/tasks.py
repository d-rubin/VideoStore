import glob

from celery import shared_task
from django.core.files import File
import os
import subprocess

from .models import Video
from .utils import upload_video


@shared_task
def convert_video(title: str, description: str):
    """
    Convert the video to 360p, 420p, 720p, and 1080p and upload them to S3
    :param title: The title of the video
    :param description: The description of the video
    """
    resolutions = ["360", "420", "720", "1080"]
    thumbnail_name = f"{title}_thumbnail.jpg"
    thumbnail_command = f"""ffmpeg -y -i original.mp4 -vf "select='eq(n\,10)'" -vframes 1 {thumbnail_name}"""

    subprocess.call(thumbnail_command, shell=True)

    print(f"Thumbnail created: {os.path.exists(thumbnail_name)}")  # Debug output
    with open(thumbnail_name, 'rb') as thumbnail_file:
        Video.objects.create(title=title, description=description, thumbnail=File(thumbnail_file))

    for res in resolutions:
        converted_video_name = f"{title}_{res}p.m3u8"

        convert_command = f"""ffmpeg -y -i original.mp4 -vf "scale=-2:{res}" -start_number 0 -hls_time 10 -hls_list_size 0 -f hls {converted_video_name}"""

        subprocess.call(convert_command, shell=True)
        video_chunk_files = glob.glob("*.ts")

        if os.path.exists(converted_video_name):
            upload_video(converted_video_name)
            os.remove(converted_video_name)

        for video_chunk in video_chunk_files:
            upload_video(video_chunk)
            os.remove(video_chunk)

    os.remove(thumbnail_name)
    os.remove("original.mp4")
