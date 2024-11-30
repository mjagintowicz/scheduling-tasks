# ALGORYTM OPTYMALIZACYJNY

from beautiful_date import *
from model_params import Task
from typing import List, Dict
from map_functions import get_distance_cost_matrixes
from copy import deepcopy
from init_heuristic import initial_solution, get_all_travel_modes
from random import choice

inf = float('inf')


def depot_time_fix_tmp(route: List[Task]):
    """
    Dodawanie czasu zakończenia czekania w bazie.
    :param route: kurs
    :return: NIC
    """

    route[0].end_date_time = route[1].start_date_time - route[1].travel_time * minutes


def get_route_objective(route):
    """
    DO UZUPEŁNIENIA liczenie wartości funkcji celu z konkretnego kursu
    :param route: kurs
    :return: wartość objective
    """

    return 111


def intra_route_reinsertion(route: List[Task], travel_modes: List[str], transit_modes: List[str] = []):
    """
    NIETESTOWANE! Operator sąsiedztwa usuwający jedno losowe zadanie z kursu i szukający innych możliwych miejsc jego
    wstawienia.
    :param route: kurs
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły dotyczące komunikacji miejskiej
    :return: najlepszy ze znalezionych sąsiadów lub None
    """

    all_modes = get_all_travel_modes(travel_modes, transit_modes)

    route_tmp = deepcopy(route)     # kopia oryginalnego kursu
    random_task = choice(route_tmp[1:-1])       # wybór losowego zadania

    # usunięcie zadania z kursu
    random_task_inx = route_tmp.index(random_task)  # indeks zadania w og kursie
    route_tmp.remove(random_task)

    # naprawa drogi od indeksu inx - 1
    for i in range(random_task_inx - 1, len(route_tmp)):
        # uzyskanie macierzy odległości dla dostępnych metod transportu i wybór najkrótszej drogi
        locations = [route_tmp[i].location, route_tmp[i+1].location]
        matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[i].end_date_time)[0]
        distances = []
        for matrix in matrixes:     # uzyskanie odległości z macierzy
            distance = matrix[0][1]
            distances.append(distance)
        # wybór najlepszego z indeksem odpowiedniej metody transportu
        travel_time = min(distances)
        matrix_inx = distances.index(travel_time)
        arrival_time = route_tmp[i].end_date_time + travel_time * minutes
        waiting_time = route_tmp[i+1].get_waiting_time(arrival_time)
        start_time = arrival_time + waiting_time * minutes

        # aktualizacja godzin start/end (nw czy baza powinna mieć end_time, więc dlatego jest if)
        if route_tmp[i+1].name != 'Dom':
            end_time = start_time + route_tmp[i+1].duration * minutes
            route_tmp[i+1].set_start_end_date_time(start_time, end_time)
        else:
            route_tmp[i+1].start_date_time = start_time

        route_tmp[i+1].travel_method = all_modes[matrix_inx]

    # wybór najlepszego miejsca do wstawienia
    feasible_insertions = []
    objectives = []
    for i in range(len(route)-1):
        if i == random_task_inx - 1:     # pominięcie og miejsca
            continue

        locations = [route_tmp[i].location, random_task.location]
        matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[i].end_date_time)[0]
        distances = []
        for matrix in matrixes:  # uzyskanie odległości z macierzy
            distance = matrix[0][1]
            distances.append(distance)
        travel_time = min(distances)

        matrix_inx = distances.index(travel_time)
        arrival_time = route_tmp[i].end_date_time + travel_time * minutes
        waiting_time = route_tmp[i + 1].get_waiting_time(arrival_time)
        # jeśli zadanie nie może być wykonane w określonej porze tego dnia, to odrzucenie tego wstawiena
        if waiting_time is None:
            break
        # jeśli można poczekać, to akceptacja wstawienia
        start_time = arrival_time + waiting_time * minutes
        end_time = start_time + random_task.duration * minutes
        random_task.set_start_end_date_time(start_time, end_time)
        random_task.travel_method = all_modes[matrix_inx]
        # wstawienie do drogi tmp
        route_tmp.insert(i+1, random_task)

        # sprawdzenie, czy wstawienie jest dopuszczalne (fix analogicznie jak na początku)
        j = 0
        for j in range(i+1, len(route_tmp)):
            locations = [route_tmp[j].location, route_tmp[j + 1].location]
            matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[j].end_date_time)[0]
            distances = []
            for matrix in matrixes:
                distance = matrix[0][1]
                distances.append(distance)
            travel_time = min(distances)
            matrix_inx = distances.index(travel_time)
            arrival_time = route_tmp[i].end_date_time + travel_time * minutes
            waiting_time = route_tmp[i + 1].get_waiting_time(arrival_time)
            # niepoprawny waiting time oznacza, że to wstawienie nie jest dopuszczalne
            if waiting_time is None:
                break
            start_time = arrival_time + waiting_time * minutes
            if route_tmp[i + 1].name != 'Dom':
                end_time = start_time + route_tmp[i + 1].duration * minutes
                route_tmp[i + 1].set_start_end_date_time(start_time, end_time)
            else:
                route_tmp[i + 1].start_date_time = start_time
            route_tmp[i + 1].travel_method = all_modes[matrix_inx]

        if j == len(route_tmp) - 1:     # jeśli pętla przeszła przez cały kurs i nie znalazła problemów z czekaniem
            feasible_insertions.append(i)   # zapisanie indeksu, po którym możliwe jest potencjalne wstawienie
            objectives.append(get_route_objective(route_tmp))   # zapisanie wartości f. celu dla tego wstawienia

        route_tmp.remove(random_task)  # usunięcie zadania z tymczasowego kursu, żeby móc testować inne kombinacje

    # po analizie wszystkich możliwych wstawień
    if feasible_insertions:
        best = min(objectives)
        best_inx = feasible_insertions.index(best)

        # zapisanie faktycznego wstawienia
        locations = [route_tmp[best_inx].location, random_task.location]
        matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[best_inx].end_date_time)[0]
        distances = []
        for matrix in matrixes:  # uzyskanie odległości z macierzy
            distance = matrix[0][1]
            distances.append(distance)
        travel_time = min(distances)

        matrix_inx = distances.index(travel_time)
        arrival_time = route_tmp[best_inx].end_date_time + travel_time * minutes
        waiting_time = route_tmp[best_inx + 1].get_waiting_time(arrival_time)
        start_time = arrival_time + waiting_time * minutes
        end_time = start_time + random_task.duration * minutes
        random_task.set_start_end_date_time(start_time, end_time)
        random_task.travel_method = all_modes[matrix_inx]
        route_tmp.insert(best_inx + 1, random_task)

        return route_tmp

    else:
        return None

