# funkcje realizujące łączenie z kalendarzem

import datetime
import os.path

from typing import Tuple, List

#from google.auth.transport.requests import Request
#from google.oauth2.credentials import Credentials
#from google_auth_oauthlib.flow import InstalledAppFlow
#from googleapiclient.discovery import build
#from googleapiclient.errors import HttpError

from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event

from PyQt6.QtCore import QDate, QTime

from beautiful_date import *

from model_params import Task


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_schedule_limits(begin_date: QDate(), end_date: QDate(), begin_time: QTime(), end_time: QTime())\
        -> Tuple[BeautifulDate, BeautifulDate]:

    """
    Wyznaczenie granic harmonogramu (T_begin, T_end) w formacie daty.

    :param begin_date: data rozpoczęcia harmonogramu
    :param end_date: data zakończenia harmonogramu
    :param begin_time: godzina rozpoczęcia harmonogramu
    :param end_time: godzina zakończenia harmonogramu
    :return: termin rozpoczęcia, termin zakończenia harmonogramu
    """

    begin_date_time = (D @ begin_date.day()/begin_date.month()/begin_date.year())[begin_time.hour():begin_time.minute()]
    end_date_time = (D @ end_date.day()/end_date.month()/end_date.year())[end_time.hour():end_time.minute()]

    return begin_date_time, end_date_time


def get_event_info(event: Event) -> Tuple[str, int, str]:

    """
    Uzyskanie parametrów zdarzeń z kalendarza.

    :param event: zdarzenie pobrane z kalendarza (event)
    :return: nazwa, czas realizacji (min.), nazwa lokalizacji
    """

    name = event.summary
    location_name = event.location
    duration = (event.end - event.start).seconds / 60

    return name, duration, location_name


def event_2_task(event: Event) -> Task:

    """
    Konwersja (typów) zdarzenia z kalendarza na zadanie.

    :param event: zdarzenie z kalendarza
    :return: zadanie do realizacji
    """

    name, duration, location = get_event_info(event)
    new_task = Task(name, duration, location)

    return new_task


def get_tasks_from_calendar(begin_date_time: BeautifulDate, end_date_time: BeautifulDate) -> Tuple[List[Task], bool]:

    """
    Pobieranie zadań z kalendarza w wybranym zakresie czasu.

    :param begin_date_time: data i godzina początku zakresu
    :param end_date_time: data i godzina końca zakresu
    :return: lista zadań do wykonania w wybranym zakresie, informacja o poprawnie pobranych danych
    """

    # logowanie
    gc = None

    if os.path.exists("token.pickle"):  # jeśli dane logowania zapisane w pliku (nie jest to pierwsze logowanie)
        gc = GoogleCalendar(credentials_path="credentials.json", token_path="token.pickle")

    if not gc:  # jeśli pliku nie ma - logowanie manualne
        gc = GoogleCalendar(credentials_path="credentials.json", save_token=True)

    if not gc:      # co jeśli logowanie się nie powiedzie???
        return [], False

    events = list(gc.get_events(time_min=begin_date_time, time_max=end_date_time))  # pobranie listy zdarzeń
    tasks = []

    for event in events:    # konwersja zdarzeń do zadań
        tasks.append(event_2_task(event))

    return tasks, True















