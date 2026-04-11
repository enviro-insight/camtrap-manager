import os
import re
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

DOWNLOAD_DIR = Path("20260319") # use the download date as these files are updated regularly

# Regex pattern for filenames
# Example: r"camera.*_"
NAME_REGEX = r"camera.*_"

# Compile once
name_pattern = re.compile(NAME_REGEX, re.IGNORECASE)

# Case sensitivity for the filename filter
CASE_SENSITIVE = False


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.rstrip(" .")
    return name or "unnamed_file"


def name_matches(filename: str) -> bool:
    return bool(name_pattern.search(filename))


def get_drive_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def list_root_google_sheets(service):
    page_token = None

    query = (
        "'root' in parents "
        "and trashed = false "
        "and mimeType = 'application/vnd.google-apps.spreadsheet'"
    )

    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=100,
            pageToken=page_token,
        ).execute()

        for file in response.get("files", []):
            yield file

        page_token = response.get("nextPageToken")
        if not page_token:
            break


def export_sheet_as_csv(service, file_id: str, destination: Path):
    request = service.files().export_media(fileId=file_id, mimeType="text/csv")

    with open(destination, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"    {int(status.progress() * 100)}%")


def main():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    service = get_drive_service()

    found_any = False
    downloaded_any = False

    for file in list_root_google_sheets(service):
        found_any = True
        file_name = file["name"]

        if not name_matches(file_name):
            continue

        downloaded_any = True

        safe_name = sanitize_filename(file_name)
        destination = DOWNLOAD_DIR / f"{safe_name}.csv"

        print(f"Exporting: {file_name}")
        print(f"  Saving as: {destination.name}")

        export_sheet_as_csv(service, file["id"], destination)

        print("  Done.\n")

    if not found_any:
        print("No Google Sheets found directly in My Drive root.")
    elif not downloaded_any:
        print("Google Sheets were found in root, but none matched the name filter.")
    else:
        print(f"Finished. Files saved to: {DOWNLOAD_DIR.resolve()}")

if __name__ == "__main__":
    main()