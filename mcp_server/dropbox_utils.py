import os
import dropbox

from dotenv import load_dotenv
load_dotenv()

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN", "").strip()

_TARGET_FOLDERS = None


def get_dropbox_client():
    if not DROPBOX_ACCESS_TOKEN:
        raise RuntimeError(
            "DROPBOX_ACCESS_TOKEN is missing. Add it to mcp_server/.env"
        )
    try:
        return dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    except Exception as e:
        raise RuntimeError(f"Error creating Dropbox client: {e}")


def get_first_5_folders(dbx):
    global _TARGET_FOLDERS

    if _TARGET_FOLDERS is not None:
        return [folder["id"] for folder in _TARGET_FOLDERS]

    try:
        _TARGET_FOLDERS = []
        result = dbx.files_list_folder(path="", recursive=False)

        for entry in result.entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                _TARGET_FOLDERS.append({
                    "id": entry.path_lower,
                    "name": entry.name
                })
                if len(_TARGET_FOLDERS) >= 5:
                    break

        return [folder["id"] for folder in _TARGET_FOLDERS]

    except Exception as e:
        print(f"Error fetching Dropbox folders: {e}")
        return []


def get_first_5_folders_with_names(dbx):
    global _TARGET_FOLDERS

    if _TARGET_FOLDERS is not None:
        return _TARGET_FOLDERS

    get_first_5_folders(dbx)
    return _TARGET_FOLDERS if _TARGET_FOLDERS else []


def find_folder_by_name(dbx, name):
    normalized = name.lower()
    normalized_path = name if name.startswith("/") else f"/{name}"
    normalized_path = normalized_path.lower()

    try:
        result = dbx.files_list_folder("", recursive=False)
    except Exception:
        return None

    for entry in result.entries:
        if isinstance(entry, dropbox.files.FolderMetadata):
            if (
                entry.name.lower() == normalized
                or entry.path_lower == normalized_path
            ):
                return entry.path_lower

    return None