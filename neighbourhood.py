# ALGORYTM OPTYMALIZACYJNY

from beautiful_date import *
from model_params import Task
from typing import List, Dict
from map_functions import get_distance_cost_matrixes
from copy import deepcopy
from init_heuristic import initial_solution, get_all_travel_modes, create_depot, display_solution
from random import choice, randint

inf = float('inf')


def depot_time_fix_tmp(route: List[Task]):
    """
    Dodawanie czasu zakończenia czekania w bazie.
    :param route: kurs
    :return: NIC
    """

    route[0].end_date_time = route[1].start_date_time - route[1].travel_time * minutes


def idle_times(solution: Dict[BeautifulDate, List[Task]]):
    """
    Czas oczekiwania w bazie.
    :param solution: rozwiązanie
    :return:
    """
    for key, route in solution.items():
        idle_time = route[0].end_date_time - key
        idle_time = idle_time.total_seconds() / 60
        route[0].idle_time = idle_time


def get_route_objective(route, weights=None):
    """
    Liczenie wartości funkcji celu z konkretnego kursu.
    :param route: kurs
    :param weights: wagi kryteriów funkcji celu
    :return: wartość objective
    """

    if weights is None:
        weights = [0.6, 0, 0.4]
    objective = 0

    for inx in range(len(route)):
        if inx == 0:
            continue
        elif inx == len(route) - 1:
            if route[inx].travel_cost == inf:
                objective += weights[0] * route[inx].travel_time
            else:
                objective += weights[0] * route[inx].travel_time + weights[1] * route[inx].travel_cost
        else:
            arrival_date_time = route[inx - 1].end_date_time + route[inx].travel_time * minutes
            waiting_time = route[inx].start_date_time - arrival_date_time
            waiting_time = waiting_time.total_seconds() / 60
            if route[inx].travel_cost == inf:
                objective += weights[0] * route[inx].travel_time + weights[2] * waiting_time
            else:
                objective += weights[0] * route[inx].travel_time + weights[1] * route[inx].travel_cost \
                             + weights[2] * waiting_time

    return objective


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
            waiting_time = route_tmp[i + 1].get_waiting_time(
                route_tmp[i].end_date_time - route_tmp[i].idle_time * minutes)
            if waiting_time is None:
                return None
            # jeśli można poczekać w bazie to czekam w bazie na otwarcie i dla tego czasu sprawdzam dojazdy
            opening_time = route_tmp[i].end_date_time - route_tmp[i].idle_time * minutes + waiting_time * minutes
            matrixes, cost_matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, opening_time)
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
            matrixes, cost_matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes,
                                                                 route_tmp[i].end_date_time, car_enabled=car_enabled,
                                                                 bike_enabled=bike_enabled,
                                                                 others_enabled=others_enabled)
        distances = []
        for matrix in matrixes:  # uzyskanie odległości z macierzy
            distance = matrix[0][1]
            distances.append(distance)
        # wybór najlepszego z indeksem odpowiedniej metody transportu
        travel_time = min(distances)  # uwaga, trzeba pilnować, żeby nie był inf
        matrix_inx = distances.index(travel_time)
        if i == 0:  # przybycie na miejsce - czas z macierzy + czas podróży
            arrival_time = route_tmp[i].end_date_time - route_tmp[i].idle_time * minutes + waiting_time * minutes \
                           + travel_time * minutes
        else:
            arrival_time = route_tmp[i].end_date_time + travel_time * minutes
        waiting_time = route_tmp[i + 1].get_waiting_time(arrival_time)
        if waiting_time is None:  # waiting time zły -> naprawa niedopuszczalna
            return None
        start_time = arrival_time + waiting_time * minutes

        # aktualizacja godzin start/end (nw czy baza powinna mieć end_time, więc dlatego jest if)
        if route_tmp[i + 1].name != 'Dom':
            end_time = start_time + route_tmp[i + 1].duration * minutes
            route_tmp[i + 1].set_start_end_date_time(start_time, end_time)
        else:
            route_tmp[i + 1].start_date_time = start_time

        # aktualizacja parametrów transportu
        route_tmp[i + 1].set_travel_parameters(all_modes[matrix_inx], travel_time, cost_matrixes[matrix_inx][0][1])

    return route_tmp


