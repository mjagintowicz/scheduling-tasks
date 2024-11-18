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

    min_distance = min(task_distances)      # minimalna odległość
    next_task_inx = task_distances.index(min_distance)  # indeks zadania

    return next_task_inx


def get_available_nearest(task_inx: int, matrix: List[List], tasks: List[Task], date_time: BeautifulDate):

    matrix_tmp = deepcopy(matrix)      # tymczasowa kopia macierzy dystansów

    while True:

        next_task_inx = get_nearest(task_inx, matrix_tmp)       # znalezenie najbliższej lokalizacji

        if next_task_inx is None:       # jeśli takiej nie ma -- stop
            return None

        if tasks[next_task_inx].is_available(date_time):    # jeśli jest możliwa realizacja zadania -- zwracany indeks
            return next_task_inx

        matrix_tmp[task_inx][next_task_inx] = inf       # jeśli nie -- oznaczenie zadania, jako niewykonalne w tymczasowej macierzy


def tasks_available():
    # sprawdź, czy od chwili t do końca dnia są dostępne taski
    return False


def heuristic(T_begin: BeautifulDate, T_end: BeautifulDate, tasks: List[Task]):    # (depot musi być w liście też)

    solution = {}

    unfinished = tasks
    finished = []       # albo czyszczenie macierzy zamiast tych list

    current_time = T_begin
    depot = tasks[0]

    locations = get_tasks_locations(tasks)

    matrix = get_distance_cost_matrixes(locations, ['walking'], [], T_begin)
    # generacja macierzy w każdej iteracji będzie i w każdej zastąpienie infami tych odwiedzonych
    # :((((((((((((((((((((((((
    while True:
        current_task = depot
        current_task_inx = tasks.index(current_task)
        routes = []
        route = [current_task]

        while True:
            nearest_neighbour = get_available_nearest(current_task_inx, matrix)

            if not nearest_neighbour:   # jeśli nie ma już nic odwiedzenia (lub bardziej opłaca się zakończyć kurs niż robić task - implement!)
                break
            else:
                route.append(nearest_neighbour)     # jeśli neighbour jest ok - dodaj go do kursu
                # update listy finished, unfinished

        routes.append(route)
        if not tasks_available():       # jeśli już nie ma tasków
            current_time += 1*day  # update daty nie do końca tak, bo godzina musi się zresetować
            solution[current_time] = routes     # zapisz trasę w rozwiązaniu

        else:   # jeśli są taski, to zacznij nowy kurs
            continue

