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


def get_nearest(task_inx: int, matrix: List[List], tasks: List[Task], current_time: BeautifulDate, weights: List[float] = [0.1, 0.1, 0.8]):

    """
    Funkcja znajdująca następne zadanie o lokalizacji najbliższej obecnej.
    :param task_inx: indeks zadania
    :param matrix: macierze dystansów (ew. kosztów)
    :param tasks: lista zadań
    :param current_time: obecna chwila czasowa
    :param weights: wagi dotyczące poszczególnych kryteriów wyboru następnego zadania
    :return: indeks najbliższego zadania i wartość kosztu albo None, gdy takiego nie ma
    """

    results = []    # ostateczne wyniki kryterium
    task_distances = matrix[task_inx]   # odległości od obecnego zadania do pozostałych
    if all(distance == inf for distance in task_distances):     # jeśli wszystko inf -- wszystko jest już odwiedzone
        return None

    for inx in range(len(tasks)):
        if task_distances[inx] == inf or not tasks[inx].is_available_today(current_time):       # jeśli zadanie wykonane lub niemożliwe do realizacji dzisiaj
            results.append(inf)

        distance = task_distances[task_inx][inx]        # odległość
        waiting_time = tasks[inx].get_waiting_time(current_time)     # czas oczekiwania na najwcześniejszy start
        current_time_plus = current_time + distance*minute + tasks[inx].duration*minute
        urgency = tasks[inx].window_right - current_time_plus     # pilność zadania
        urgency = urgency.total_seconds() / 60

        results.append(weights[0]*distance + weights[1]*waiting_time + weights[2]*urgency)

    best_result = min(results)
    next_task_inx = results.index(best_result)      # indeks najbliższego

    return next_task_inx, best_result


def get_available_nearest(task_inx: int, matrixes: List[List], tasks: List[Task], current_time: BeautifulDate, finished: List):

    """
    Funkcja zwracająca indeks najbliższego zadania spełniającego ograniczenia.
    :param task_inx: indeks ostatniego zadania
    :param matrixes: macierze dystansów (kosztów)
    :param tasks: lista zadań
    :param current_time: obecny czas
    :param finished: lista indeksów wykonanych zadań
    :return: indeks najbliższego zadania i indeks macierzy
    """

    best_inxs = []
    best_results = []

    for matrix in matrixes:
        matrix_tmp = deepcopy(matrix)      # tymczasowa kopia macierzy dystansów

        while True:
            next_task_inx, best_result = get_nearest(task_inx, matrix_tmp, tasks, current_time)       # znalezenie najbliższej lokalizacji

            if next_task_inx is None or next_task_inx == inf:       # jeśli takiej nie ma - stop
                best_inxs.append(inf)
                best_results.append(inf)
            else:                               # zapisz najlepszy wynik dla macierzy
                best_inxs.append(next_task_inx)
                best_results.append(best_result)

    min_result = min(best_results)              # wybór najlepszego zadania
    matrix_inx = best_inxs.index(min_result)
    next_task_inx = best_inxs[matrix_inx]

    return next_task_inx, matrix_inx


def tasks_available():
    # sprawdź, czy od chwili t do końca dnia są dostępne taski
    return False


def nearest_neighbour(T_begin: BeautifulDate, T_end: BeautifulDate, tasks: List[Task], travel_modes: List[str], transit_modes = []):    # (depot musi być w liście też)

    solution = {}

    current_time = T_begin      # obecna chwila
    depot = tasks[0]            # ustawienie bazy
    finished = [0]  # indeksy zadań nieodwiedzonych (baza jest odwiedzona)
    locations = get_tasks_locations(tasks)      # lista lokalizacji zadań

    while True:     # tworzenie trasy w 1 dniu
        current_task = depot
        current_task_inx = tasks.index(current_task)
        routes = []     # trasa w ciągu dnia (lista kursów)
        route = [current_task]      # kokretny kurs

        while True:     # tworzenie konkretnego kursu
            # SPR WARUNEK SAMOCHODU/ROWERU
            # ...
            matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, current_time)  # macierze dystansów
            for matrix in matrixes:  # czyszczenie macierzy z wykonanych zadań
                for inx in finished:
                    matrix[current_task_inx][inx] = inf

            next_task_inx, matrix_inx = get_available_nearest(current_task_inx, matrixes, tasks, current_time, finished)      # wybór indeksu najbliższego zadania
            if not next_task_inx == inf:   # jeśli nie ma już nic odwiedzenia - zakończ kurs
                break
            elif route_end_valid(current_task_inx, next_task_inx, matrixes, tasks, current_time):   # jeśli opłacalny powrót do bazy
                # update czasu na powrót do bazy
                # ustaw depot?
                break
            else:       # jeśli wybór zadania był valid
                route.append(tasks[next_task_inx])     # jeśli neighbour jest ok - dodaj go do kursu
                finished.append(next_task_inx)         # zapusz indeks zadania w wykonanych
                current_time += matrixes[matrix_inx]

        routes.append(route)        # zapisz kurs do trasy

        if not tasks_available():       # jeśli już nie ma tasków dziś
            current_time += 1*day  # update daty nie do końca tak, bo godzina musi się zresetować
            solution[current_time] = routes     # zapisz trasę w rozwiązaniu

        else:   # jeśli są taski, to nową trasę
            continue

