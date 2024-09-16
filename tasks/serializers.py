from rest_framework import serializers
from .models import Task, OAUTHToken

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class OAUTHTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OAUTHToken
        fields = '__all__'