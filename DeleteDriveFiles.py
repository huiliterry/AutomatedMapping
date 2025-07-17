import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import DownloadTool

# Scope needed for full Drive access
SCOPES = ['https://www.googleapis.com/auth/drive']

# load credentials and token, return servive object
def authenticate_drive():
    creds = None
    if os.path.exists('/home/hli47/InseasonMapping/KEY/token.json'):
        creds = Credentials.from_authorized_user_file('/home/hli47/InseasonMapping/KEY/token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('/home/hli47/InseasonMapping/KEY/deleteDriveCredential.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('/home/hli47/InseasonMapping/KEY/token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

# search folder matching the input folder name
def get_folder_id_by_name(service, folder_name):
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    if not folders:
        print(f"No folder named '{folder_name}' found.")
        return None
    print(f"Found folder '{folder_name}' with ID: {folders[0]['id']}")
    return folders[0]['id']  # Return the first match

def delete_all_files_in_folder(service, folder_id):
    files = DownloadTool.list_all_files_in_folder(service, folder_id)
    print('files',len(files))

    if not files:
        return

    deleted_count = 0
    for file in files:
        try:
            service.files().delete(fileId=file['id']).execute()
            deleted_count += 1
            # print(f"Deleted: {file['name']}")
        except Exception as e:
            print(f"Failed to delete {file['name']}: {e}")
    
    print(f'{deleted_count} files were deleted')


# Run everything
def delete_drive_files(folder_name):
    drive_service = authenticate_drive()
    folder_id = get_folder_id_by_name(drive_service, folder_name)
    if folder_id:
        delete_all_files_in_folder(drive_service, folder_id)
