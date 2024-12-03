# ALGORYTM OPTYMALIZACYJNY

from beautiful_date import *
from model_params import Task
from typing import List, Dict
from map_functions import get_distance_cost_matrixes
from copy import deepcopy
from init_heuristic import initial_solution, get_all_travel_modes, create_depot, display_solution
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


def fix_route(route: List[Task], current_inx: int, travel_modes: List[str], transit_modes: List[str] = []) \
        -> List[Task] | None:
    """
    NIETESTOWANE PO NAPRAWIE MACIERZY! Naprawa godzin kursu od zakończenia zadania o wybranym indeksie do końca.
    :param route: kurs
    :param current_inx: indeks ostatniego zadania (po którym ma się zacząć naprawa)
    :param travel_modes: lista metod transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :return: naprawiona droga lub None, jeśli nie jest to możliwe
    """

    route_tmp = deepcopy(route)
    all_modes = get_all_travel_modes(travel_modes, transit_modes)

    for i in range(current_inx, len(route_tmp) - 1):
        # uzyskanie macierzy odległości dla dostępnych metod transportu i wybór najkrótszej drogi
        locations = [route_tmp[i].location, route_tmp[i + 1].location]
        if i == 0:
            matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[i].end_date_time)[0]
        else:
            if route_tmp[i].travel_method == 'driving':
                car_enabled = True
                bike_enabled = False
                others_enabled = False
            elif route_tmp[i].travel_method == 'bicycling':
                car_enabled = False
                bike_enabled = True
                others_enabled = False
            else:
                car_enabled = False
                bike_enabled = False
                others_enabled = True
            matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[i].end_date_time,
                                                  car_enabled=car_enabled, bike_enabled=bike_enabled,
                                                  others_enabled=others_enabled)[0]

        distances = []
        for matrix in matrixes:  # uzyskanie odległości z macierzy
            distance = matrix[0][1]
            distances.append(distance)
        # wybór najlepszego z indeksem odpowiedniej metody transportu
        travel_time = min(distances)  # uwaga, trzeba pilnować, żeby nie był inf
        matrix_inx = distances.index(travel_time)
        arrival_time = route_tmp[i].end_date_time + travel_time * minutes
        waiting_time = route_tmp[i + 1].get_waiting_time(arrival_time)
        if waiting_time is None:  # waiting time zły -> naprawa niedopuszczalna
            return None
        start_time = arrival_time + waiting_time * minutes

        # aktualizacja godzin start/end (nw czy baza powinna mieć end_time, więc dlatego jest if)
        if route_tmp[i + 1].name != 'Dom':
            end_time = start_time + route_tmp[i + 1].duration * minutes
            route_tmp[i + 1].set_start_end_date_time(start_time, end_time)
            route_tmp[i + 1].travel_time = travel_time
        else:
            route_tmp[i + 1].start_date_time = start_time
            route_tmp[i + 1].travel_time = travel_time

        route_tmp[i + 1].travel_method = all_modes[matrix_inx]

    return route_tmp


def find_valid_insertion(route: List[Task], lonely_task: Task, travel_modes: List[str],
                         transit_modes: List[str] = [], forbidden_inx=None):
    """
    NIESTESTOWANE! Funkcja znajdująca dopuszczalne wstawienia w kursie.
    :param route: kurs
    :param lonely_task: zadanie do wstawienia
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :param forbidden_inx: opcjonalnie - indeks zadania, po którym zabronione jest wstawienie
    :return: lista dopuszczalnych indeksów, po których można wstawić zadanie i koszty
    """

    route_tmp = deepcopy(route)
    all_modes = get_all_travel_modes(travel_modes, transit_modes)
    car_enabled = True
    bike_enabled = True
    others_enabled = True

    feasible_insertions = []
    objectives = []

    for i in range(len(route_tmp) - 2):  # range to liczba krawędzi
        if forbidden_inx is not None:
            if i == forbidden_inx - 1:  # pominięcie og miejsca
                continue

        locations = [route_tmp[i].location, lonely_task.location]
        if i == 0:
            matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[i].end_date_time)[0]
        else:
            if route_tmp[i].travel_method == 'driving':
                car_enabled = True
                bike_enabled = False
                others_enabled = False
            elif route_tmp[i].travel_method == 'bicycling':
                car_enabled = False
                bike_enabled = True
                others_enabled = False
            else:
                car_enabled = False
                bike_enabled = False
                others_enabled = True
            matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, route_tmp[i].end_date_time,
                                                  car_enabled=car_enabled, bike_enabled=bike_enabled,
                                                  others_enabled=others_enabled)[0]

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
        end_time = start_time + lonely_task.duration * minutes
        lonely_task.set_start_end_date_time(start_time, end_time)
        lonely_task.travel_method = all_modes[matrix_inx]
        lonely_task.travel_time = travel_time
        # wstawienie do drogi tmp
        route_tmp.insert(i + 1, lonely_task)

        # sprawdzenie, czy wstawienie jest dopuszczalne (fix analogicznie jak na początku)
        route_tmp_try = deepcopy(route_tmp)
        route_tmp_try = fix_route(route_tmp_try, i + 1, travel_modes, transit_modes)
        if route_tmp_try is not None:  # jeśli pętla przeszła przez cały kurs i nie znalazła problemów z czekaniem
            feasible_insertions.append(i)  # zapisanie indeksu, po którym możliwe jest potencjalne wstawienie
            objectives.append(get_route_objective(route_tmp_try))  # zapisanie wartości f. celu dla tego wstawienia

        route_tmp.remove(lonely_task)  # usunięcie zadania z tymczasowego kursu, żeby móc testować inne kombinacje

    return feasible_insertions, objectives


