from django.urls import path
from .views import create, Login

urlpatterns = [
    path('create/', create, name="create"),
    path('login', Login.as_view(), name="login"),
]
