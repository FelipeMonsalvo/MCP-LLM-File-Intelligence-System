from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os, pickle

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

_TARGET_FOLDERS = None

def get_drive_service():
    creds = None
    token_path = "token.pickle"

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def get_first_5_folders(service):
    global _TARGET_FOLDERS
    
    if _TARGET_FOLDERS is not None:
        return [folder["id"] for folder in _TARGET_FOLDERS]
    
    try:
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=5,
            fields="files(id, name)",
            orderBy="modifiedTime desc"
        ).execute()
        
        folders = results.get("files", [])
        _TARGET_FOLDERS = [{"id": folder["id"], "name": folder.get("name", "Unknown")} for folder in folders]
        
        return [folder["id"] for folder in _TARGET_FOLDERS]
    except Exception as e:
        print(f"Error fetching folders: {e}")
        return []


def get_first_5_folders_with_names(service):
    global _TARGET_FOLDERS
    
    if _TARGET_FOLDERS is not None:
        return _TARGET_FOLDERS
    
    get_first_5_folders(service)
    return _TARGET_FOLDERS if _TARGET_FOLDERS else []


def find_folder_by_name(service, folder_name):
    try:
        folders = get_first_5_folders_with_names(service)
        for folder in folders:
            if folder.get("name", "").lower() == folder_name.lower():
                return folder["id"]

        return None

    except Exception as e:
        print(f"Error finding folder by name: {e}")
        return None
