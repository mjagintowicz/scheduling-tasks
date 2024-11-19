from beautiful_date import *
from map_functions import get_location_working_hours
from datetime import timedelta, time, datetime
from typing import List


# KLASA OPISUJĄCA ZADANIE
class Task:

    def __init__(self, name: str, duration: int, location: str, window_left: BeautifulDate,
                 window_right: BeautifulDate) -> None:
        self.name = name  # nazwa zadania
        self.duration = duration  # czas trwania
        self.location = location  # lokalizacja

        self.opening_hours = None  # godziny pracy
        self.closing_hours = None

        self.window_left = window_left  # dodatkowe ograniczenia zawężające okres na realizację
        self.window_right = window_right

        self.start_date_time = None  # ustalony czas rozpoczęcia i zakończenia zadania
        self.end_date_time = None

        self.travel_method = None   # ustalona metoda transportu do lokalizacji zadania

    def set_time_windows(self, window_left: BeautifulDate, window_right: BeautifulDate):
        """
        Zawężanie czasu na realizację.
        :param window_left: najwcześniejszy termin rozpoczęcia
        :param window_right: najpóźniejszy termin zakończenia
        :return: NIC
        """
        self.window_left = window_left
        self.window_right = window_right

    def set_start_end_date_time(self, start_date_time: BeautifulDate, end_date_time: BeautifulDate) -> None:
        """
        Metoda ustawiająca finalny czas rozpoczęcia i zakończenia realizacji zadania.
        :param start_date_time: ustalona data i godzina rozpoczęcia
        :param end_date_time: ustalona data i godzina zakończenia
        :return: NIC
        """

        self.start_date_time = start_date_time
        self.end_date_time = end_date_time

    def set_travel_method(self, travel_method: str):
        """
        Metoda ustawiająca parametr określający metodę transportu do lokalizacji zadania
        :param travel_method: metoda transportu (“driving”, “walking”, “bus”, “subway”, “train”, “tram”, “rail”, “bicycling”)
        takie jak w mapach
        :return: NIC
        """

        self.travel_method = travel_method

    def get_working_hours(self):
        """
        Uzyskanie informacji na temat godzin pracy lokalizacji z Google Places API.
        :return: NIC
        """

        self.opening_hours, self.closing_hours = get_location_working_hours(self.location)

    def is_available(self, date_time: BeautifulDate) -> bool:
        """
        Sprawdzenie czy w wybranej chwili możliwa jest realizacja zadania.
        :param date_time: data i godzina
        :return: tak/nie
        """

        # sprawdzenie czy dany dzień jest w oknie czasowym
        if date_time < self.window_left or date_time + timedelta(minutes=self.duration) > self.window_right:
            return False

        # sprawdzenie czy w tym dniu tygodnia miejsce jest otwarte
        # jeśli godziny nie zostały zainicjowane wcześniej
        if not self.opening_hours or not self.closing_hours:
            self.get_working_hours()

        day_of_week = date_time.weekday()
        if self.opening_hours[day_of_week] != '-':

            current_time = time(hour=date_time.hour, minute=date_time.minute)
            opening_time = datetime.strptime(self.opening_hours[day_of_week], '%H:%M')
            opening_time = time(hour=opening_time.hour, minute=opening_time.minute)
            closing_time = datetime.strptime(self.closing_hours[day_of_week], '%H:%M')
            closing_time = time(hour=closing_time.hour, minute=closing_time.minute)

            # czas po realizacji
            tmp_time = datetime.combine(datetime.today(), current_time) + timedelta(minutes=self.duration)
            current_time_plus = time(hour=tmp_time.hour, minute=tmp_time.minute)

            # jeśli jest czynne - sprawdzenie czy godzina jest w oknie czasowym
            if current_time < opening_time or current_time_plus > closing_time:
                return False

        # zadanie jest dostępne, jeśli żaden z powyższych warunków nie został spełniony
        return True


#task = Task("test", 20, "Galeria Krakowska", (D @ 12 / 11 / 2024)[8:00], (D @ 14 / 12 / 2024)[8:00])
#task.is_available(D.now())
