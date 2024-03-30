from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from .models import Video


class VideoModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up non-modified objects used by all test methods
        Video.objects.create(title="Test Video", description="This is a test video")

    def test_title_label(self):
        video = Video.objects.get(id=1)
        field_label = video._meta.get_field("title").verbose_name
        self.assertEqual(field_label, "title")

    def test_description_label(self):
        video = Video.objects.get(id=1)
        field_label = video._meta.get_field("description").verbose_name
        self.assertEqual(field_label, "description")

    def test_object_name_is_title(self):
        video = Video.objects.get(id=1)
        expected_object_name = f"{video.title}"
        self.assertEqual(expected_object_name, str(video))


class VideoViewTest(APITestCase):
    url = "http://127.0.0.1:8000/videos/"

    def setUp(self):
        self.video1 = Video.objects.create(title="Test Video 1", description="This is a test video 1")
        self.video2 = Video.objects.create(title="Test Video 2", description="This is a test video 2")

        # Create a test user
        self.test_user = User.objects.create_user(username='testuser', password='testpassword')
        # Generate a token for the test user
        self.token = Token.objects.create(user=self.test_user)

    def test_video_list_view(self):
        response = self.client.get(self.url, headers={"Authorization": f"Token {self.token.key}"})
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
