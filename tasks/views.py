from .serializers import TaskSerializer
from rest_framework import status
from rest_framework.response import Response

def create(request):
    serializer = TaskSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
    else:
        return Response({'message': 'Data in invalid format or poorly formed request'}, status=status.HTTP_400_BAD_REQUEST)