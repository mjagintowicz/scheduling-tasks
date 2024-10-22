# funkcje realizujące łączenie z kalendarzem

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


# POBIERANIE ZADAŃ Z KALENDARZA
def get_tasks_from_calendar():

    # logowanie
    creds = None

    if os.path.exists("token.json"):  # dane logowania zapisane w pliku
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:  # jeśli pliku nie ma - logowanie manualne
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:  # zapisz dane logowania do pliku
            token.write(creds.to_json())

    # pobieranie zadań (gcsa???)
    # ...

    tasks_obtained = True

    if HttpError:
        tasks_obtained = False

    return tasks_obtained




