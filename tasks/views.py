from .serializers import TaskSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

class Login(APIView):
    def post(self, request):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if creds and creds.valid:
            return Response({'message': 'You are already authenticated. The logout URL is /logout'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
            
            email = get_user_info(creds)

            return Response({'message': 'Login successful. The logout URL is /logout', 'email': email}, status=status.HTTP_200_OK)

def create(request):
    pass