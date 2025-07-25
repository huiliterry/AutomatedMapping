import os
import io
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


# Access all files in a specific folder of Google Drive
def list_all_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    files = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            spaces='drive',
            fields="nextPageToken, files(id, name)",
            pageSize=1000,
            pageToken=page_token
        ).execute()

        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)

        if page_token is None:
            break

    return files

# A recursive file search
def list_all_files_recursive(service, folder_id):
    all_files = []
    stack = [folder_id]

    while stack:
        current_id = stack.pop()
        query = f"'{current_id}' in parents and trashed=false"
        response = service.files().list(
            q=query,
            spaces='drive',
            fields="files(id, name, mimeType)",
            pageSize=1000
        ).execute()

        for f in response.get('files', []):
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                stack.append(f['id'])  # recurse into subfolders
            else:
                all_files.append(f)
    return all_files


# create service account key in Google Cloud, download key .json, share downloadable folders to created service account
def downloadfiles_byserviceaccout(target_name, local_folder):
    # Load your service account key
    SERVICE_ACCOUNT_FILE = '/home/hli47/InseasonMapping/KEY/ee-huil7073-0802b07b2350.json'
    # SERVICE_ACCOUNT_FILE= os.path.join("..","KEY",'ee-huil7073-81b7212a3bd2.json')
    SCOPES = ['https://www.googleapis.com/auth/drive']

    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    drive_service = build('drive', 'v3', credentials=creds)

    # List shared folders
    results = drive_service.files().list(q=f"name = '{target_name}' and trashed = false", pageSize=10, fields="files(id, name)").execute()
    print('results',results.get('files'))

    # search and download each file in every folder
    download_file_number = 0
    for f in results['files']:
        folder_name = f['name']
        folder_id = f['id']
        print("folder_id",folder_id)
        
        # create local folder 
        local_file_path = os.path.join(local_folder, folder_name)
        os.makedirs(local_file_path, exist_ok=True)
        print('local_file_path',local_file_path)

        # Search for all files in this Drive folder
        filesList = list_all_files_recursive(drive_service, folder_id)
        print('filesList',len(filesList))
        if len(filesList) == 0:
             break

        for i, file_obj in enumerate(filesList):
                file_title = file_obj['name']
                file_id = file_obj['id']
                print(f"{i+1}. {file_title} ({file_id})")
                local_file_name = os.path.join(local_file_path, file_title)

                request = drive_service.files().get_media(fileId=file_id)
                fh = io.FileIO(local_file_name, 'wb')
                downloader = MediaIoBaseDownload(fh, request)
                download_file_number += 1
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print(f"Download {int(status.progress() * 100)}%.")
                time.sleep(1)

        print(f"{download_file_number} files were downloaded to: {local_file_path}")

