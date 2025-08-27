import os
import pathlib
import io
import json, requests
from django.http import JsonResponse, HttpResponse


from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.conf import settings
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from django.shortcuts import render
from .forms import UploadFileForm
from django.views.decorators.csrf import csrf_exempt
from .utils import upload_to_google_drive, ensure_drive_authenticated, process_image_and_upload



from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
REDIRECT_URI = 'http://localhost:8000/oauth2callback'


def google_drive_auth(request):
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    #request.session['flow'] = flow.credentials_to_dict()
    return HttpResponseRedirect(auth_url)


""" def oauth2callback(request):
    state = request.GET.get('state')
    code = request.GET.get('code')

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    request.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect('list_drive_files')
    #return HttpResponse("Google Drive linked successfully!") """

def oauth2callback(request):
    code = request.GET.get('code')
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials
    request.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    #return HttpResponse("<script>window.close();</script>")  # closes popup
    #return HttpResponse('<html><body><script>window.close();</script><p>Authentication complete. You can close this window.</p></body></html>')
    return HttpResponse("""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Authentication Complete</title>
        <script>
            setTimeout(function() {
                window.location.href = '/'; // change '/' if your home URL is different
            }, 2000);
        </script>
    </head>
    <body>
        <p>Authentication complete. Redirecting to home page in 2 seconds...</p>
    </body>
    </html>
""")


def upload_file(request):
    if 'credentials' not in request.session:
        return redirect('google_drive_auth')

    creds = Credentials(**request.session['credentials'])
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': 'test.txt'}
    media = MediaFileUpload('test.txt', mimetype='text/plain')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    return HttpResponse(f'Uploaded file with ID: {file.get("id")}') 


"""def list_drive_files(request):
    if 'credentials' not in request.session:
        return redirect('google_drive_auth')

    creds = Credentials(**request.session['credentials'])
    service = build('drive', 'v3', credentials=creds)

    results = service.files().list(pageSize=20, fields="files(id, name, mimeType)").execute()
    items = results.get('files', [])

    return render(request, 'drive_app/drive_list.html', {'files': items})"""

def list_drive_files(request):
    if 'credentials' not in request.session:
        return render(request, 'drive_app/drive_not_connected.html')

    creds = Credentials(**request.session['credentials'])
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(pageSize=20, fields="files(id, name, mimeType)").execute()
    items = results.get('files', [])
    return render(request, 'drive_app/drive_list.html', {'files': items})


@csrf_exempt
# def upload_user_file(request):
#     # Allow processing requests from another views.py via POST with credentials in session
#     if 'credentials' not in request.session:
#         return redirect('google_drive_auth')

#     # Support both direct form POST and API-style POST (e.g., from another view)
#     if request.method == 'POST':
#         # Check if file is in request.FILES (form upload) or in request.POST (API call)
#         if 'file' in request.FILES:
#             file = request.FILES['file']
#             creds = Credentials(**request.session['credentials'])
#             service = build('drive', 'v3', credentials=creds)

#             media = MediaIoBaseUpload(file.file, mimetype=file.content_type)
#             file_metadata = {'name': file.name}
#             uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

#             return HttpResponse(f"File uploaded: {uploaded_file.get('id')}")
#         elif 'file_content' in request.POST and 'file_name' in request.POST:
#             # Handle API-style POST with file content and name in POST data
#             file_content = request.POST['file_content']
#             file_name = request.POST['file_name']
#             creds = Credentials(**request.session['credentials'])
#             service = build('drive', 'v3', credentials=creds)

#             file_stream = io.BytesIO(file_content.encode())
#             media = MediaIoBaseUpload(file_stream, mimetype='application/octet-stream')
#             file_metadata = {'name': file_name}
#             uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

#             return HttpResponse(f"File uploaded: {uploaded_file.get('id')}")
#         else:
#             form = UploadFileForm(request.POST, request.FILES)
#             return render(request, 'drive_app/upload.html', {'form': form, 'error': 'No file provided.'})
#     else:
#         form = UploadFileForm()

#     return render(request, 'drive_app/upload.html', {'form': form})

def upload_user_file(request):
    # if 'credentials' not in request.session:
    #     return redirect('google_drive_auth')
    auth_check = ensure_drive_authenticated(request, api_mode=False)
    if auth_check:
        return auth_check

    if request.method == 'POST':
        if 'file' in request.FILES:
            file = request.FILES['file']
            file_id = upload_to_google_drive(
                request.session['credentials'],
                file.name,
                file.file,
                file.content_type
            )
            return HttpResponse(f"File uploaded: {file_id}")

        elif 'file_content' in request.POST and 'file_name' in request.POST:
            file_stream = io.BytesIO(request.POST['file_content'].encode())
            file_id = upload_to_google_drive(
                request.session['credentials'],
                request.POST['file_name'],
                file_stream,
                'application/octet-stream'
            )
            return HttpResponse(f"File uploaded: {file_id}")

        else:
            form = UploadFileForm(request.POST, request.FILES)
            return render(request, 'drive_app/upload.html', {'form': form, 'error': 'No file provided.'})
    else:
        form = UploadFileForm()
        return render(request, 'drive_app/upload.html', {'form': form})
    

