from beautiful_date import *
from map_functions import get_location_working_hours
from datetime import timedelta, time, datetime
from typing import List

inf = float('inf')


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
        self.travel_time = None     # czas trwania podróży do lokalizacji
        self.travel_cost = None     # koszt podróży (kryterium 2)
        self.transit_details = []

        self.idle_time = None

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

        if start_date_time < self.window_left or end_date_time > self.window_right:
            pass

        self.start_date_time = start_date_time
        self.end_date_time = end_date_time

    def set_travel_parameters(self, travel_method: str, travel_time: int, travel_cost: float):
        """
        Metoda ustawiająca parametry dotyczące transportu do lokalizacji zadania.
        :param travel_method: sposób podróży
        :param travel_time: czas (min)
        :param travel_cost: koszt
        :return: NIC
        """
        self.travel_method = travel_method
        self.travel_time = travel_time
        self.travel_cost = travel_cost

    def get_working_hours(self):
        """
        Uzyskanie informacji na temat godzin pracy lokalizacji z Google Places API.
        :return: NIC
        """
        self.opening_hours, self.closing_hours = get_location_working_hours(self.location)

    def is_available_now(self, date_time: BeautifulDate) -> bool:
        """
        Sprawdzenie, czy w wybranej chwili możliwa jest realizacja zadania.
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
            if closing_time > opening_time:     # zamknięcie tego samego dnia
                if current_time < opening_time or current_time_plus > closing_time:
                    return False

            if closing_time < opening_time:     # zamknięcie już w następnej dobie
                if current_time < opening_time:
                    return False
                elif current_time < current_time_plus < closing_time:
                    return False
                elif current_time > current_time_plus > closing_time:
                    return False

        # zadanie jest dostępne, jeśli żaden z powyższych warunków nie został spełniony
        return True

    def is_available_today(self, date_time: BeautifulDate) -> bool:

        """
        Sprawdzenie, czy konkretnego dnia możliwa jest realizacja zadania.
        :param date_time: obecna chwila czasowa
        :return: tak/nie
        """

        # sprawdzenie czy dany dzień jest w oknie czasowym
        # sprawdzenie dnia
        if date_time < self.window_left:        # obecny czas jest przed otwarciem okna czasowego
            date_time_tmp = (D @ date_time.day/date_time.month/date_time.year)[00:00]
            window_left_tmp = (D @ self.window_left.day/self.window_left.month/self.window_right.year)[00:00]
            if date_time_tmp != window_left_tmp:    # jeśli okno nie otworzy się obecnego dnia
                return False

        date_time_plus = date_time + self.duration * minutes
        if date_time_plus > self.window_right:
            return False  # error

        # sprawdzenie czy w tym dniu tygodnia miejsce jest otwarte
        if not self.opening_hours or not self.closing_hours:
            self.get_working_hours()

        day_of_week = date_time.weekday()
        if self.opening_hours[day_of_week] != '-':

            current_time = time(hour=date_time.hour, minute=date_time.minute)
            opening_time = datetime.strptime(self.opening_hours[day_of_week], '%H:%M')
            opening_time = time(hour=opening_time.hour, minute=opening_time.minute)
            closing_time = datetime.strptime(self.closing_hours[day_of_week], '%H:%M')      # SPR! zamiast 12 powinno być 00
            closing_time = time(hour=closing_time.hour, minute=closing_time.minute)

            # czas po realizacji
            tmp_time = datetime.combine(datetime.today(), current_time) + timedelta(minutes=self.duration)
            current_time_plus = time(hour=tmp_time.hour, minute=tmp_time.minute)

            # jeśli jest czynne - sprawdzenie czy godzina jest w oknie czasowym
            if closing_time > opening_time:  # zamknięcie tego samego dnia
                if current_time_plus > closing_time:
                    return False

            if closing_time < opening_time:  # zamknięcie już w następnej dobie
                if current_time_plus < closing_time:
                    return False
                elif closing_time < current_time_plus < current_time:
                    return False

            return True
        return False

    def get_waiting_time(self, date_time: BeautifulDate):

        """
        Wyznaczenie czasu oczekiwania na otwarcie lokalizacji.
        :param date_time: obecna chwila czasowa
        :return: czas oczekiwania w minutach
        """

        if not self.is_available_today(date_time):
            return None

        day_of_week = date_time.weekday()
        current_time = timedelta(hours=date_time.hour, minutes=date_time.minute)
        opening_time = datetime.strptime(self.opening_hours[day_of_week], '%H:%M')
        opening_time = timedelta(hours=opening_time.hour, minutes=opening_time.minute)
        window_left_time = timedelta(hours=self.window_left.hour, minutes=self.window_left.minute)

        if opening_time >= window_left_time >= current_time or opening_time >= current_time >= window_left_time:     # jeśli trzeba oczekiwać na otwarcie miejsca
            waiting_time = opening_time - current_time
            return waiting_time.total_seconds() / 60
        elif window_left_time >= opening_time >= current_time or window_left_time >= current_time >= opening_time:        # jeśli trzeba oczekiwać na otwarcie okna
            waiting_time = window_left_time - current_time
            return waiting_time.total_seconds() / 60
        else:
            return 0


# klasa reprezentująca kurs, żeby nie robić już na słownikach
class Route:

    def __init__(self, start_date: BeautifulDate, tasks: List[Task]):

        self.tasks = tasks
        self.start_date_only = (D @ start_date.day / start_date.month / start_date.year)[00:00]
        self.start_date_og = start_date

        # naprawa daty depot
        self.tasks[0].end_date_time = tasks[1].start_date_time - tasks[1].travel_time * minutes

        self.objective = 0

        self.idle_time = None

        self.infeasable_inx = []       # indeksy zadań, gdzie następują kolizje

    def set_objective(self, weights=None):
        """
        Wyliczanie funkcji celu dla konkretnego kursu.
        :param weights:
        :return:
        """

        if weights is None:
            weights = [0.6, 0, 0.4]

        for inx in range(len(self.tasks)):
            if inx == 0:
                continue
            elif inx == len(self.tasks) - 1:
                if self.tasks[inx].travel_cost == inf:
                    self.objective += weights[0] * self.tasks[inx].travel_time
                else:
                    self.objective += weights[0] * self.tasks[inx].travel_time + weights[1] *\
                                      self.tasks[inx].travel_cost
            else:
                arrival_date_time = self.tasks[inx-1].end_date_time + self.tasks[inx].travel_time * minutes
                waiting_time = self.tasks[inx].start_date_time - arrival_date_time
                waiting_time = waiting_time.total_seconds() / 60
                if self.tasks[inx].travel_cost == inf:
                    self.objective += weights[0] * self.tasks[inx].travel_time + weights[2] * waiting_time
                else:
                    self.objective += weights[0] * self.tasks[inx].travel_time + weights[1] *\
                                      self.tasks[inx].travel_cost + weights[2] * waiting_time

    def depot_fix(self):
        self.tasks[0].end_date_time = self.tasks[1].start_date_time - self.tasks[1].travel_time * minutes
        self.start_date_og = self.tasks[0].end_date_time

    def __repr__(self):
        s = ""
        for i in range(1, len(self.tasks)):
            if i == len(self.tasks) - 1:
                s += f"{i}. planowana godzina powrotu: {self.tasks[i].end_date_time}; transport: {self.tasks[i].travel_method}\n"
            else:
                s += f"{i}. {self.tasks[i].name} o godzinie {self.tasks[i].end_date_time}; transport: {self.tasks[i].travel_method}\n"
        return s


def set_idle_time(route: Route, prev_route: Route | None):
    """
    Funkcja ustawiająca czas bezczynnego czekania w bazie przed rozpoczęciem kursu.
    :param route: kurs
    :param prev_route: poprzedni kurs
    :return:
    """

    if prev_route is None or prev_route.start_date_only < route.start_date_only:  # jeśli nie ma poprzedniej drogi albo jest ona innego dnia
        idle_time = route.tasks[0].end_date_time - route.start_date_og
    else:
        idle_time = route.tasks[0].end_date_time - prev_route.tasks[-1].start_date_time

    idle_time = idle_time.total_seconds() / 60
    route.idle_time = idle_time


