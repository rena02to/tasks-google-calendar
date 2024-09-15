from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.conf import settings
import jwt
from .models import OAUTHToken
import pytz

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar'
]
User = get_user_model()

class Login(APIView):
    def post(self, request):
        #definition of the Google API and what will be requested in the service
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json",
            SCOPES
        )
        try:
            #open the browser to authenticate
            creds = flow.run_local_server(port=54857, prompt='select_account')
            service = build('oauth2', 'v2', credentials=creds)
            #recupera o e-mail
            user_info = service.userinfo().get().execute()
            email = user_info.get('email')
            name = user_info.get('name')

            #checks if the user exists: if it exists, returns, otherwise, creates and returns
            user, created = User.objects.get_or_create(email=email)

            #update username
            user.name = name
            user.save()

            expiry_str = creds.expiry.isoformat()
            expires_at = datetime.strptime(expiry_str, "%Y-%m-%dT%H:%M:%S.%f")
            expires_at = expires_at.replace(tzinfo=pytz.UTC)

            #create the user's OAuth token in the db
            OAUTHToken.objects.update_or_create(
                user = user,
                defaults={
                    'access_token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'universe_domain': creds.universe_domain,
                    'expires_at': expires_at,
                    'token_uri': creds.token_uri,
                    'scopes': ','.join(creds.scopes)
                }
            )

            #payload from jwt
            payload = {
                'user_id': user.id,
                'email': user.email,
                'exp': datetime.utcnow() + settings.JWT_SETTINGS['ACCESS_TOKEN_LIFETIME'],
            }

            #generate JWT token
            token = jwt.encode(payload, settings.JWT_SETTINGS['SIGNING_KEY'], algorithm=settings.JWT_SETTINGS['ALGORITHM'])

            return Response({'message': 'Login successful', 'Access token': token}, status=status.HTTP_200_OK)
        except:
            return Response({'message': 'An error occurred in the login process'}, status=status.HTTP_400_BAD_REQUEST)

def Create(request):
    pass