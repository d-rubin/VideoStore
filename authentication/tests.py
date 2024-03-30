from django.contrib.auth.models import User
from rest_framework.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED, HTTP_200_OK
from rest_framework.test import APITestCase

default_user = {
    "username": "test-daniel",
    "password": "123456dkdiefn",
    "email": "daniel.rubin1997+registertest@gmail.com",
}


def setup_user(active: bool = True):
    User.objects.create_user(
        default_user.get("username"),
        default_user.get("email"),
        default_user.get("password"),
        is_active=active,
    )


class RegisterTestCase(APITestCase):
    url = "http://127.0.0.1:8000/auth/register/"

    def test_successful_register(self):
        response = self.client.post(self.url, default_user, "json")
        self.assertEqual(response.status_code, HTTP_201_CREATED)

    def test_username_exists(self):
        User.objects.create_user(
            default_user.get("username"),
            "daniel.rubin1997+registertest2@gmail.com",
            default_user.get("password")
        )
        response = self.client.post(self.url, default_user, "json")
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"status": 401, "message": "Username already registered"})

    def test_email_exists(self):
        User.objects.create_user(
            "test2-daniel",
            default_user.get("email"),
            default_user.get("password")
        )
        response = self.client.post(self.url, default_user, "json")
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"status": 401, "message": "Email already registered"})

    def test_username_too_short(self):
        response = self.client.post(
            self.url,
            {"username": "A", "email": default_user.get("email"), "password": default_user.get("password")},
            "json"
        )
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"status": 401, "message": "Username too short"})

    def test_password_not_strong_enough(self):
        response = self.client.post(
            self.url,
            {"username": default_user.get("username"), "email": default_user.get("email"), "password": "12345"},
            "json"
        )
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"status": 401, "message": "Password too weak"})

    def test_email_not_valid(self):
        response = self.client.post(
            self.url,
            {
                "username": default_user.get("username"),
                "email": "daniel.rubin",
                "password": default_user.get("password")
            },
            "json"
        )
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"status": 401, "message": "Not a valid email"})

    def tearDown(self):
        # Löschen Sie die benutzerdefinierten Daten nach jedem Testfall
        User.objects.all().delete()


class LoginTestCase(APITestCase):
    url = "http://127.0.0.1:8000/auth/login/"

    def test_login_valid(self):
        setup_user()
        response = self.client.post(
            self.url,
            {"username": default_user.get("username"), "password": default_user.get("password")},
            "json"
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_wrong_username(self):
        setup_user()
        response = self.client.post(
            self.url,
            {"username": "test-not-daniel", "password": default_user.get("password")},
            "json"
        )
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"status": 401, "message": "No such user"})

    def test_wrong_password(self):
        setup_user()
        response = self.client.post(
            self.url,
            {"username": default_user.get("username"), "password": "123456"},
            "json"
        )
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"status": 401, "message": "Wrong credentials"})

    def test_user_not_verified(self):
        setup_user(False)
        response = self.client.post(
            self.url,
            {"username": default_user.get("username"), "password": default_user.get("password")},
            "json"
        )
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"status": 401, "message": "User not verified"})

    def test_user_not_exists(self):
        setup_user(False)
        response = self.client.post(
            self.url,
            {"username": "HabeDere", "password": default_user.get("password")},
            "json"
        )
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"status": 401, "message": "No such user"})
