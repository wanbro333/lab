from django.urls import path
from .views import items

urlpatterns = [path("items/", items, name="items")]
