from beautiful_date import *


# KLASA OPISUJĄCA ZADANIE
class Task:

    def __init__(self, name: str, duration: int, location: str, window_left: BeautifulDate = None, window_right: BeautifulDate = None) -> None:

        self.name = name  # nazwa zadania
        self.duration = duration  # czas trwania
        self.location = location  # lokalizacja

        self.window_left = window_left  # dodatkowe ograniczenia zawężające okres czasu na realizację (opcjonalne)
        self.window_right = window_right

        self.start_date_time = None  # ustalony czas rozpoczęcia i zakończenia zadania
        self.end_date_time = None

        # dodać parametry opisujące transport
        # ...

    def get_day_limits(self, date):
        # wyślij zapytanie do Maps API
        # w jakich godzinach self.location jest czynne w dniu date
        # zwróć godzinę otwarcia i godzinę zamknięcia
        pass

    def set_start_end_date_time(self, start_date_time: BeautifulDate, end_date_time: BeautifulDate) -> None:
        """
        Metoda ustawiająca finalny czas rozpoczęcia i zakończenia realizacji zadania.

        :param start_date_time: ustalona data i godzina rozpoczęcia
        :param end_date_time: ustalona data i godzina zakończenia
        :return: NIC
        """

        self.start_date_time = start_date_time
        self.end_date_time = end_date_time
