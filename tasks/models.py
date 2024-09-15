from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from .managers import UserManager

class User(AbstractUser):
    username=None
    first_name=None
    last_name=None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    objects = UserManager()
    def __str__(self):
        return self.email

class Task(models.Model):
    title = models.CharField(max_length=75)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class OAUTHToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    token_uri = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    scopes = models.JSONField(default=list)
    universe_domain = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Token for {self.user.email}'