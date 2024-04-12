from celery import shared_task
from django.core.files import File
import os
import subprocess

from .utils import upload_video


@shared_task
def convert_video(title: str):
    """
    Convert the video to 360p, 420p, 720p, and 1080p and upload them to S3
    :param title: The title of the video
    """
    resolutions = ["360", "420", "720", "1080"]
    for res in resolutions:
        converted_video_name = f"{title}_{res}p.m3u8"
        # Use ffmpeg to convert the video
        command = f"""ffmpeg -i original.mp4 -vf "scale=-2:{res}" -start_number 0 -hls_time 10 -hls_list_size 0 -f hls {converted_video_name}"""

        subprocess.call(command, shell=True)

        if os.path.exists(converted_video_name):
            upload_video(converted_video_name)

        # Delete the local converted video files
        os.remove(converted_video_name)
        os.remove(f"{title}_{res}p0.ts")

    # Delete the local .mp4 video file
    os.remove("original.mp4")
