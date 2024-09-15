from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from django import forms


class UserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('name', 'email')

class UserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('name', 'email')