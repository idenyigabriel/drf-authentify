from django.urls import re_path

from sample_project.views import LoginView, LogoutView, AccountView


app_name = "sample_project"


urlpatterns = [
    re_path(r"^login/?$", LoginView.as_view(), name="login"),
    re_path(r"^logout/?$", LogoutView.as_view(), name="logout"),
    re_path(r"^me/?$", AccountView.as_view(), name="account"),
]
