from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import io
from django.http import JsonResponse, HttpResponse
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
import json
from django.shortcuts import redirect, render
from drive_app.views import upload_user_file, list_drive_files, download_file, delete_file
from django.contrib.auth import logout
from  drive_app.utils import upload_to_google_drive, ensure_drive_authenticated, process_image_and_upload



# Create your views here.
def home(request):
    return render(request, 'home.html')

@csrf_exempt
def process_image_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed.'}, status=405)

    auth_check = ensure_drive_authenticated(request, api_mode=True)
    if auth_check:
        return auth_check

    image_url = request.POST.get('image_url')
    if not image_url:
        return JsonResponse({'error': 'Missing image_url parameter.'}, status=400)

    try:
        result = process_image_and_upload(request.session['credentials'], image_url)
        return JsonResponse(result)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'RequestException: {e}'}, status=502)
    except IOError as e:
        return JsonResponse({'error': f'IOError: {e}'}, status=500)

def logout_view(request):
    from django.contrib.auth import logout
    creds = request.session.get('credentials')
    if creds and 'token' in creds:
        requests.post(
            'https://oauth2.googleapis.com/revoke',
            params={'token': creds['token']},
            headers={'content-type': 'application/x-www-form-urlencoded'}
        )
    request.session.flush()  # Clears all session data
    logout(request)
    return render(request, 'logged_out.html')

def login_view(request):
    """
    Redirects to Google Drive authentication.
    """
    if 'credentials' in request.session:
        # If already authenticated, redirect to home or another page
        return redirect('home')
    # Redirect to Google Drive authentication
    return redirect('google_drive_auth')  # Assuming 'google_drive_auth' is defined in drive_app.urls