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
        event_format['start']['dateTime'] = f'{event.get('start_date')}T{event.get('start_hour')}-03:00'
        event_format['end']['dateTime'] = f'{event.get('end_date')}T{event.get('end_hour')}-03:00'

        start_hour = event.get('start_hour')
        end_hour = event.get('end_hour')
    
    #is it recurring?
    if event.get('appellant') == True:
        event_format['recurrence'] = [event.get('recurrence')]

    try:
        #create the event on google calendar
        result = service.events().insert(calendarId='primary', body=event_format).execute()

        #create object in db
        Task.objects.create(
            id = result.get('id'),
            user = user,
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
            recurrence = event.get('recurrence')
        )

        return Response({'message': 'Event created successfully!', 'link': result.get('htmlLink')}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'message': f'Error creating event: {e}'}, status=status.HTTP_400_BAD_REQUEST)


#views that retrieve scheduled events do not retrieve all events
#from the user's calendar, only those created by the application
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def GetAllTasks(request):
    #search for all tasks belonging to the user making the request
    tasks = Task.objects.filter(user=request.user)
    tasks = TaskSerializer(tasks, many=True).data
    if tasks:
        return Response(tasks, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'User has no registered tasks'}, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def GetTask(request):
    try:
        #search the task by id
        task = Task.objects.get(id=request.data.get('id'))
        task = TaskSerializer(task).data

        #checks if the user requesting to view an event is the owner
        if task.get('user') != request.user.id:
            return Response({'message': 'The user does not have permission to view this task'}, status=status.HTTP_401_UNAUTHORIZED)
        elif task:
            return Response(task, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'This task does not exist or an error occurred in the request'}, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def Search(request):
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
        return Response({'message': 'User has no registered tasks'}, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
@api_view(['DELETE'])
def Delete(request):
    #check the existence of the event
    try:
        event = Task.objects.get(id=request.data.get('eventId'))
        event = TaskSerializer(event).data

        #if the event exists, check if the user has permission to delete it
        if event.get('user') != request.user.id:
            return Response({'message': "User does not have permission to delete the event"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            #if the user has permission to delete, redeem the Google Calendar token
            token = OAUTHToken.objects.get(user=request.user)
            token = OAUTHTokenSerializer(token).data.get('access_token')

            #create credentials from the token
            creds = Credentials(token=token)
            service = build('calendar', 'v3', credentials=creds)

            try:
                #delete the event from Google Calendar
                service.events().delete(calendarId='primary', eventId=request.data.get('eventId'), sendUpdates=request.data.get('sendUpdates')).execute()

                #exclude the event from the db
                Task.objects.get(id=request.data.get('eventId')).delete()

                #in the front end there should be a security question to check if the user really wants to delete the event
                return Response({'message': "The event was successfully deleted!"}, status=status.HTTP_200_OK)
            except:
                return Response({'message': "An error occurred when trying to delete the event"}, status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({'message': "The event does not exist or an error occurred in the request"}, status=status.HTTP_400_BAD_REQUEST)


#the update view, and delete view does not update the event if it
#is not created by the application
@permission_classes([IsAuthenticated])
@api_view(['PATCH'])
def Update(request):
    #retrieves data from the request
    user = request.user
    event = request.data

    try:
        #retrieves data from the database
        event_db = Task.objects.get(id=event.get('idTask'))
        event_db_info = TaskSerializer(event_db).data

        #user has permission to edit?
        if user.id == event_db_info.get('user'):
            event_format = {}
            
            #is there an edit in the title?
            if event.get('title'):
                event_db.title = event.get('title')
                event_format['summary'] = event.get('title')

            #is there an on-site edition?
            if event.get('locale'):
                event_db.locale = event.get('locale')
                event_format['locale'] = event.get('locale')

            #is there an edit in the description?
            if event.get('description'):
                event_db.description = event.get('description')
                event_format['description'] = event.get('description')

            #will the event be changed to an all-day event?
            if event.get('full_day') == True:
                event_db.full_day = event.get('full_day')
                #if there is a new start date in the request, edit
                if event.get('start_date'):
                    event_db.start_date = event.get('start_date')
                    event_format['start'] = {}
                    event_format['start']['timeZone'] = 'America/Sao_Paulo'
                    event_format['start']['date'] = event.get('start_date')
                
                #if there is a new end date in the request, edit
                if event.get('end_date'):
                    event_db.end_date = event.get('end_date')
                    event_format['start'] = {}
                    event_format['end']['timeZone'] = 'America/Sao_Paulo'
                    event_format['end']['date'] = event.get('end_date')
                
                #otherwise there is a new start or end date, take the one in the db
                if event.get('end_date') == None and event.get('start_date') == None:
                    start_date = event_db_info.get('start_date')
                    end_date = event_db_info.get('end_date')
                    event_format['start'] = {}
                    event_format['start']['timeZone'] = 'America/Sao_Paulo'
                    event_format['start']['date'] = start_date
                    event_format['end'] = {}
                    event_format['end']['timeZone'] = 'America/Sao_Paulo'
                    event_format['end']['date'] = end_date

            #will the event no longer be all day long?
            elif event.get('full_day') == False:
                event_db.full_day = event.get('full_day')
                #if there is a new start date, store it in a variable
                if event.get('start_date'):
                    event_db.start_date = event.get('start_date')
                    start_date = event.get('start_date')
                
                #if there is a new end date, store it in a variable
                if event.get('end_date'):
                    event_db.end_date = event.get('end_date')
                    end_date = event.get('end_date')

                #if there is no end or start date, the dates will be those of the db
                if event.get('end_date') == None and event.get('start_date') == None:
                    start_date = event_db_info.get('start_date')
                    end_date = event_db_info.get('end_date')
                
                #if there is a new start time, store it in a variable
                if event.get('start_hour'):
                    event_db.start_hour = event.get('start_hour')
                    start_hour = event.get('start_hour')

                #if there is a new end date, store it in a variable
                if event.get('end_date'):
                    event_db.end_date = event.get('end_date')
                    end_hour = event.get('end_hour')

                #if there is no new start or end date, it will be set as a default start at 09:00 and end at 10:00
                if event.get('end_date') == None and event.get('start_hour') == None:
                    start_hour = '09:00:00'
                    end_hour = '10:00:00'
                
                #format in the format accepted by Google calendar
                event_format['start'] = {}
                event_format['start']['timeZone'] = 'America/Sao_Paulo'
                event_format['start']['dateTime'] = f'{start_date}T{start_hour}-03:00'
                event_format['end'] = {}
                event_format['end']['timeZone'] = 'America/Sao_Paulo'
                event_format['end']['dateTime'] = f'{end_date}T{end_hour}-03:00'

            #want to add a new participant?
            if event.get('participants_add'):
                #db participants
                participants = event_db_info.get('participants')
                existing_emails = {p['email'] for p in participants}
                #search if the participant already exists in the db
                for participant in event.get('participants_add'):
                    #if the participant does not exist, insert
                    if participant['email'] not in existing_emails:
                        participants.append(participant)
                event_db.participants = event.get('participants')
                #format in the format accepted by Google Calendar
                event_format['attendees'] = participants

            #want to delete a participant?
            if event.get('participants_del'):
                participants = event_db_info.get('participants')
                #if the participant exists, delete it
                if event.get('participants_del') in participants:
                    participants.remove(event.get('participants_del'))
                event_db.participants = event.get('participants')
                #format in the format accepted by Google Calendar
                event_format['attendees'] = participants


            #Do you want to edit any notifications?
            if event.get('reminders_edit'):
                #db notifications
                reminders = event_db_info.get('reminders')
                for new_reminder in event.get('reminders_edit'):
                    # Remove any reminder with the same 'method' as the request
                    reminders = [r for r in reminders if r['method'] != new_reminder['method']]
                    # Add the new reminder
                    reminders.append(new_reminder)
                event_db.reminders = event.get('reminders')
                #format in the format that Google Calendar accepts
                event_format['reminders'] = {}
                event_format['reminders']['useDefault'] = False
                event_format['reminders']['overrides'] = reminders

            #Do you want to delete any notifications?
            if event.get('reminders_del'):
                #notificações do db
                reminders = event_db_info.get('reminders')
                #if the notification exists, delete it
                reminders = [r for r in reminders if r['method'] != event.get('reminders_del')]
                #format in the format accepted by Google Calendar
                event_db.reminders = event.get('reminders')
                event_format['reminders'] = {}
                event_format['reminders']['useDefault'] = False
                event_format['reminders']['overrides'] = reminders

            #want to add some notification?
            if event.get('reminders_add'):
                #db notifications
                reminders = event_db_info.get('reminders')
                #if the notification does not exist, insert
                for reminder_to_add in event.get('reminders_add'):
                    if not any(r['method'] == reminder_to_add['method'] for r in reminders):
                        reminders.append(reminder_to_add)
                        #format in the format accepted by Google Calendar
                event_db.reminders = event.get('reminders')
                event_format['reminders'] = {}
                event_format['reminders']['useDefault'] = False
                event_format['reminders']['overrides'] = reminders


            #want to change it to a non-recurring event?
            if event.get('appellant') and event.get('appellant') == False:
                event_db.appellant = False
                #remove the recurrence
                event_format['recurrence'] = []
            
            #want to change it to a recurring event?
            if event.get('appellant') and event.get('appellant') == True:
                event_db.appellant = True
                #define a recorrência
                event_format['recurrence'] = [event.get('appellant')]


            token = OAUTHToken.objects.get(user=user)
            #use the serializer to leave it in the correct format
            oauth_token = OAUTHTokenSerializer(token).data
            
            #from the db data, assemble the credentials to use in the Google Calendar request
            creds = Credentials(
                token = oauth_token.get("access_token"),
                refresh_token = oauth_token.get("refresh_token"),
                token_uri=oauth_token.get('token_uri'),
                client_id=oauth_token.get("client_id"),
                client_secret=oauth_token.get("client_secret"),
                scopes=oauth_token.get("scopes").split(','),
            )

            #define the service and credentials
            service = build('calendar', 'v3', credentials=creds)

            try:
                #update event
                result = service.events().patch(calendarId='primary', eventId=event.get('idTask'), body=event_format).execute()
                return Response({'message': 'Event edited successfully!', 'link': result.get('htmlLink')}, status=status.HTTP_200_OK)
            except:
                return Response({'message': 'An error occurred while editing the event'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'The user does not have permission to edit this task'}, status=status.HTTP_401_UNAUTHORIZED)
    except:
        return Response({'message': "The event does not exist or an error occurred in the request"}, status=status.HTTP_400_BAD_REQUEST)