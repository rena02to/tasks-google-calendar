from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from django.contrib.auth import get_user_model
from datetime import datetime
from .models import OAUTHToken, Task
import pytz
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import OAUTHTokenSerializer, TaskSerializer
from google.oauth2.credentials import Credentials

User = get_user_model()

class Login(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/calendar']
        #definition of the Google API and what will be requested in the service
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

        try:
            #create the service to interact with the Google Calendar API

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
        except Exception as e:
            return Response({'message': f'An error occurred in the login process: {e}'}, status=status.HTTP_400_BAD_REQUEST)


class TasksView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
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

        #set up the event based on the request
        event_format = {
            'summary': event.get('title'),
            'location': event.get('locale'),
            'description': event.get('description'),
            'start': {
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'timeZone': 'America/Sao_Paulo',
            },
            'attendees': event.get('participants'),
            'reminders': {
                'useDefault': False,
                'overrides': event.get('reminders'),
            }
        }

        #is it an all-day event?
        if event.get('full_day') == True:
            event_format['start']['date'] = event.get('start_date')
            event_format['end']['date'] = event.get('end_date')

            start_hour = None
            end_hour = None
        else:
            if event.get('start_hour'):
                start_hour = event.get('start_hour')
            else:
                start_hour = "09:00:00"
            
            if event.get('end_hour'):
                end_hour = event.get('end_hour')
            else:
                end_hour = "10:00:00"
            
            event_format['start']['dateTime'] = f'{event.get('start_date')}T{start_hour}-03:00'
            event_format['end']['dateTime'] = f'{event.get('end_date')}T{end_hour}-03:00'

        
        #is it recurring?
        if event.get('appellant') == True:
            event_format['recurrence'] = [event.get('recurrence')]

        try:
            #create the event on google calendar
            result = service.events().insert(calendarId='primary', body=event_format).execute()

            #create object in db
            event['id'] = result.get('id')
            event['user'] = user.id
            serializer = TaskSerializer(data=event)

            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Event created successfully!', 'id': result.get('id'), 'link': result.get('htmlLink')}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': f'Error creating event: {e}'}, status=status.HTTP_400_BAD_REQUEST)
    

    #views that retrieve scheduled events do not retrieve all events
    #from the user's calendar, only those created by the application
    def get(self, request):
        if request.data.get('id'):
            try:
                #search the task by id
                task = Task.objects.get(user=request.user.id, id=request.data.get('id'))
                task = TaskSerializer(task).data
                return Response(task, status=status.HTTP_200_OK)
            except Task.DoesNotExist:
                return Response({'message:': 'This task does not exist'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'message': f'An error occurred in the request: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        elif request.GET.dict():
            try:
                #recovers all user events
                tasks = Task.objects.all()
                tasks = tasks.filter(user=request.user)

                #transforms the request url filters into a dictionary
                filters = request.GET.dict()

                #separate filters individually
                query = filters.get('q')
                date_start = filters.get('date_start')
                date_end = filters.get('date_end')
                locale = filters.get('locale')
                participants = filters.get('participants')
                
                #filter by search string, if any
                if query:
                    tasks = tasks.filter(title__icontains=query)
                
                #filter by the event start date, if any
                if date_start:
                    interval_start_date = date_start.split('|')[0]
                    interval_end_date = date_start.split('|')[1]
                    tasks = tasks.filter(start_date__range=(interval_start_date, interval_end_date))
                
                #filter by the event end date, if any
                if date_end:
                    interval_start_date = date_end.split('|')[0]
                    interval_end_date = date_end.split('|')[1]
                    tasks = tasks.filter(end_date__range=(interval_start_date, interval_end_date))

                #filter by location (location is a string, which can be the address), if it exists
                if locale:
                    tasks = tasks.filter(locale__icontains=locale)

                #filter by participants’ email, if any
                if participants:
                    tasks = [task for task in tasks if any(participants in participant.get('email', '') for participant in task.participants)]

                if tasks:
                    tasks = TaskSerializer(tasks, many=True).data
                    return Response(tasks, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'There are no tasks with the specified search parameters'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'message': f'An error occurred in the request: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            #search for all tasks belonging to the user making the request
            tasks = Task.objects.filter(user=request.user)
            tasks = TaskSerializer(tasks, many=True).data
            if tasks:
                return Response(tasks, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'User has no registered tasks'}, status=status.HTTP_404_NOT_FOUND)
            
    
    
    def delete(self, request):
        #check the existence of the event
        try:
            event = Task.objects.get(user=request.user.id, id=request.data.get('id'))

            #if the user has permission to delete, redeem the Google Calendar token
            token = OAUTHToken.objects.get(user=request.user)
            token = OAUTHTokenSerializer(token).data.get('access_token')

            #create credentials from the token
            creds = Credentials(token=token)
            service = build('calendar', 'v3', credentials=creds)

            try:
                #delete the event from Google Calendar
                service.events().delete(calendarId='primary', eventId=request.data.get('id'), sendUpdates=request.data.get('sendUpdates')).execute()

                #exclude the event from the db
                event.delete()

                #in the front end there should be a security question to check if the user really wants to delete the event
                return Response({'message': "The event was successfully deleted!"}, status=status.HTTP_200_OK)
            except:
                return Response({'message': "An error occurred when trying to delete the event"}, status=status.HTTP_400_BAD_REQUEST)
        except Task.DoesNotExist:
            return Response({'message': "The event does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': f"An error occurred in the request: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        

    #the update view, and delete view does not update the event if it
    #is not created by the application
    def patch(self, request):
        try:
            user = request.user
            event = request.data
            task = Task.objects.get(user=user.id, id=request.data.get('id'))

            token = OAUTHToken.objects.get(user=user)
            oauth_token = OAUTHTokenSerializer(token).data
            
            event = request.data
            creds = Credentials(
                token = oauth_token.get("access_token"),
                refresh_token = oauth_token.get("refresh_token"),
                token_uri=oauth_token.get('token_uri'),
                client_id=oauth_token.get("client_id"),
                client_secret=oauth_token.get("client_secret"),
                scopes=oauth_token.get("scopes").split(','),
            )

            service = build('calendar', 'v3', credentials=creds)

            event_format = {
                'summary': event.get('title'),
                'location': event.get('locale'),
                'description': event.get('description'),
                'start': {
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'timeZone': 'America/Sao_Paulo',
                },
                'attendees': event.get('participants'),
                'reminders': {
                    'useDefault': False,
                    'overrides': event.get('reminders'),
                }
            }

            if event.get('full_day') == True:
                event_format['start']['date'] = event.get('start_date')
                event_format['end']['date'] = event.get('end_date')

                start_hour = None
                end_hour = None
            else:
                if event.get('start_hour'):
                    start_hour = event.get('start_hour')
                else:
                    start_hour = "09:00:00"
                
                if event.get('end_hour'):
                    end_hour = event.get('end_hour')
                else:
                    end_hour = "10:00:00"
                event_format['start']['dateTime'] = f'{event.get('start_date')}T{start_hour}-03:00'
                event_format['end']['dateTime'] = f'{event.get('end_date')}T{end_hour}-03:00'
            if event.get('appellant') == True:
                event_format['recurrence'] = [event.get('recurrence')]

            event['user'] = user.id
            serializer = TaskSerializer(task, data=event)
            if serializer.is_valid():
                serializer.save()
                result = service.events().patch(calendarId='primary', eventId=event.get('id'), body=event_format).execute()
                return Response({'message': 'Event edited successfully!', 'link': result.get('htmlLink')}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Task.DoesNotExist:
            return Response({'message': "The event does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': f"An error occurred in the request: {e}"}, status=status.HTTP_400_BAD_REQUEST)