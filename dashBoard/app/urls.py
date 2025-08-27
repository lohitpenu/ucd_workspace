from django.urls import path
from . import views

urlpatterns = [
    # Define your URL patterns here
    path('', views.home, name='home'),
    path('process-image/', views.process_image_view, name='process_image'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
] 