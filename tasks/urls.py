from django.urls import path
from .views import Create, Login, GetAllTasks, GetTask, Update, Delete, Search

urlpatterns = [
    path('login/', Login.as_view(), name="login"),
    path('create/', Create, name="create"),
    path('get_all_tasks/', GetAllTasks, name="get_all_tasks"),
    path('get_task/', GetTask, name="get_task"),
    path('update/', Update, name="update"),
    path('delete/', Delete, name="delete"),
    path('search/', Search, name="search"),
]

#views that retrieve scheduled events do not retrieve all events
#from the user's calendar, only those created by the application

#the update view, and delete view does not update the event if it
#is not created by the application