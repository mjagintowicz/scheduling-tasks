# IMPLEMENTACJA HEURYSTYKI DO GENERACJI ROZWIĄZANIA POCZĄTKOWEGO / SĄSIEDZTWA

from beautiful_date import *
from model_params import Task
from typing import List
from map_functions import get_location_working_hours, get_distance_cost_matrixes, get_transit_route_details
from copy import deepcopy


inf = float('int')


def get_tasks_locations(tasks: List[Task]):

    """
    Funkcja tworząca listę lokalizacji na podstawie listy zadań.
    :param tasks: lista zadań
    :return: lista lokalizacji
    """

    locations = []

    for task in tasks:
        locations.append(task.location)

    return locations


def route_end_valid(task_inx, next_task_inx, matrix, tasks, current_time):

    task = tasks[task_inx]
    next_task = tasks[next_task_inx]

    # next_task_start = wyliczony czas rozpoczęcia
    # waiting_time = czas od current_time do next_task_start
    # sprawdzenie czy waiting_time < czas dojazdu do bazy
    # jeśli tak - return False
    # jeśli nie - znajdź najbliższe zadanie, sprawdź czas jego otwarcia i ten czas z macierzy
    # obliczenie ich róźnicy
    # jeśli < 90 - return False (nie opłaca się kończyć kursu)
    # jeśli > 90 - return True (przerwa w trasie - oszczędność w funkcji celu)

    return False


def get_nearest(task_inx: int, matrix: List[List]):

    """
    Funkcja znajdująca następne zadanie o lokalizacji najbliższej obecnej.
    :param task_inx: indeks zadania
    :param matrix: macierz dystansów (ew. kosztów)
    :return: indeks najbliższego zadania albo None, gdy takiego nie ma
    """

    task_distances = matrix[task_inx]   # odległości od obecnego zadania do pozostałych
    if all(distance == inf for distance in task_distances):     # jeśli wszystko inf -- wszystko jest już odwiedzone
        return None

    min_distance = min(task_distances[task_inx][1:])      # minimalna odległość (bez depotu)
    next_task_inx = task_distances.index(min_distance)  # indeks zadania

    return next_task_inx


def get_available_nearest(task_inx: int, matrix: List[List], tasks: List[Task], current_time: BeautifulDate, finished: List):

    """
    Funkcja zwracająca indeks najbliższego zadania spełniającego ograniczenia.
    :param task_inx: indeks ostatniego zadania
    :param matrix: macierz dystansów (kosztów)
    :param tasks: lista zadań
    :param current_time: obecny czas
    :param finished: lista indeksów wykonanych zadań
    :return: indeks najbliższego zadania
    """

    matrix_tmp = deepcopy(matrix)      # tymczasowa kopia macierzy dystansów

    while True:
        next_task_inx = get_nearest(task_inx, matrix_tmp)       # znalezenie najbliższej lokalizacji

        if next_task_inx is None:       # jeśli takiej nie ma - stop
            return None

        if next_task_inx in finished:
            matrix_tmp[task_inx][next_task_inx] = inf
            continue

        elif tasks[next_task_inx].is_available(current_time):    # jeśli jest możliwa realizacja zadania

            if route_end_valid(task_inx, next_task_inx, matrix, tasks, current_time):   # czy opłaca się robić przerwę
                return 0    # tak - zwracan indeks bazy
            else:
                return next_task_inx    # nie - zwracany indeks wyznaczonego zadania (kontynuacja kursu)

        else:               # w przeciwnym wypadku (nieodwiedzony, ale niemożliwy do realizacji)
            matrix_tmp[task_inx][next_task_inx] = inf


def tasks_available():
    # sprawdź, czy od chwili t do końca dnia są dostępne taski
    return False


def nearest_neighbour(T_begin: BeautifulDate, T_end: BeautifulDate, tasks: List[Task], travel_modes, transit_modes = []):    # (depot musi być w liście też)

    solution = {}

    current_time = T_begin
    depot = tasks[0]
    finished = [0]  # indeksy zadań nieodwiedzonych (baza jest odwiedzona)

    locations = get_tasks_locations(tasks)
    matrix = get_distance_cost_matrixes(locations, travel_modes, transit_modes, current_time)

    while True:
        current_task = depot
        current_task_inx = tasks.index(current_task)
        routes = []
        route = [current_task]

        while True:
            next_task = get_available_nearest(current_task_inx, matrix, tasks, current_time, finished)

            if not next_task or next_task == 0:   # jeśli nie ma już nic odwiedzenia
                break
            else:
                route.append(next_task)     # jeśli neighbour jest ok - dodaj go do kursu
                # update listy finished
                # update macierzy

        routes.append(route)

        if not tasks_available():       # jeśli już nie ma tasków
            current_time += 1*day  # update daty nie do końca tak, bo godzina musi się zresetować
            solution[current_time] = routes     # zapisz trasę w rozwiązaniu

        else:   # jeśli są taski, to zacznij nowy kurs
            continue

