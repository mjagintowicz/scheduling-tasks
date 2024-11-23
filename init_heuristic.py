# IMPLEMENTACJA HEURYSTYKI DO GENERACJI ROZWIĄZANIA POCZĄTKOWEGO / SĄSIEDZTWA

from beautiful_date import *
from model_params import Task
from typing import List
from map_functions import get_distance_cost_matrixes
from copy import deepcopy

inf = float('inf')


def create_depot(location: str, T_begin: BeautifulDate, T_end: BeautifulDate) -> Task:
    """
    Funkcja tworząca bazę.
    :param location: lokalizacja domu
    :param T_begin: początek harmonogramu
    :param T_end: koniec harmonogramu
    :return: baza jako zadanie
    """

    depot = Task("Dom", 0, location, T_begin, T_end)
    return depot


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


def get_nearest(task_inx: int, matrix: List[List], tasks: List[Task], current_time: BeautifulDate,
                weights: List[float] = [0.1, 0.1, 0.8]):
    """
    Funkcja znajdująca następne zadanie o lokalizacji najbliższej obecnej.
    :param task_inx: indeks zadania
    :param matrix: macierze dystansów (ew. kosztów)
    :param tasks: lista zadań
    :param current_time: obecna chwila czasowa
    :param weights: wagi dotyczące poszczególnych kryteriów wyboru następnego zadania
    :return: indeks najbliższego zadania i wartość kosztu albo None, gdy takiego nie ma
    """

    results = []  # ostateczne wyniki kryterium
    task_distances = matrix[task_inx]  # odległości od obecnego zadania do pozostałych
    if all(distance == inf for distance in task_distances):  # jeśli wszystko inf -- wszystko jest już odwiedzone
        return inf, inf

    for inx in range(len(tasks)):
        if task_distances[inx] == inf or not tasks[inx].is_available_today(current_time):  # jeśli zadanie wykonane lub niemożliwe do realizacji dzisiaj
            results.append(inf)
        else:
            distance = task_distances[inx]  # odległość
            waiting_time = tasks[inx].get_waiting_time(current_time)  # czas oczekiwania na najwcześniejszy start
            current_time_plus = current_time + distance * minutes + tasks[inx].duration * minutes
            urgency = tasks[inx].window_right - current_time_plus  # pilność zadania
            urgency = urgency.total_seconds() / 60

            results.append(weights[0] * distance + weights[1] * waiting_time + weights[2] * urgency)

    best_result = min(results)
    next_task_inx = results.index(best_result)  # indeks najbliższego

    return next_task_inx, best_result


def get_available_nearest(task_inx: int, matrixes: List[List], tasks: List[Task], current_time: BeautifulDate,
                          finished: List):
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
        matrix_tmp = deepcopy(matrix)  # tymczasowa kopia macierzy dystansów

        while True:
            next_task_inx, best_result = get_nearest(task_inx, matrix_tmp, tasks, current_time)  # znalezenie najbliższej lokalizacji

            if best_result == inf:  # jeśli takiej nie ma - stop
                best_inxs.append(inf)
                best_results.append(inf)
                break
            else:  # zapisz najlepszy wynik dla macierzy
                best_inxs.append(next_task_inx)
                best_results.append(best_result)
                break

    min_result = min(best_results)  # wybór najlepszego zadania
    if min_result == inf:
        return inf, inf
    else:
        matrix_inx = best_results.index(min_result)
        next_task_inx = best_inxs[matrix_inx]

    return next_task_inx, matrix_inx


def tasks_available(tasks, finished, current_time):
    """
    Funkcja sprawdzająca, czy w danym dniu można jeszcze wykonać jakieś zadania.
    :param tasks: lista zadań
    :param finished: indeksy wykonanych zadań
    :param current_time: obecna chwila czasowa
    :return: tak/nie
    """
    for inx in range(len(tasks)):
        if inx not in finished:
            if tasks[inx].is_available_today(current_time):
                return True
    return False


