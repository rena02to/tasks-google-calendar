from django.urls import path
from .views import Create, Login

urlpatterns = [
    path('login/', Login.as_view(), name="login"),
    path('create/', Create, name="create"),
]
