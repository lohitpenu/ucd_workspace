# drive_app/urls.py

from django.urls import path
from . import views

#app_name = 'drive_app'


urlpatterns = [
    path('auth/', views.google_drive_auth, name='google_drive_auth'),
    path('oauth2callback', views.oauth2callback, name='oauth2callback'),
    path('upload/', views.upload_user_file, name='upload_user_file'),
    path('files/', views.list_drive_files, name='list_drive_files'),
    path('download/<str:file_id>/', views.download_file, name='download_file'),
    path('delete/<str:file_id>/', views.delete_file, name='delete_file'),
    path('search/', views.drive_search, name='drive_search')
]

