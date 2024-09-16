from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from .models import OAUTHToken, Task
import pytz
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import OAUTHTokenSerializer
from google.oauth2.credentials import Credentials

User = get_user_model()

class Login(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/calendar']
        #definition of the Google API and what will be requested in the service
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

        try:
            #cria o serviço para interagir com a API do Google Calendar

            ##############     trocar a porta no último commit    ##############

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
                defaults = {
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

            #jwt
            token = RefreshToken.for_user(user)
            token = str(token.access_token)

            return Response({'message': 'Login successful', 'Access token': token}, status=status.HTTP_200_OK)
        except:
            return Response({'message': 'An error occurred in the login process'}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
@api_view(['POST'])
def Create(request):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    #retrieves data from the database
    user = request.user
    token = OAUTHToken.objects.get(user=user)
    #use the serializer to leave it in the correct format
    oauth_token = OAUTHTokenSerializer(token).data
    
    event = request.data

    #from the db data, assemble the credentials to use in the Google Calendar request
    creds = Credentials(
        token = oauth_token.get("access_token"),
        refresh_token = oauth_token.get("refresh_token"),
        token_uri=oauth_token.get('token_uri'),
        client_id=oauth_token.get("client_id"),
        client_secret=oauth_token.get("client_secret"),
        scopes=oauth_token.get("scopes").split(','),
    )

    #create the service to interact with the Google Calendar API
    service = build('calendar', 'v3', credentials=creds)

    #is it an all-day event?
    if event.get('full_day') == True:
        start_hour = None
        end_hour = None
        start = event.get('start_date')
        end = event.get('end_date')
    else:
        start_hour = event.get('start_hour')
        end_hour = event.get('end_hour')
        start = f'{event.get('start_date')}T{event.get('start_hour')}-03:00'
        end = f'{event.get('end_date')}T{event.get('end_hour')}-03:00'
    
    #is it recurring?
    if event.get('appellant') == True:
        recurrence = event.get('recurrence')
    else:
        recurrence = None

    #set up the event based on the request
    event_format = {
        'summary': event.get('title'),
        'location': event.get('locale'),
        'description': event.get('description'),
        'start': {
            'dateTime': start,
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': end,
            'timeZone': 'America/Sao_Paulo',
        },
        'attendees': event.get('participants'),
        'reminders': {
            'useDefault': False,
            'overrides': event.get('reminders'),
        },
        'recurrence': [
            recurrence
        ],
    }

    try:
        #create the event on google calendar
        result = service.events().insert(calendarId='primary', body=event_format).execute()

        #create object in db
        Task.objects.create(
            id = result.get('id'),
            title = event.get('title'),
            locale = event.get('locale'),
            full_day = event.get('full_day'),
            description = event.get('description'),
            start_date = event.get('start_date'),
            start_hour = start_hour,
            end_date = event.get('end_date'),
            end_hour = end_hour,
            participants = event.get('participants'),
            reminders = event.get('reminders'),
            appellant = event.get('appellant'),
            recurrence = recurrence
        )

        return Response({'message': 'Event created successfully!', 'link': result.get('htmlLink')}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'message': f'Error creating event: {e}'}, status=status.HTTP_400_BAD_REQUEST)