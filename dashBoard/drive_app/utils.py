# drive_app/utils.py
import io, requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from django.shortcuts import redirect
from django.http import JsonResponse

# def upload_to_google_drive(credentials_dict, file_name, file_stream, mime_type):
#     creds = Credentials(**credentials_dict)
#     service = build('drive', 'v3', credentials=creds)

#     media = MediaIoBaseUpload(file_stream, mimetype=mime_type)
#     file_metadata = {'name': file_name}
#     uploaded_file = service.files().create(
#         body=file_metadata,
#         media_body=media,
#         fields='id'
#     ).execute()
#     return uploaded_file.get('id')

# drive_app/utils.py
def upload_to_google_drive(credentials_dict, file_name, file_stream, mime_type, folder_id=None):
    creds = Credentials(**credentials_dict)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]  # upload inside folder

    media = MediaIoBaseUpload(file_stream, mimetype=mime_type)
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return uploaded_file.get('id')



def process_image_and_upload(credentials_dict, image_url, imgName=None):
    """
    Calls the external image processing API, uploads the resulting ZIP to Drive,
    and returns (message, file_id, drive_link).
    """
    url = "http://167.99.135.60:8080/process_image/"
    files = {'url': (None, image_url)}
    headers = {'accept': 'application/json, application/zip'}

    response = requests.post(url, headers=headers, files=files, stream=True)
    response.raise_for_status()
    content_type = response.headers.get('content-type')

    if imgName is None:
        imgName = image_url.split('/')[-1].split('.')[0] + "_processed"
    else:
        imgName = imgName.split('.')[0]

    if content_type == 'application/json':
        return {'json_response': response.json()}

    elif content_type == 'application/zip':
        zip_buffer = io.BytesIO(response.content)
        zip_buffer.seek(0)
        file_id = upload_to_google_drive(
            credentials_dict,
            imgName + ".zip",
            zip_buffer,
            "application/zip",
            folder_id="1bXPYVbXAMqcfEX1kqPWOOlpc2itG5pmh"
        )
        return {
            'message': 'ZIP uploaded to Google Drive successfully.',
            'file_id': file_id,
            'drive_link': f"https://drive.google.com/file/d/{file_id}/view"
        }
    else:
        raise ValueError("Unexpected content type from processing API")


def ensure_drive_authenticated(request, api_mode=False):
    """
    Ensures Google Drive credentials exist in the session.
    If missing:
        - In API mode: returns JSON error.
        - In browser mode: redirects to Google auth view.
    """
    if 'credentials' not in request.session:
        if api_mode:
            return redirect('google_drive_auth')
        else:
            return redirect('google_drive_auth')
    return None


