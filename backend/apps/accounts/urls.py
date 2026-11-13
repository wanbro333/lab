from django.urls import path
from . import views

urlpatterns = [
    path("csrf/", views.csrf),
    path("me/", views.me),
    path("login/", views.sign_in),
    path("logout/", views.sign_out),
]
