from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register),
    path("login/", views.login_view),
    path("logout/", views.logout_view),
    path("check-auth/", views.check_auth, name='check_auth'),
    path('get-csrf-token/', views.get_csrf_token),
]