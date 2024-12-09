# funkcje realizujące łączenie z kalendarzem

import datetime
import os.path
from typing import Tuple, List
import pickle

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


def access_calendar(calendar_id: str = 'primary') -> GoogleCalendar | None:

    """
    Uzyskanie dostępu do kalendarza Google (logowanie).

    :param calendar_id: email lub nazwa/id kalendarza, domyślnie primary
    :return: obiekt GoogleCalendar reprezentujący wybrany kalendarz lub None, gdy logowanie się nie powiodło
    """

    gc = None

    if os.path.exists("token.pickle"):  # jeśli dane logowania zapisane w pliku (nie jest to pierwsze logowanie)
        try:
            gc = GoogleCalendar(default_calendar=calendar_id, credentials_path="credentials.json", token_path="token.pickle")
            return gc
        except Exception as err:
            os.remove("token.pickle")

    if not gc:  # jeśli pliku nie ma - logowanie manualne
        gc = GoogleCalendar(default_calendar=calendar_id, credentials_path="credentials.json", save_token=True)
        return gc

    if not gc:  # jaka akcja, jeśli logowanie się nie powiedzie???
        return None


def get_time_limits(begin_date: QDate(), end_date: QDate(), begin_time: QTime(), end_time: QTime())\
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


def event_2_task(event: Event, begin_date_time: BeautifulDate, end_date_time: BeautifulDate) -> Task:

    """
    Konwersja (typów) zdarzenia z kalendarza na zadanie.

    :param event: zdarzenie z kalendarza
    :param begin_date_time: T_begin
    :param end_date_time: T_end
    :return: zadanie do realizacji
    """
    task = Task(event.summary, (event.end - event.start).seconds / 60, event.location, begin_date_time, end_date_time)

    return task


def task_2_event(task: Task) -> Event:

    """
    Konwersja zadania do zdarzenia w kalendarzu.

    :param task: zadanie
    :return: zdarzenie (event)
    """

    event = Event(summary=task.name, start=task.start_date_time, end=task.end_date_time, location=task.location)
    return event


def get_tasks_from_calendar(begin_date_time: BeautifulDate, end_date_time: BeautifulDate, calendar_id: str = 'primary'):

    """
    Pobieranie zadań z kalendarza w wybranym zakresie czasu.

    :param begin_date_time: data i godzina początku zakresu
    :param end_date_time: data i godzina końca zakresu
    :param calendar_id: nazwa kalendarza (domyślnie primary)
    :return: lista zadań do wykonania w wybranym zakresie, informacja o poprawnie pobranych danych
    """

    gc = access_calendar(calendar_id)   # uzyskanie dostępu do kalendarza

    if not gc:          # jeśli się nie powiodł
        return [], False

    events = list(gc.get_events(time_min=begin_date_time, time_max=end_date_time))  # pobranie listy zdarzeń
    tasks = []
    event_ids = []

    for event in events:    # konwersja zdarzeń do zadań
        event_ids.append(event.event_id)
        tasks.append(event_2_task(event, begin_date_time, end_date_time))

    return tasks, event_ids, True


def add_task_to_calendar(task: Task, calendar_id: str = 'primary') -> bool:

    """
    Dodanie zadania do kalendarza Google.

    :param task: zadanie, które ma zostać dodane
    :param calendar_id: nazwa kalendarza docelowego (domyślnie primary)
    :return: informacja, czy udało się dodać zadanie
    """

    gc = access_calendar(calendar_id)

    if not gc:
        return False

    # verify location
    # ...

    event = task_2_event(task)
    gc.add_event(event)

    return True


def find_event(event_id, calendar_id: str = 'primary'):

    """
    Znajdowanie eventu po id.
    :param event_id: id
    :param calendar_id: id kalendarza, domyślnie primary
    :return: event
    """

    gc = access_calendar(calendar_id)

    event = gc.get_event(event_id)
    return event


def log_out():
    """
    Funkcja do wylogowywania.
    :return: NIC
    """
    os.remove("token.pickle")