def download_file(request, file_id):
    if 'credentials' not in request.session:
        return redirect('google_drive_auth')

    creds = Credentials(**request.session['credentials'])
    service = build('drive', 'v3', credentials=creds)

    request_file = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request_file)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)
    file_meta = service.files().get(fileId=file_id, fields='name').execute()
    filename = file_meta['name']

    response = HttpResponse(fh.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def delete_file(request, file_id):
    if 'credentials' not in request.session:
        return redirect('google_drive_auth')

    creds = Credentials(**request.session['credentials'])
    service = build('drive', 'v3', credentials=creds)

    service.files().delete(fileId=file_id).execute()
    return redirect('list_drive_files')


def drive_search(request):
    if 'credentials' not in request.session:
        return redirect('google_drive_auth')
    
    if request.method == "POST":
        from_date = request.POST.get('fromDate')
        to_date = request.POST.get('toDate')
        creds = Credentials(**request.session['credentials'])
        service = build('drive', 'v3', credentials=creds)

        # Google Drive uses RFC 3339 date format (e.g., 2024-06-01T00:00:00)
        from_date_str = f"{from_date}T00:00:00" if from_date else None
        to_date_str = f"{to_date}T23:59:59" if to_date else None

        query_parts = []
        if from_date_str:
            query_parts.append(f"modifiedTime >= '{from_date_str}'")
        if to_date_str:
            query_parts.append(f"modifiedTime <= '{to_date_str}'")
        query = " and ".join(query_parts) if query_parts else None

        results = service.files().list(
            q=query,
            pageSize=1000,
            fields="files(id, name, mimeType, modifiedTime, webContentLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives'
        ).execute()

        items = results.get('files', [])
        items.sort(key=lambda x: x['name'])  # Sort by name
        pretty_json_string = json.dumps(items, indent=4) 
        print(pretty_json_string)

        #This is to reset the image processing service each time search happens
        reset_url = "http://167.99.135.60:8080/reset/"
        data = {"token": "auth_hard_reset"}
        response = requests.post(reset_url, data=data)
        if response.status_code != 200:
            return JsonResponse({'error': 'Failed to reset the image processing service.'}, status=500)
        else:
            print("Image processing service reset successfully.")  
            
        # Download images locally
        local_files = []
        for file in items:
            if file['mimeType'].startswith('image/'):
                local_path = os.path.join(settings.MEDIA_ROOT, file['name'])
                result = process_image_and_upload(request.session['credentials'], file['webContentLink'], imgName=file['name'])
                if 'file_id' in result:
                    print(f"Image {file['name']} processed and uploaded with ID: {result['file_id']}")
                # Avoid downloading if already exists
                if not os.path.exists(local_path):
                    request_file = service.files().get_media(fileId=file['id'])
                    fh = io.BytesIO()
                    downloader = MediaIoBaseDownload(fh, request_file)

                    done = False
                    while not done:
                        status, done = downloader.next_chunk()

                    fh.seek(0)
                    with open(local_path, 'wb') as f:
                        f.write(fh.read())

                # Add local path to file dict
                file['local_url'] = settings.MEDIA_URL + file['name']
            else:
                file['local_url'] = None

            local_files.append(file)

        return render(request, 'drive_app/drive_search.html', {
            'files': local_files,
            'from_date': from_date,
            'to_date': to_date
        })

    else:
        return HttpResponse("Please submit the form.")


""" def drive_search(request):
    if 'credentials' not in request.session:
        return redirect('google_drive_auth')
    
    if request.method == "POST":
        from_date = request.POST.get('fromDate')
        to_date = request.POST.get('toDate')
        creds = Credentials(**request.session['credentials'])
        service = build('drive', 'v3', credentials=creds)

        # Google Drive uses RFC 3339 date format (e.g., 2024-06-01T00:00:00)
        from_date_str = f"{from_date}T00:00:00" if from_date else None
        to_date_str = f"{to_date}T23:59:59" if to_date else None

        query_parts = []
        if from_date_str:
            query_parts.append(f"modifiedTime >= '{from_date_str}'")
        if to_date_str:
            query_parts.append(f"modifiedTime <= '{to_date_str}'")
        # Do NOT add any mimeType filter
        query = " and ".join(query_parts) if query_parts else None

        results = service.files().list(
            q=query,
            pageSize=1000,
            fields="files(id, name, mimeType, modifiedTime, webViewLink, webContentLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives'
        ).execute()
        items = results.get('files', [])
        print(f"Search query: {query}, Found items: {len(items)}, Results: {results}")

        return render(request, 'drive_app/drive_search.html', {'files': items, 'from_date': from_date, 'to_date': to_date})
    else:
        return HttpResponse("Please submit the form.") """
