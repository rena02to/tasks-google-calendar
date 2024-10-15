from django.urls import path
from .views import Login, TasksListView, TasksDetailView

urlpatterns = [
    path('login/', Login.as_view(), name="login"),
    path('task/', TasksListView.as_view(), name="task-list"),
    path('task/<str:id>/', TasksDetailView.as_view(), name="task-detail"),
]

#views that retrieve scheduled events do not retrieve all events
#from the user's calendar, only those created by the application

#the update view, and delete view does not update the event if it
#is not created by the application