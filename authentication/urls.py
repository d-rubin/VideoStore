from django.urls import path, include

from .views import RegisterView, LoginView, VerifyView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("verify/<str:uidb64>/<str:token>/", VerifyView.as_view(), name="verify-email"),
    path("password_reset/", include("django_rest_passwordreset.urls", namespace="password_reset")),
]