def find_valid_insertion(route: List[Task], lonely_task: Task, travel_modes: List[str],
                         transit_modes: List[str] = [], forbidden_inx=None):
    """
    Funkcja znajdująca dopuszczalne wstawienia w kursie.
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

    # na początku sprawdzić, czy zadanie tego dnia jest dostępne!
    if not lonely_task.is_available_today(route_tmp[0].end_date_time - route_tmp[0].idle_time * minutes):
        return feasible_insertions, objectives

    for i in range(len(route_tmp) - 2):  # range to liczba krawędzi
        if forbidden_inx is not None:
            if i == forbidden_inx - 1:  # pominięcie og miejsca
                continue

        locations = [route_tmp[i].location, lonely_task.location]
        if i == 0:
            waiting_time = route_tmp[i + 1].get_waiting_time(
                route_tmp[i].end_date_time - route_tmp[i].idle_time * minutes)
            if waiting_time is None:
                continue
            # jeśli można poczekać w bazie, to czekam w bazie na otwarcie i dla tego czasu sprawdzam dojazdy
            opening_time = route_tmp[i].end_date_time - route_tmp[i].idle_time * minutes + waiting_time * minutes
            matrixes, cost_matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, opening_time)
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
            matrixes, cost_matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes,
                                                                 route_tmp[i].end_date_time, car_enabled=car_enabled,
                                                                 bike_enabled=bike_enabled,
                                                                 others_enabled=others_enabled)
        distances = []
        for matrix in matrixes:  # uzyskanie odległości z macierzy
            distance = matrix[0][1]
            distances.append(distance)
        travel_time = min(distances)

        matrix_inx = distances.index(travel_time)
        if i == 0:
            arrival_time = route_tmp[i].end_date_time - route_tmp[i].idle_time * minutes + waiting_time * minutes \
                           + travel_time * minutes
        else:
            arrival_time = route_tmp[i].end_date_time + travel_time * minutes
        waiting_time = lonely_task.get_waiting_time(arrival_time)
        # jeśli zadanie nie może być wykonane w określonej porze tego dnia, to odrzucenie tego wstawiena
        if waiting_time is None:
            continue
        # jeśli można poczekać, to akceptacja wstawienia
        start_time = arrival_time + waiting_time * minutes
        end_time = start_time + lonely_task.duration * minutes
        lonely_task.set_start_end_date_time(start_time, end_time)
        lonely_task.set_travel_parameters(all_modes[matrix_inx], travel_time, cost_matrixes[matrix_inx][0][1])
        route_tmp.insert(i + 1, lonely_task)  # wstawienie do drogi tmp

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
    Funkcja realizująca wstawienie punktu do kursu.
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
        waiting_time = route_tmp[insertion_inx + 1].get_waiting_time(route_tmp[insertion_inx].end_date_time
                                                                     - route_tmp[insertion_inx].idle_time * minutes)
        if waiting_time is None:
            return None
        opening_time = route_tmp[insertion_inx].end_date_time - route_tmp[insertion_inx].idle_time * minutes \
                       + waiting_time * minutes
        matrixes, cost_matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, opening_time)
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
        matrixes, cost_matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes,
                                                             route_tmp[insertion_inx].end_date_time,
                                                             car_enabled=car_enabled, bike_enabled=bike_enabled,
                                                             others_enabled=others_enabled)
    distances = []
    for matrix in matrixes:  # uzyskanie odległości z macierzy
        distance = matrix[0][1]
        distances.append(distance)
    travel_time = min(distances)

    matrix_inx = distances.index(travel_time)
    if insertion_inx == 0:
        arrival_time = route_tmp[insertion_inx].end_date_time - route_tmp[insertion_inx].idle_time * minutes\
                       + waiting_time * minutes + travel_time * minutes
    else:
        arrival_time = route_tmp[insertion_inx].end_date_time + travel_time * minutes
    waiting_time = route_tmp[insertion_inx + 1].get_waiting_time(arrival_time)
    if waiting_time is None:
        return None
    start_time = arrival_time + waiting_time * minutes
    end_time = start_time + lonely_task.duration * minutes
    lonely_task.set_start_end_date_time(start_time, end_time)
    lonely_task.set_travel_parameters(all_modes[matrix_inx], travel_time, cost_matrixes[matrix_inx][0][1])

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


def verify_shift(route: List[Task], next_route: List[Task]):
    """
    Funkcja sprawdzająca, czy po edycji kursu czekanie w bazie jest opłacalne.
    :param route: kurs
    :param next_route: kolejny kurs
    :return: tak/nie
    """

    date1 = route[-1].start_date_time
    date2 = next_route[0].end_date_time

    only_date1 = (D @ date1.day / date1.month / date1.year)[00:00]
    only_date2 = (D @ date2.day / date2.month / date2.year)[00:00]

    # kolejny kurs jest już innego dnia -> w porządku
    if only_date1 < only_date2:
        return True
    # kolejny kurs jest tego samego dnia, ale czekanie w bazie wynosi przynajmniej 90 minut
    elif (date2 - date1).total_seconds() / 60 >= 90:
        return True
    # zbyt krótkie czekanie w bazie -> zmiana nie jest opłacalna
    else:
        return False


def inter_route_shift(route1: List[Task], route2: List[Task], route3: List[Task] | None, travel_modes: List[str],
                      transit_modes: List[str] = []):
    """
    NIETESTOWANE! Funkcja przenosząca zadanie z kursu 1. do kursu 2.
    :param route1: kurs 1.
    :param route2: kurs 2.
    :param route3: kurs 3. (kolejny w rozwiązaniu po 2.)
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :return: zmodyfikowane kursy lub None, jeśli się nie udało
    """

    route1_tmp = deepcopy(route1)
    route2_tmp = deepcopy(route2)

    # usunięcie zadania z kursu 1.
    random_task = choice(route1_tmp[1:-1])
    random_task_inx = route1_tmp.index(random_task)
    route1_tmp.remove(random_task)
    route1_tmp = fix_route(route1, random_task_inx, travel_modes, transit_modes)
    if route1_tmp is None:
        return None

    # znalezienie valid wstawień w kursie 2.
    feasible_insertions, objectives = find_valid_insertion(route2_tmp, random_task, travel_modes, transit_modes)
    if feasible_insertions:
        best = min(objectives)
        best_inx = objectives.index(best)
        best_inx = feasible_insertions[best_inx]
        route2_tmp = single_insertion(route2_tmp, random_task, best_inx, travel_modes, transit_modes)
        # weryfikacja w alg. głównym
        return route1_tmp, route2_tmp
    else:
        return None


def count_tasks_daily(solution: Dict[BeautifulDate, List[Task]], day: BeautifulDate):
    """
    Funkcja zliczająca wykonane zadania w ciągu 1 dnia.
    :param solution: rozwiązanie
    :param day: data d/m/y [00:00]
    :return: liczba zadań
    """

    task_count = 0
    for start_date, route in solution.items():
        if day == (D @ start_date.day / start_date.month / start_date.year)[00:00]:
            task_count += len(route) - 1

    return task_count


def pick_the_last_task_daily(solution: Dict[BeautifulDate, List[Task]], day: BeautifulDate, travel_modes: List[str],
                             transit_modes: List[str] = []):
    """
    Funkcja usuwająca ostatnie zadanie w ciągu wybranego dnia.
    :param solution: rozwiązanie
    :param day: dzień
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :return: skrócony kurs i samotne zadanie
    """

    routes_tmp = []

    # uzyskanie listy kursów z dnia
    for start_date, route in solution.items():
        if day == (D @ start_date.day / start_date.month / start_date.year)[00:00]:
            routes_tmp.append(deepcopy(route))

    route_tmp = routes_tmp[-1]  # ostatni kurs
    length = len(route_tmp)
    lonely_task = route_tmp.pop(-2)  # usunięcie ostatniego zadania
    if length > 3:  # dla kursów wielozadaniowych
        # none nie powinien się zdarzyć
        route_tmp = fix_route(route_tmp, length - 3, travel_modes, transit_modes)  # naprawa kursu - wcześniejszy powrót
    else:  # dla jednozadaniowych (lista ma 3 elementy)
        route_tmp = []  # usunięcie drogi

    return route_tmp, lonely_task


def replace_route(solution: Dict[BeautifulDate, List[Task]], new_route: List[Task], lonely_task: Task):
    """
    Podmiana kursu.
    :param solution: rozwiązanie
    :param new_route: nowy kurs
    :param lonely_task: zadanie do indentyfiakcji, który kurs ma być podmieniony
    :return: zmodyfikowane rozwiązanie
    """

    for start_date, route in solution.items():
        if lonely_task in route:
            solution[start_date] = new_route

    return solution


def generate_short_route(depot: Task, task: Task, current_time: BeautifulDate, travel_modes: List[str],
                         transit_modes: List[str]):
    """
    Funkcja tworząca krótki kurs baza-zadanie-baza.
    :param depot: baza
    :param task: zadanie
    :param current_time: obecna chwila czasowa
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :return: nowy kurs
    """

    if not task.is_available_today(current_time):
        return None

    # minimalizacja czekania (nie powinno go już być potem tj. arrival=start)
    waiting_time = task.get_waiting_time(current_time)
    if waiting_time is None:
        return None
    elif waiting_time != 0:
        current_time = current_time + waiting_time * minutes

    last_stop = deepcopy(depot)
    all_modes = get_all_travel_modes(travel_modes, transit_modes)
    locations = [last_stop.location, task.location]
    matrixes, cost_matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, current_time)
    distances = []
    for matrix in matrixes:
        distances.append(matrix[0][1])
    min_distance = min(distances)
    min_inx = distances.index(min_distance)

    arrival_time = current_time + min_distance * minutes
    end_time = arrival_time + task.duration * minutes
    task.set_start_end_date_time(arrival_time, end_time)
    task.travel_time = min_distance
    task.travel_method = all_modes[min_inx]
    task.set_travel_parameters(all_modes[min_inx], min_distance, cost_matrixes[min_inx][0][1])
    depot.end_date_time = current_time

    short_route = [depot, task]

    # droga powrotna
    matrixes, cost_matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, end_time)
    distances = []
    for matrix in matrixes:
        distances.append(matrix[1][0])
    min_distance = min(distances)
    min_inx = distances.index(min_distance)

    last_stop.start_date_time = current_time + min_distance * minutes
    task.set_travel_parameters(all_modes[min_inx], min_distance, cost_matrixes[min_inx][0][1])
    short_route.append(last_stop)

    return short_route


def shift_from_the_most_busy_day(solution: Dict[BeautifulDate, List[Task]], T_begin: BeautifulDate,
                                 T_end: BeautifulDate, travel_modes: List[str], transit_modes: List[str] = []):
    """
    NIETESTOWANE! Operator sąsiedztwa - przenosi ostatnie zadanie z najbardziej zajętego dnia na inny.
    :param solution: rozwiązanie
    :param T_begin: początek harmonogramu
    :param T_end: koniec harmonogramu
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :return: zmodyfikowane rozwiązanie albo og, jeśli zmiany się nie powiodły
    """

    begin_date = (D @ T_begin.day / T_begin.month / T_begin.year)[00:00]
    end_date = (D @ T_end.day / T_end.month / T_end.year)[00:00]

    current_date = begin_date
    most_busy_day = None
    task_count = 0

    # pętla znajdująca najbardziej zajęty dzień
    while current_date > end_date:
        task_count_tmp = count_tasks_daily(solution, current_date)
        if task_count_tmp > task_count and task_count_tmp != 0:
            task_count = task_count_tmp
            most_busy_day = current_date

    # wybór ostaniego zadania z ostatniego kursu
    route_tmp, lonely_task = pick_the_last_task_daily(solution, most_busy_day, travel_modes, transit_modes)

    # wybór dnia na wstawienie nowego zadania
    num_days = (end_date - begin_date).total_seconds() / 60 / 60 / 24
    num_days = int(num_days)

    # wyznaczenie innego, losowego dnia
    new_day = current_date
    while current_date == new_day:
        delta_days = randint(1, num_days)
        if delta_days == 0:
            new_day = begin_date + delta_days * day
        else:
            new_day = begin_date + delta_days * days

    # dla tego dnia trzeba zrobić wstawienie
    insertion = False
    short_route = None
    for start_date, route in solution.items():
        # jeśli ten dzień już coś ma -> wstawić do kursu (pierwszego możliwego)
        if new_day == (D @ start_date.day / start_date.month / start_date.year)[00:00]:
            feasible_insertions, objectives = find_valid_insertion(route, lonely_task, travel_modes, transit_modes)
            if feasible_insertions:
                best = min(objectives)
                best_inx = objectives.index(best)
                best_inx = feasible_insertions[best_inx]
                route = single_insertion(route, lonely_task, best_inx, travel_modes, transit_modes)
                if route is not None:
                    solution[start_date] = route    # wstawienie aktualizacji w nowym dniu
                    insertion = True
                else:
                    return solution     # jak się nie udało, to zakończ
            break

        # w przypadku, gdy okazało się, że w wybranym dniu nic nie ma
        elif new_day < (D @ start_date.day / start_date.month / start_date.year)[00:00]:
            depot = deepcopy(route[0])
            short_route = generate_short_route(depot, lonely_task, new_day, travel_modes, transit_modes)
            break

    if insertion:  # jeśli wstawienie się powiodło - podmiana kursu na skrócony
        solution_tmp = deepcopy(solution)
        solution_tmp = replace_route(solution_tmp, route_tmp, lonely_task)      # update tego og. zajętego dnia
        return solution_tmp
    elif short_route is not None:  # jeśli został stworzony nowy kurs - podmiana i dodanie nowego kursu do rozwiązania
        solution_tmp = deepcopy(solution)
        solution_tmp = replace_route(solution_tmp, route_tmp, lonely_task)
        solution_tmp[short_route[0].end_date_time] = short_route        # dodaje całkowicie nowy dzień do rozwiązania
        return solution_tmp
    else:
        return solution


def shift_from_the_least_busy_day(solution: Dict[BeautifulDate, List[Task]], T_begin: BeautifulDate,
                                  T_end: BeautifulDate, travel_modes: List[str], transit_modes: List[str] = []):
    """
    NIETESTOWANE! Operator sąsiedztwa - przenosi ostatnie zadanie z najbardziej zajętego dnia na inny.
    :param solution: rozwiązanie
    :param T_begin: początek harmonogramu
    :param T_end: koniec harmonogramu
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :return: zmodyfikowane rozwiązanie
    """

    begin_date = (D @ T_begin.day / T_begin.month / T_begin.year)[00:00]
    end_date = (D @ T_end.day / T_end.month / T_end.year)[00:00]

    current_date = begin_date
    least_busy_day = None
    task_count = inf

    # pętla znajdująca najmniej zajęty dzień
    while current_date > end_date:
        task_count_tmp = count_tasks_daily(solution, current_date)
        if task_count_tmp < task_count:
            task_count = task_count_tmp
            least_busy_day = current_date

    # wybór ostatniego zadania
    route_tmp, lonely_task = pick_the_last_task_daily(solution, least_busy_day, travel_modes, transit_modes)

    num_days = (end_date - begin_date).total_seconds() / 60 / 60 / 24
    num_days = int(num_days)

    # wyznaczenie innego, losowego dnia
    new_day = current_date
    while current_date == new_day:
        delta_days = randint(1, num_days)
        if delta_days == 0:
            new_day = begin_date + delta_days * day
        else:
            new_day = begin_date + delta_days * days

    # dla tego dnia trzeba zrobić wstawienie
    insertion = False
    short_route = None
    for start_date, route in solution.items():
        # jeśli ten dzień już coś ma -> wstawić do kursu (pierwszego możliwego)
        if new_day == (D @ start_date.day / start_date.month / start_date.year)[00:00]:
            feasible_insertions, objectives = find_valid_insertion(route, lonely_task, travel_modes, transit_modes)
            if feasible_insertions:
                best = min(objectives)
                best_inx = objectives.index(best)
                best_inx = feasible_insertions[best_inx]
                route = single_insertion(route, lonely_task, best_inx, travel_modes, transit_modes)
                if route is not None:
                    solution[start_date] = route  # wstawienie aktualizacji w nowym dniu
                    insertion = True
                else:
                    return solution  # jak się nie udało, to zakończ
            break

            # w przypadku, gdy okazało się, że w wybranym dniu nic nie ma
        elif new_day < (D @ start_date.day / start_date.month / start_date.year)[00:00]:
            depot = deepcopy(route[0])
            short_route = generate_short_route(depot, lonely_task, new_day, travel_modes, transit_modes)
            break

    if insertion:  # jeśli wstawienie się powiodło - podmiana kursu na skrócony
        solution_tmp = deepcopy(solution)
        if len(route_tmp) == 2:     # jeśli w tym dniu została tylko baza-baza, to usuwany jest ten kurs
            del solution_tmp[least_busy_day]
        else:
            solution_tmp = replace_route(solution_tmp, route_tmp, lonely_task)  # update tego og. zajętego dnia
        return solution_tmp
    elif short_route is not None:  # jeśli został stworzony nowy kurs - podmiana i dodanie nowego kursu do rozwiązania
        solution_tmp = deepcopy(solution)
        solution_tmp = replace_route(solution_tmp, route_tmp, lonely_task)
        solution_tmp[short_route[0].end_date_time] = short_route  # dodaje całkowicie nowy dzień do rozwiązania
        return solution_tmp
    else:
        return solution


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
modes = ["walking"]       
transit_modes = []

solution, finished = initial_solution((D @ 9/12/2024)[8:00], (D @ 15/12/2024)[22:00], tasks, modes, transit_modes)
display_solution(solution)

route_test = solution[(D @ 9/12/2024)[8:00]]
depot_time_fix_tmp(route_test)
route_test_prim = intra_route_reinsertion(route_test, modes, transit_modes)
"""