def initial_solution(T_begin: BeautifulDate, T_end: BeautifulDate, tasks: List[Task], travel_modes: List[str],
                     transit_modes: List[str] = []):  # (depot musi być w liście też)

    """
    Generacja rozwiązania początkowego.
    :param T_begin: początek harmongramu
    :param T_end: koniec harmonogramu
    :param tasks: lista zadań
    :param travel_modes: lista możliwych metod transportu
    :param transit_modes: lista możliwej komunikacji miejskiej
    :return: rozwiązanie!
    """

    solution = {}

    current_time = T_begin  # obecna chwila
    depot = tasks[0]  # ustawienie bazy
    finished = [0]  # indeksy zadań nieodwiedzonych (baza jest odwiedzona)
    locations = get_tasks_locations(tasks)  # lista lokalizacji zadań

    while True:  # tworzenie trasy w 1 dniu
        current_task = depot
        current_task_inx = tasks.index(current_task)
        route = [current_task]  # kokretny kurs
        route_start_time = current_time

        while True:  # tworzenie konkretnego kursu
            # SPR WARUNEK SAMOCHODU/ROWERU
            # ...
            matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, current_time)[0]  # macierze dystansów
            for matrix in matrixes:  # czyszczenie macierzy z wykonanych zadań
                for inx in finished:
                    matrix[current_task_inx][inx] = inf
                    # czy odwr inx też?

            next_task_inx, matrix_inx = get_available_nearest(current_task_inx, matrixes, tasks, current_time, finished)  # wybór indeksu najbliższego zadania
            # co zrobić jeśli zadanie skończy się następnego dnia? chyba kurs można dalej kontynuować?
            if next_task_inx == inf or not tasks_available(tasks, finished, current_time):  # jeśli nie ma już nic odwiedzenia - zakończ kurs
                current_time = current_time + 24 * hours  # update daty
                current_time = (D @ current_time.day / current_time.month / current_time.year)[00:00]
                if len(route) != 1:  # jeśli droga faktycznie powstała, to ją zapisz
                    solution[route_start_time] = route
                break
            elif route_end_valid(current_task_inx, next_task_inx, matrixes, tasks, current_time):  # jeśli opłacalny powrót do bazy
                # update czasu na powrót do bazy
                # ustaw depot?
                break
            else:  # jeśli wybór zadania był valid
                # zapisanie czasu rozpoczęcia i zakończenia
                # przypadki, że transit...
                tasks[next_task_inx].travel_method = travel_modes[matrix_inx]
                travel_time = matrixes[matrix_inx][current_task_inx][next_task_inx]
                # czas start/end jest zły, bo skoro okno jest od 14 do 18.30 to powinno sie to ustawic
                # najblizszy task -> sprawdz czy jest available_now, jak tak to czas tak jak teraz, jak jeszcze nie to trzeba sprawdzic od opening hour
                # tylko tutaj to robić czy w funkcji szukającej - chyba tu by to miało wiecej sensu
                start_time = current_time+travel_time*minutes
                end_time = start_time + tasks[next_task_inx].duration * minutes
                tasks[next_task_inx].set_start_end_date_time(start_time, end_time)
                if (len(route)) == 1:       # jeśli jest to pierwsze zadanie w kursie - zapis czasu rozpoczęcia kursu
                    route_start_time = start_time
                route.append(tasks[next_task_inx])  # jeśli neighbour jest ok - dodaj go do kursu

                finished.append(next_task_inx)  # zapisz indeks zadania w wykonanych
                current_time = end_time         # udpate czasu
                current_task_inx = next_task_inx    # udpate ostatniego zadania

            if not tasks_available(tasks, finished, current_time):      # sprawdzenie czy kurs można kontynuować - jeśli nie
                current_time = current_time + 24 * hours  # update daty
                current_time = (D @ current_time.day / current_time.month / current_time.year)[00:00]
                solution[route_start_time] = route
                break



        if len(finished) == len(tasks) or current_time >= T_end:     # jeśli wszystkie zadania zostały już wykonane albo czas przekroczony
            break

    return solution
