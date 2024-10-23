# funkcje realizujące łączenie z kalendarzem

import datetime
import os.path

#from google.auth.transport.requests import Request
#from google.oauth2.credentials import Credentials
#from google_auth_oauthlib.flow import InstalledAppFlow
#from googleapiclient.discovery import build
#from googleapiclient.errors import HttpError

from gcsa.google_calendar import GoogleCalendar

from PyQt6.QtWidgets import QDateEdit, QTimeEdit

from beautiful_date import *

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


# POBIERANIE ZADAŃ Z KALENDARZA
def get_tasks_from_calendar(begin_date, end_date, begin_time, end_time):

    # logowanie
    gc = None

    if os.path.exists("token.pickle"):  # jeśli dane logowania zapisane w pliku (nie jest to pierwsze logowanie)
        gc = GoogleCalendar(credentials_path="credentials.json", token_path="token.pickle")

    if not gc:  # jeśli pliku nie ma - logowanie manualne
        gc = GoogleCalendar(credentials_path="credentials.json", save_token=True)

    if not gc:
        return False

    # edycja dat do wymaganego formatu
    begin_date_time = (D @ begin_date.day()/begin_date.month()/begin_date.year())[begin_time.hour():begin_time.minute()]
    end_date_time = (D @ end_date.day()/end_date.month()/end_date.year())[end_time.hour():end_time.minute()]

    # eventy się pobierają (trzeba odświeżać token co jakiś czas)
    # ...
    events = list(gc.get_events(time_min=begin_date_time, time_max=end_date_time))

    return True




