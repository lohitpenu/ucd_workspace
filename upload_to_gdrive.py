from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
import time
import os

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'
PARENT_FOLDER_ID = "1VJ4WWoZ_trILQRo6EcVqRnbHotNC_5ho"
MAX_RETRIES = 3  # Number of retry attempts
RETRY_DELAY = 5  # Delay between retries in seconds

def authenticate():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return creds

def upload_photo(file_path):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    file_name = file_path.split('/')[-1]  # Extract the file name from the path

    # Check if the file already exists in the Drive folder
    query = f"'{PARENT_FOLDER_ID}' in parents and name = '{file_name}' and trashed = false"
    try:
        response = service.files().list(q=query, spaces='drive').execute()
        if response.get('files', []):
            print(f"File '{file_name}' already exists in Google Drive. Skipping upload.")
            return
    except HttpError as error:
        print(f"Error checking if file exists: {error}")
        raise

    file_metadata = {
        'name': file_name,
        'mimeType': 'image/jpeg',  # Change this if you're uploading a different type of file
        'parents': [PARENT_FOLDER_ID]
    }

    for attempt in range(MAX_RETRIES):
        try:
            file = service.files().create(
                body=file_metadata,
                media_body=file_path
            ).execute()
            print("File uploaded successfully.")
            return file
        except HttpError as error:
            print(f"Attempt {attempt + 1} failed: {error}")
            if attempt < MAX_RETRIES - 1:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print("Max retries reached. Upload failed.")
                raise

if __name__ == "__main__":
    # Example usage
    folder_path = "/home/lohit/phd_workspace/stageOne_testSet"  # Replace with your folder path
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):  # Ensure it's a file
            try:
                upload_photo(file_path)
            except Exception as e:
                print(f"Failed to upload {file_name}: {e}")