def single_insertion(route: List[Task], lonely_task: Task, insertion_inx: int, travel_modes: List[str],
                     transit_modes: List[str] = []):

    """
    NIETESTOWANE! Funkcja realizująca wstawienie punktu do kursu.
    :param route: kurs
    :param lonely_task: zadanie do wstawienia
    :param insertion_inx: indeks zadania, po którym należy wstawić
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :return: gotowy kurs lub None, jeśli naprawa drogi po wstawieniu jest niemożliwa
    """

    route_tmp = deepcopy(route)
    all_modes = get_all_travel_modes(travel_modes, transit_modes)

    locations = [route_tmp[insertion_inx].location, lonely_task.location]
    if insertion_inx == 0:
        matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes,
                                              route_tmp[insertion_inx].end_date_time)[0]
    else:
        if route_tmp[insertion_inx].travel_method == 'driving':
            car_enabled = True
            bike_enabled = False
            others_enabled = False
        elif route_tmp[insertion_inx].travel_method == 'bicycling':
            car_enabled = False
            bike_enabled = True
            others_enabled = False
        else:
            car_enabled = False
            bike_enabled = False
            others_enabled = True
        matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes,
                                              route_tmp[insertion_inx].end_date_time, car_enabled=car_enabled,
                                              bike_enabled=bike_enabled, others_enabled=others_enabled)[0]

    distances = []
    for matrix in matrixes:  # uzyskanie odległości z macierzy
        distance = matrix[0][1]
        distances.append(distance)
    travel_time = min(distances)

    matrix_inx = distances.index(travel_time)
    arrival_time = route_tmp[insertion_inx].end_date_time + travel_time * minutes
    waiting_time = route_tmp[insertion_inx + 1].get_waiting_time(arrival_time)
    start_time = arrival_time + waiting_time * minutes
    end_time = start_time + lonely_task.duration * minutes
    lonely_task.set_start_end_date_time(start_time, end_time)
    lonely_task.travel_method = all_modes[matrix_inx]
    lonely_task.travel_time = travel_time
    route_tmp.insert(insertion_inx + 1, lonely_task)

    route_tmp = fix_route(route_tmp, insertion_inx, travel_modes, transit_modes)
    return route_tmp


def intra_route_reinsertion(route: List[Task], travel_modes: List[str], transit_modes: List[str] = []) \
        -> List[Task] | None:
    """
    Operator sąsiedztwa usuwający jedno losowe zadanie z kursu i szukający innych możliwych miejsc jego wstawienia.
    :param route: kurs
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły dotyczące komunikacji miejskiej
    :return: najlepszy ze znalezionych sąsiadów lub None
    """

    route_tmp = deepcopy(route)  # kopia oryginalnego kursu
    random_task = choice(route_tmp[1:-1])  # wybór losowego zadania

    # usunięcie zadania z kursu
    random_task_inx = route_tmp.index(random_task)  # indeks zadania w og kursie
    route_tmp.remove(random_task)

    # naprawa drogi od indeksu inx - 1
    route_tmp = fix_route(route_tmp, random_task_inx - 1, travel_modes, transit_modes)

    # znalezienie miejsc do wstawienia
    feasible_insertions, objectives = find_valid_insertion(route_tmp, random_task, travel_modes, transit_modes,
                                                           forbidden_inx=random_task_inx)
    # po analizie wszystkich możliwych wstawień
    if feasible_insertions:
        best = min(objectives)
        best_inx = objectives.index(best)
        best_inx = feasible_insertions[best_inx]

        route_tmp = single_insertion(route_tmp, random_task, best_inx, travel_modes, transit_modes)

        return route_tmp

    else:
        return None


def inter_route_shift(route1: List[Task], route2: List[Task]):
    pass


def clear_the_most_busy_day(solution):
    pass


def clear_the_least_busy_day(solution):
    pass


# TESTOWANIE
"""
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
"""
