from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=75)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title