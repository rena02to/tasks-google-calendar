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
    id = models.CharField(max_length=255, primary_key=True)
    title = models.CharField(max_length=75)
    description = models.TextField()
    locale = models.CharField(max_length=255)
    full_day = models.BooleanField()
    start_date = models.DateField()
    start_hour = models.TimeField(null=True)
    end_date = models.DateField()
    end_hour = models.TimeField(null=True)
    participants = models.JSONField(default=list)
    reminders = models.JSONField(default=list)
    appellant = models.BooleanField()
    recurrence =  models.CharField(max_length=100, null=True)
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