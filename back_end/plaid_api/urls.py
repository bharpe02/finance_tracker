from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path("create_link_token/", views.create_link_token),
    path("set_access_token/", views.get_access_token),
    path("info/", views.info),
    path("transactions/", views.get_transactions),
]