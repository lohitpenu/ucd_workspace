from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
import time
import os

SCOPES = ['https://www.googleapis.com/auth/drive']
MAX_RETRIES = 3  # Number of retry attempts
RETRY_DELAY = 5  # Delay between retries in seconds

class GoogleDriveUploader:
    def __init__(self, service_account_file, parent_folder_id):
        self.service_account_file = service_account_file
        self.parent_folder_id = parent_folder_id
        self.creds = self.authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)

    def authenticate(self):
        return Credentials.from_service_account_file(self.service_account_file, scopes=SCOPES)

    def upload_photo(self, file_path):
        file_name = os.path.basename(file_path)  # Extract the file name from the path

        # Check if the file already exists in the Drive folder
        query = f"'{self.parent_folder_id}' in parents and name = '{file_name}' and trashed = false"
        try:
            response = self.service.files().list(q=query, spaces='drive').execute()
            if response.get('files', []):
                print(f"File '{file_name}' already exists in Google Drive. Skipping upload.")
                return
        except HttpError as error:
            print(f"Error checking if file exists: {error}")
            raise

        file_metadata = {
            'name': file_name,
            'mimeType': 'image/jpeg',  # Change this if you're uploading a different type of file
            'parents': [self.parent_folder_id]
        }

        for attempt in range(MAX_RETRIES):
            try:
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=file_path
                ).execute()
                print(f"File '{file_name}' uploaded successfully.")
                return file
            except HttpError as error:
                print(f"Attempt {attempt + 1} failed: {error}")
                if attempt < MAX_RETRIES - 1:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    print("Max retries reached. Upload failed.")
                    raise