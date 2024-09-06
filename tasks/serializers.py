from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['title', 'description', 'date', 'time']
    
    def create(self, validated_data):
        task = Task.objects.create(
            title = validated_data['title'],
            description = validated_data['description'],
            date = validated_data['date'],
            time = validated_data['time']
        )
        return task