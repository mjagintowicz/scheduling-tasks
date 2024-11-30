# ALGORYTM OPTYMALIZACYJNY

from beautiful_date import *
from model_params import Task
from typing import List, Dict
from map_functions import get_distance_cost_matrixes
from copy import deepcopy
from init_heuristic import initial_solution, get_all_travel_modes, create_depot, display_solution,\
     disable_travel_methods
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


def fix_route(route: List[Task], current_inx: int, travel_modes: List[str], transit_modes: List[str] = [])\
        -> List[Task] | None:

    """
    Naprawa godzin kursu od zakończenia zadania o wybranym indeksie do końca.
    :param route: kurs
    :param current_inx: indeks ostatniego zadania (po którym ma się zacząć naprawa)
    :param travel_modes: lista metod transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :return: naprawiona droga lub None, jeśli nie jest to możliwe
    """

    all_modes = get_all_travel_modes(travel_modes, transit_modes)

    for i in range(current_inx, len(route) - 1):
        # uzyskanie macierzy odległości dla dostępnych metod transportu i wybór najkrótszej drogi
        locations = [route[i].location, route[i+1].location]

        matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route[i].end_date_time)[0]
        matrixes = disable_travel_methods(route, all_modes, i, matrixes)   # czyszczenie

        distances = []
        for matrix in matrixes:     # uzyskanie odległości z macierzy
            distance = matrix[0][1]
            distances.append(distance)
        # wybór najlepszego z indeksem odpowiedniej metody transportu
        travel_time = min(distances)        # uwaga, trzeba pilnować, żeby nie był inf
        matrix_inx = distances.index(travel_time)
        arrival_time = route[i].end_date_time + travel_time * minutes
        waiting_time = route[i+1].get_waiting_time(arrival_time)
        if waiting_time is None:    # waiting time zły -> naprawa niedopuszczalna
            return None
        start_time = arrival_time + waiting_time * minutes

        # aktualizacja godzin start/end (nw czy baza powinna mieć end_time, więc dlatego jest if)
        if route[i+1].name != 'Dom':
            end_time = start_time + route[i+1].duration * minutes
            route[i+1].set_start_end_date_time(start_time, end_time)
            route[i + 1].travel_time = travel_time
        else:
            route[i+1].start_date_time = start_time
            route[i + 1].travel_time = travel_time

        route[i+1].travel_method = all_modes[matrix_inx]

    return route


def intra_route_reinsertion(route: List[Task], travel_modes: List[str], transit_modes: List[str] = [])\
        -> List[Task] | None:
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
    route_tmp = fix_route(route_tmp, random_task_inx-1, travel_modes, transit_modes)

    # wybór najlepszego miejsca do wstawienia
    feasible_insertions = []
    objectives = []
    for i in range(len(route) - 2):     # range to liczba krawędzi
        if i == random_task_inx - 1:     # pominięcie og miejsca
            continue

        locations = [route_tmp[i].location, random_task.location]
        matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[i].end_date_time)[0]
        matrixes = disable_travel_methods(route_tmp, all_modes, i, matrixes)
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
        random_task.travel_time = travel_time
        # wstawienie do drogi tmp
        route_tmp.insert(i + 1, random_task)

        # sprawdzenie, czy wstawienie jest dopuszczalne (fix analogicznie jak na początku)
        route_tmp_try = deepcopy(route_tmp)
        route_tmp_try = fix_route(route_tmp_try, i + 1, travel_modes, transit_modes)
        if route_tmp_try is not None:     # jeśli pętla przeszła przez cały kurs i nie znalazła problemów z czekaniem
            feasible_insertions.append(i)   # zapisanie indeksu, po którym możliwe jest potencjalne wstawienie
            objectives.append(get_route_objective(route_tmp_try))   # zapisanie wartości f. celu dla tego wstawienia

        route_tmp.remove(random_task)  # usunięcie zadania z tymczasowego kursu, żeby móc testować inne kombinacje

    # po analizie wszystkich możliwych wstawień
    if feasible_insertions:
        best = min(objectives)
        best_inx = objectives.index(best)
        best_inx = feasible_insertions[best_inx]

        # zapisanie faktycznego wstawienia
        locations = [route_tmp[best_inx].location, random_task.location]
        matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[best_inx].end_date_time)[0]
        matrixes = disable_travel_methods(route_tmp, all_modes, best_inx, matrixes)
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
        random_task.travel_time = travel_time
        route_tmp.insert(best_inx + 1, random_task)

        route_tmp = fix_route(route_tmp, best_inx, travel_modes, transit_modes)    # naprawa drogi - zatwierdzenie wybranego wstawienia

        return route_tmp

    else:
        return None


# TESTOWANIE
depot = create_depot("Juliana Tokarskiego 8, Kraków", (D @ 9/12/2024)[8:00], (D @ 15/12/2024)[22:00])
task1 = Task("Basen", 270, "Basen AGH", (D @ 9/12/2024)[14:00], (D @ 12/12/2024)[14:00])
task2 = Task("Gry", 210, "BarON - Pub z planszówkami i konsolami w Krakowie Stefana Batorego 1, 31-135 Kraków, Polska", (D @ 10/12/2024)[18:00], (D @ 11/12/2024)[23:30])
task3 = Task("Obiad", 60, "IKEA Kraków Josepha Conrada 66, 31-357 Kraków, Polska", (D @ 9/12/2024)[13:00], (D @ 12/12/2024)[16:00])
task4 = Task("Zakupy", 30, "Biedronka Piastowska 49, 30-211 Kraków, Polska", (D @ 9/12/2024)[11:00], (D @ 12/12/2024)[21:00])
task5 = Task("Zajęcia", 195, "Wydział Humanistyczny AGH Czarnowiejska 36/Budynek C-7, 30-054 Kraków, Polska", (D @ 12/12/2024)[16:45], (D @ 12/12/2024)[20:00])
task6 = Task("Odebranie przesyłki", 30, "Galeria Krakowska Pawia 5, 31-154 Kraków, Polska", (D @ 10/12/2024)[11:00], (D @ 15/12/2024)[9:45])
tasks = [depot, task1, task2, task3, task4, task5, task6]
modes = ["walking", "transit"]       # auto solos
transit_modes = ["bus", "tram"]

solution, finished = initial_solution((D @ 9/12/2024)[8:00], (D @ 15/12/2024)[22:00], tasks, modes, transit_modes)
display_solution(solution)

route_test = solution[(D @ 9/12/2024)[8:00]]
depot_time_fix_tmp(route_test)
route_test_prim = intra_route_reinsertion(route_test, modes, transit_modes)
