from django.urls import re_path

from sample_project.views import LoginView, LogoutView, LogoutAllView, LogoutByUserView


app_name = "sample_project"


urlpatterns = [
    re_path(r"^login/?$", LoginView.as_view(), name="login"),
    re_path(r"^logout/?$", LogoutView.as_view(), name="logout"),
    re_path(r"^logout-all/?$", LogoutAllView.as_view(), name="logout-all"),
    re_path(r"^logout-by-user/?$", LogoutByUserView.as_view(), name="login-by-user"),
]
