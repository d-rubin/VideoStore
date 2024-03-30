import re
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from django.utils.encoding import force_bytes, force_str
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class RegisterView(APIView):
    @staticmethod
    def post(request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        email = request.data.get("email", "")

        if User.objects.filter(username=username).exists():
            return Response({"status": 401, "message": "Username already registered"}, status=HTTP_401_UNAUTHORIZED)

        if User.objects.filter(email=email).exists():
            return Response({"status": 401, "message": "Email already registered"}, status=HTTP_401_UNAUTHORIZED)

        if len(username) < 3:
            return Response({"status": 401, "message": "Username too short"}, status=HTTP_401_UNAUTHORIZED)

        if len(password) < 6:
            return Response({"status": 401, "message": "Password too weak"}, status=HTTP_401_UNAUTHORIZED)

        if not re.search("^[A-Za-z0-9_!#$%&'*+/=?`{|}~^.-]+@[A-Za-z0-9.-]+$", email):
            return Response({"status": 401, "message": "Not a valid email"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.create_user(username, email, password, is_active=False)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            activation_link = reverse("verify-email", kwargs={"uidb64": uid, "token": token})
            activation_url = request.build_absolute_uri(activation_link)
            user.save()
            send_mail(
                "Registered",
                f"""You successfully registered to Videoflix! 
                Please confirm your email by clicking on this link\n{activation_url}""",
                "videoflix@daniel-rubin.de",
                [email],
            )
            return Response({"status": 201, "message": "User registered successfully"}, status=HTTP_201_CREATED)
        except Exception:
            return Response({"status": 400, "message": "Bad request"}, status=HTTP_400_BAD_REQUEST)


class VerifyView(APIView):
    """"
    Activates the user after the user verified his email
    """
    @staticmethod
    def get(request, uidb64=None, token=None):
        if uidb64 is None or token is None:
            return Response({"status": 404, "message": "Something's missing"}, status=HTTP_400_BAD_REQUEST)
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"status": 200, "message": "Successfully confirmed email"}, status=HTTP_200_OK)
        else:
            return Response({"status": 401, "message": "Link expired"}, status=HTTP_401_UNAUTHORIZED)


class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        try:
            user = User.objects.filter(username=request.data.get("username"))
            if not user:
                return Response({"status": 401, "message": "No such user"}, status=status.HTTP_401_UNAUTHORIZED)
            if not user[0].check_password(request.data.get("password")):
                return Response({"status": 401, "message": "Wrong credentials"}, status=status.HTTP_401_UNAUTHORIZED)

            if not user[0].is_active:
                return Response({"status": 401, "message": "User not verified"}, status=status.HTTP_401_UNAUTHORIZED)

            token, created = Token.objects.get_or_create(user=user[0])

            return Response({
                "token": token.key,
                "status": 200,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
