# IMPLEMENTACJA HEURYSTYKI DO GENERACJI ROZWIĄZANIA POCZĄTKOWEGO / SĄSIEDZTWA

from beautiful_date import *
from model_params import Task
from typing import List
from map_functions import get_location_working_hours, get_distance_cost_matrixes, get_transit_route_details


def get_nearest():
    # znajdź najbliższy możliwy task
    return 0

def tasks_available():
    # sprawdź czy od chwili t do końca dnia są dostępne taski
    return False


def heuristic(T_begin: BeautifulDate, T_end: BeautifulDate, tasks: List[Task], depot: Task):
    solution = {}

    unfinished = tasks
    finished = []

    current_time = T_begin

    while True:
        current_task = depot
        routes = []
        route = [current_task]

        while True:
            nearest_neighbour = get_nearest()

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

