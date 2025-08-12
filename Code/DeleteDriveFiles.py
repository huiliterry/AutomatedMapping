import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import DownloadTool


# Scope needed for full Drive access
SCOPES = ['https://www.googleapis.com/auth/drive']


# load credentials and token, return servive object
def authenticate_drive():
    """
    Authenticate and return a Google Drive API service object.

    This function uses OAuth 2.0 credentials to connect to Google Drive.
    If a saved token exists (`token.json`), it is used directly; otherwise,
    it launches a local browser flow to authenticate the user and store the
    token for future use.

    Google Cloud setting and API install (important)
    Set Up Google Drive API
    - Go to: https://console.developers.google.com
    - Enable Google Drive API
    - Create OAuth 2.0 credentials and download the credentials.json file
    Install Required Packages
    - conda install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

    Returns
    -------
    googleapiclient.discovery.Resource
        An authenticated Google Drive API service object.

    Notes
    -----
    - Requires `google-api-python-client`, `google-auth-oauthlib`, and `google-auth`.
    - The token is stored at:
      `/home/hli47/InseasonMapping/KEY/token.json`
    - The OAuth client secret file should be:
      `/home/hli47/InseasonMapping/KEY/deleteDriveCredential.json`
    """
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
    """
    Retrieve the Google Drive folder ID by folder name.

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        An authenticated Google Drive API service object.
    folder_name : str
        The name of the folder to search for.

    Returns
    -------
    str or None
        The folder ID if found, otherwise None.

    Notes
    -----
    - If multiple folders have the same name, this returns the first match.
    - Only non-trashed folders are considered.
    """
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    if not folders:
        print(f"No folder named '{folder_name}' found.")
        return None
    print(f"Found folder '{folder_name}' with ID: {folders[0]['id']}")
    return folders[0]['id']  # Return the first match

# delete files in the folder
def delete_all_files_in_folder(service, folder_id):
    """
    Delete all files inside a Google Drive folder (recursively).

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
        An authenticated Google Drive API service object.
    folder_id : str
        The ID of the folder whose contents should be deleted.

    Notes
    -----
    - Uses `DownloadTool.list_all_files_recursive(service, folder_id)`
      to retrieve file metadata.
    - Skips deletion if no files are found.
    - Prints the name of each deleted file.
    """
    files = DownloadTool.list_all_files_recursive(service, folder_id)
    print('files',len(files))

    if not files:
        return

    deleted_count = 0
    for file in files:
        try:
            service.files().delete(fileId=file['id']).execute()
            deleted_count += 1
            print(f"Deleted: {file['name']}")
        except Exception as e:
            print(f"Failed to delete {file['name']}: {e}")
    
    print(f'{deleted_count} files were deleted')


# Run everything
def delete_drive_files(folder_name):
    """
    Authenticate and delete all files inside a Google Drive folder by name.

    Parameters
    ----------
    folder_name : str
        The name of the Google Drive folder to clean.

    Workflow
    --------
    1. Authenticate with Google Drive API.
    2. Search for the folder ID by name.
    3. If found, delete all files inside the folder (recursively).

    Example
    -------
    >>> delete_drive_files("OldProjectBackups")
    Found folder 'OldProjectBackups' with ID: 12345abcdef
    Deleted: backup1.zip
    Deleted: backup2.zip
    2 files were deleted
    """
    drive_service = authenticate_drive()
    folder_id = get_folder_id_by_name(drive_service, folder_name)
    if folder_id:
        delete_all_files_in_folder(drive_service, folder_id)

