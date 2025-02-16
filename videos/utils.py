import os
from boto3.session import Session


def upload_video(video: str):
    """
    Connect to MinIO and upload the video.
    :param video: The video file to upload.
    """
    session = Session(
        aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY"),
    )
    s3 = session.resource(
        "s3",
        endpoint_url=f'https://{os.environ.get("MINIO_URL")}'
    )
    bucket_name = os.environ.get("BUCKET_NAME")

    try:
        s3.Bucket(bucket_name).upload_file(Filename=video, Key=os.path.basename(video))
        print(f"Successfully uploaded {video} to {bucket_name}.")
    except Exception as e:
        print(f"Failed to upload {video}: {e}")
