# IMPLEMENTACJA HEURYSTYKI DO GENERACJI ROZWIĄZANIA POCZĄTKOWEGO / SĄSIEDZTWA

from beautiful_date import *
from model_params import Task, Route, set_idle_time
from typing import List, Dict
from map_functions import get_distance_cost_matrixes, get_distance_cost_matrixes
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


def get_quickest_return(task_inx: int, matrixes: List[List[List]], current_time: BeautifulDate, all_modes, car_enabled=True, bike_enabled=True, others_enabled=True):
    """
    Funkcja znajdująca najszybszy sposób powrotu do bazy.
    :param task_inx: indeks ostatniego wykonanego zadania
    :param matrixes: macierze odległości (ew. kosztów)
    :param current_time: obecna chwila czasowa
    :return: czas powrotu, indeks wykorzystanej macierzy
    """

    distances = []
    for matrix in matrixes:
        inx = matrixes.index(matrix)
        if all_modes[inx] == "driving" and not car_enabled:
            distances.append(inf)
        elif all_modes[inx] == "bicycling" and not bike_enabled:
            distances.append(inf)
        elif all_modes[inx] in ["walking", "bus", "tram", "rail"] and not others_enabled:
            distances.append(inf)
        else:
            distances.append(matrix[0][0])      # macierz ma zawsze tylko 1 rząd

    min_distance = min(distances)
    matrix_inx = distances.index(min_distance)

    return min_distance, matrix_inx


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


def route_end_valid(task_inx, next_task_inx, matrixes, cost_matrixes, tasks, current_time, finished, all_modes):

    """
    Funkcja sprawdzająca, czy opłacalny jest powrót do bazy mimo dostępnych zadań.
    :param task_inx: indeks ostatniego zadania
    :param next_task_inx: indeks potencjalnego następnego zadania
    :param matrixes: macierze odległości
    :param cost_matrixes: macierze kosztów
    :param tasks: lista zadań
    :param current_time: obecna chwila czasowa
    :param finished: lista indeksów wykonanych zadań
    :param all_modes: lista z nazwami wszystkich metod transportu
    :return: najlepszy czas powrotu do bazy, indeks odpowiedniej macierzy (inf oznacza, że powrót nie jest opłacalny)
    """

    ends = []
    return_times = []
    return_costs = []
    locations_tmp = get_tasks_locations(tasks)

    # waiting_time = czas od current_time do next_task_start
    waiting_time = tasks[next_task_inx].get_waiting_time(current_time)

    for matrix in matrixes:
        # czekanie jest krótsze niż powrót do bazy - nie opłaca się wracać
        # ten warunek rozwiązuje też zablokowane transporty z inf
        if waiting_time < matrix[0][0]:
            ends.append(False)
            return_times.append(inf)
            return_costs.append(inf)

        else:   # wyznaczenie potencjalnego najbliższego zadania po powrocie, nie trzeba sprawdzać car/bike, bo do funkcji przekazywane są macierze inf, jeśli to jest zablokowane
            return_time = matrix[0][0]
            current_time += return_time * minutes
            # ponowna generacja macierzy (dla konkretnie przetwarzanego środka transportu)
            matrix_inx = matrixes.index(matrix)
            return_cost = cost_matrixes[matrix_inx][0][0]
            if all_modes[matrix_inx] in ['bus', 'tram', 'rail']:
                travel_mode = ['transit']
                transit_mode = [all_modes[matrix_inx]]
            else:
                travel_mode = [all_modes[matrix_inx]]
                transit_mode = []
            # jako że to jest już wyznaczenie po powrocie, to trzeba wyznaczyć nowe zaktualizowane macierze (wszystkie metody są potencjalnie możliwe)
            matrixes_tmp, cost_matrixes_tmp = get_distance_cost_matrixes([tasks[0].location], locations_tmp, travel_mode, transit_mode,
                                                                         current_time)
            # wyczyszczenie odległości z tych już wykonanych
            for m in range(len(matrixes_tmp)):
                for row in range(len(matrixes_tmp)):
                    for inx in finished:
                        matrixes_tmp[m][row][inx] = inf
                        cost_matrixes_tmp[m][row][inx] = inf
            next_task_inx_tmp, matrix_inx_tmp = get_available_nearest(0, matrixes_tmp, tasks, current_time, finished)

            # jeśli nie ma zadań na ten dzień
            if next_task_inx_tmp == inf:
                # należy sprawdzić, co się stało z next_task - czy będzie dostępne innego dnia?
                # przekroczenie okna czasowego - nie dobrze
                window_right = tasks[next_task_inx].window_right
                if window_right < current_time + tasks[next_task_inx].duration * minutes:
                    end.append(False)
                    return_times.append(inf)
                    return_costs.append(inf)

                # sprawdzanie czy jest inny dzień, w którym zadanie jest dostępne
                else:
                    current_time_tmp = current_time + 1 * day   # nw czy to zmieniać na days czy nie
                    current_time_tmp = (D @ current_time_tmp.day/current_time_tmp.month/current_time_tmp.year)[00:00]
                    window_right_tmp = (D @ window_right.day/window_right.month/window_right.year)[00:00]
                    found = False
                    while current_time_tmp <= window_right:     # szukanie innego dnia, w którym zadanie będzie dostępne
                        if tasks[next_task_inx].is_available_today(current_time_tmp):
                            end.append(True)        # przypadek, że opłaca się wracać, ale
                            return_times.append(return_time)
                            return_costs.append(return_cost)
                            break
                        current_time_tmp = current_time_tmp + 1 * day

                    # jeśli zadanie nie zostało znalezione w pętli, no to nie można zrobić przerwy
                    if not found:
                        end.append(False)
                        return_times.append(inf)
                        return_costs.append(inf)

            # znalezione zostało potencjalne następne zadanie w trasie
            else:
                waiting_time = tasks[next_task_inx_tmp].get_waiting_time(current_time)  # czas oczekiwania na zadanie
                travel_time = matrixes_tmp[matrix_inx_tmp][0][next_task_inx_tmp]   # czas podróży w nowej chwili czasowej

                if waiting_time - travel_time < 90:     # nie opłaca się wracać do bazy
                    ends.append(False)
                    return_times.append(inf)
                    return_costs.append(inf)
                else:
                    ends.append(True)           # opłaca się wracać
                    matrix_inx = matrixes.index(matrix)
                    return_times.append(return_time)
                    return_costs.append(return_cost)

    # wybor minimalnego jeśli jest jakiś true, że faktycznie warto wrocic
    possible_returns = []
    for inx in range(len(ends)):
        if ends[inx]:
            possible_returns.append(return_times[inx])

    if not possible_returns:    # jeśli w żadnej macierzy nie było możliwego powrotu - inf inf - powrót do bazy jest invalid
        return inf, inf, inf
    # jeśli był to należy wybrać ten najkrótszy i go zwrócić
    best_return = min(possible_returns)
    matrix_inx = return_times.index(best_return)
    best_cost = return_costs[matrix_inx]
    return best_return, matrix_inx, best_cost


def get_nearest(task_inx: int, matrix: List[List], tasks: List[Task], current_time: BeautifulDate,
                weights: List[float] = [0.4, 0.1, 0.5]):
    """
    Funkcja znajdująca następne zadanie o lokalizacji najbliższej obecnej.
    :param task_inx: indeks zadania
    :param matrix: macierze dystansów (ew. kosztów)
    :param tasks: lista zadań
    :param current_time: obecna chwila czasowa
    :param weights: wagi dotyczące poszczególnych kryteriów wyboru następnego zadania
    :return: indeks najbliższego zadania i wartość kosztu albo None, gdy takiego nie ma
    """

    results = [inf]  # ostateczne wyniki kryterium - baza zawsze jako inf
    task_distances = matrix[0]  # odległości od obecnego zadania do pozostałych
    if all(distance == inf for distance in task_distances[1:]):  # jeśli wszystko inf -- wszystko jest już odwiedzone (bez bazy)
        return inf, inf

    for inx in range(1, len(tasks)):    # od 1, bo depot nie jest sprawdzany
        if task_distances[inx] == inf or not tasks[inx].is_available_today(current_time):  # jeśli zadanie wykonane lub niemożliwe do realizacji dzisiaj
            results.append(inf)
        else:
            distance = task_distances[inx]  # odległość
            arrival_time = current_time + distance * minutes
            waiting_time = tasks[inx].get_waiting_time(arrival_time)  # czas oczekiwania na najwcześniejszy start
            if waiting_time is None:
                results.append(inf)
                continue
            current_time_plus = current_time + distance * minutes + tasks[inx].duration * minutes
            urgency = tasks[inx].window_right - current_time_plus  # pilność zadania
            urgency = urgency.total_seconds() / 60
            if urgency < 0:
                results.append(inf)
                continue
            else:
                result = weights[0] * distance + weights[1] * waiting_time + weights[2] * urgency
                results.append(result)

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


# funkcja kończąca kurs - dodaje przystanek końcowy bazę
def end_route(depot: Task, T_begin: BeautifulDate, T_end: BeautifulDate, current_task_inx: int,
              current_time: BeautifulDate, matrixes: List[List[List]], cost_matrixes, all_modes: List[str], route: List[Task],
              return_time = None, return_inx = None, car_enabled=True, bike_enabled=True, others_enabled=True):

    """
    Funkcja wykonująca kolejne kroki niezbędne do zakończenia kursu.
    :param depot: baza
    :param T_begin: czas rozpoczęcia harmonogramu
    :param T_end: czas zakończenia harmongramu
    :param current_task_inx: indeks ostatniego zadania
    :param current_time: obecna chwila czasowa
    :param matrixes: macierze odległości
    :param cost_matrixes: macierze kosztów
    :param all_modes: lista wszystkich metod transportu
    :param route: obecny kurs
    :param return_time: opcj. najlepszy czas powrotu do bazy - można podać, jeśli został wcześniej wyznaczony
    :param return_inx: opcj. indeks macierzy, z której uzyskany został powyższy czas
    :return: kurs z przystankiem końcowym
    """

    depot_last = create_depot(depot.location, T_begin, T_end)       # utworzenie bazy

    if return_time is None and return_inx is None:
        travel_time, matrix_inx = get_quickest_return(current_task_inx, matrixes, current_time, all_modes=all_modes, car_enabled=car_enabled, bike_enabled=bike_enabled, others_enabled=others_enabled)
        travel_method = all_modes[matrix_inx]
        travel_cost = cost_matrixes[matrix_inx][0][0]
        start_time = current_time + travel_time * minutes

    else:
        depot_last = create_depot(depot.location, T_begin, T_end)
        travel_method = all_modes[return_inx]
        travel_time = return_time
        travel_cost = cost_matrixes[return_inx][0][0]
        start_time = current_time + return_time * minutes

    depot_last.start_date_time = start_time
    depot_last.set_travel_parameters(travel_method, travel_time, travel_cost)
    route.append(depot_last)  # dołączenie bazy jako przystanka końcowego

    return route


def get_all_travel_modes(travel_modes: List[str], transit_modes: List[str] = []) -> List[str]:

    """
    Utworzenie listy ze wszystkimi wybranymi metodami transportu
    :param travel_modes: lista metod
    :param transit_modes: lista szczegółów komunikacji miejskiej
    :return: lista wszystkich metod
    """

    all_modes = []
    for mode in travel_modes:
        if mode == 'transit':
            for t_mode in transit_modes:
                all_modes.append(t_mode)
        else:
            all_modes.append(mode)
    return all_modes


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

    # utworzenie listy ze wszystkimi środkami transportu
    all_modes = get_all_travel_modes(travel_modes, transit_modes)

    solution = {}       # rozwiązanie
    objective = 0       # wartość funkcji celu

    current_time = T_begin  # obecna chwila
    depot = tasks[0]  # ustawienie bazy
    finished = [0]  # indeksy zadań nieodwiedzonych (baza jest odwiedzona)
    locations = get_tasks_locations(tasks)  # lista lokalizacji zadań

    car_enabled = True      # jakie środki są dostępne
    bike_enabled = True
    others_enabled = True

    while True:  # przetworzenie konkretnego dnia
        current_task = depot
        current_task_inx = tasks.index(current_task)
        route = [deepcopy(current_task)]  # kokretny kurs
        route_start_time = current_time

        while True:  # tworzenie konkretnego kursu
            # ustawienie warunków car/bike/others
            if current_task_inx == 0:   # na początku kursu - wszystkie są domyślnie true
                matrixes, cost_matrixes = get_distance_cost_matrixes([tasks[current_task_inx].location],
                                                                     locations, travel_modes, transit_modes,
                                                                     current_time)
            else:
                last_inx = finished[-1]     # indeks ostatniego zadania wykonanego w kursie
                if tasks[last_inx].travel_method == 'driving':
                    car_enabled = True
                    bike_enabled = False
                    others_enabled = False
                elif tasks[last_inx].travel_method == 'bicycling':
                    car_enabled = False
                    bike_enabled = True
                    others_enabled = False
                else:
                    car_enabled = False
                    bike_enabled = False
                    others_enabled = True
                matrixes, cost_matrixes = get_distance_cost_matrixes([tasks[current_task_inx].location],
                                                                     locations, travel_modes, transit_modes,
                                                                     current_time, car_enabled, bike_enabled,
                                                                     others_enabled)
            # stare dobre ahh czyszczenie - rachunek od googla is coming NO I PRZYSZEDL BYE
            for m in range(len(matrixes)):
                for row in range(len(matrixes[0])):
                    for inx in finished:
                        if inx != 0:
                            matrixes[m][row][inx] = inf
                            cost_matrixes[m][row][inx] = inf

            # wybór indeksu najbliższego zadania
            next_task_inx, matrix_inx = get_available_nearest(current_task_inx, matrixes, tasks, current_time, finished)
            # jeśli nie ma już nic odwiedzenia - zakończenie kursu, powrót do bazy
            if next_task_inx == inf or not tasks_available(tasks, finished, current_time):
                # jeśli droga faktycznie powstała (nie jest to sama baza), to ją zapisz
                if len(route) != 1:
                    if tasks[current_task_inx].travel_method == 'driving':
                        car_enabled = True
                        bike_enabled = False
                        others_enabled = False
                    elif tasks[current_task_inx].travel_method == 'bicycling':
                        car_enabled = False
                        bike_enabled = True
                        others_enabled = False
                    else:
                        car_enabled = False
                        bike_enabled = False
                        others_enabled = True
                    route = end_route(depot, T_begin, T_end, current_task_inx, current_time, matrixes, cost_matrixes,
                                      all_modes, route, car_enabled=car_enabled, bike_enabled=bike_enabled, others_enabled=others_enabled)
                    solution[route_start_time] = route
                    break
            else:  # jeśli wybór zadania był valid
                # zapisanie czasu rozpoczęcia i zakończenia
                travel_method = all_modes[matrix_inx]
                travel_cost = cost_matrixes[matrix_inx][0][next_task_inx]
                travel_time = matrixes[matrix_inx][0][next_task_inx]
                tasks[next_task_inx].set_travel_parameters(travel_method, travel_time, travel_cost)
                start_time = current_time + travel_time * minutes
                waiting_time = tasks[next_task_inx].get_waiting_time(start_time)    # czas oczekiwania
                if waiting_time is None:
                    if tasks[current_task_inx].travel_method == 'driving':
                        car_enabled = True
                        bike_enabled = False
                        others_enabled = False
                    elif tasks[current_task_inx].travel_method == 'bicycling':
                        car_enabled = False
                        bike_enabled = True
                        others_enabled = False
                    else:
                        car_enabled = False
                        bike_enabled = False
                        others_enabled = True
                    route = end_route(depot, T_begin, T_end, current_task_inx, current_time, matrixes, cost_matrixes,
                                      all_modes, route, car_enabled=car_enabled, bike_enabled=bike_enabled, others_enabled=others_enabled)
                    solution[route_start_time] = route  # zapisanie rozwiazania
                    break
                if waiting_time != 0:
                    if current_task_inx == 0:       # jeśli jest to wyjazd z bazy - wyjazd jak najpóźniej
                        # przewidywany moment rozpoczecia
                        travel_search_time = current_time + waiting_time * minutes - travel_time * minutes
                        # tutaj małe macierze szukające... TO BEDZIE MACIERZ 1 NA 1
                        matrixes_small, cost_matrixes_small = get_distance_cost_matrixes([depot.location], [tasks[next_task_inx].location], travel_modes, transit_modes,
                                                                                         travel_search_time)
                        arrival_time = travel_search_time + matrixes_small[matrix_inx][0][0] * minutes
                        new_waiting_time = tasks[next_task_inx].get_waiting_time(arrival_time)
                        start_time = arrival_time + new_waiting_time * minutes
                        tasks[next_task_inx].travel_cost = cost_matrixes[matrix_inx][0][0]
                    else:   # należy sprawdzić czy zamiast czekania lepiej wrócić
                        return_time, matrix_inx, return_cost = route_end_valid(current_task_inx, next_task_inx,
                                                                               matrixes, cost_matrixes, tasks,
                                                                               current_time, finished, all_modes)
                        if return_time != inf:      # opłacalny powrót!
                            route = end_route(depot, T_begin, T_end, current_task_inx, current_time, matrixes,
                                              cost_matrixes, all_modes, route, return_time, matrix_inx, car_enabled=car_enabled, bike_enabled=bike_enabled, others_enabled=others_enabled)
                            solution[route_start_time] = route  # zakończenie kursu
                            current_task = depot
                            current_task_inx = 0
                            route = [current_task]
                            # ... czy należy dodać tutaj waiting time as well??? albo chociaż to minimalne 90 min???
                            route_start_time = current_time + return_time * minutes
                            continue    # wykonywanie pętli od nowa - nowy kurs w ciągu dnia
                        else:
                            start_time = start_time + waiting_time*minutes      # powrót nieopłacalny - wykonywany jest znaleziony task

                end_time = start_time + tasks[next_task_inx].duration * minutes
                tasks[next_task_inx].set_start_end_date_time(start_time, end_time)
                route.append(tasks[next_task_inx])  # jeśli neighbour jest ok - dodaj go do kursu

                finished.append(next_task_inx)  # zapisz indeks zadania w wykonanych
                current_time = end_time         # udpate czasu
                current_task_inx = next_task_inx    # udpate ostatniego zadania

            if not tasks_available(tasks, finished, current_time) and len(route) != 1:      # sprawdzenie czy kurs można kontynuować - jeśli nie
                # powrót do bazy
                if tasks[current_task_inx].travel_method == 'driving':
                    car_enabled = True
                    bike_enabled = False
                    others_enabled = False
                elif tasks[current_task_inx].travel_method == 'bicycling':
                    car_enabled = False
                    bike_enabled = True
                    others_enabled = False
                else:
                    car_enabled = False
                    bike_enabled = False
                    others_enabled = True
                matrixes_small, cost_matrixes_small = get_distance_cost_matrixes([
                    tasks[current_task_inx].location], [depot.location], travel_modes, transit_modes, current_time,
                                                                                         car_enabled=car_enabled,
                                                                                         bike_enabled=bike_enabled,
                                                                                         others_enabled=others_enabled)
                route = end_route(depot, T_begin, T_end, current_task_inx, current_time, matrixes_small, cost_matrixes_small,
                                  all_modes, route, car_enabled=car_enabled, bike_enabled=bike_enabled, others_enabled=others_enabled)
                solution[route_start_time] = route      # zapisanie rozwiazania
                break
            elif len(route) == 1:
                break

        if len(finished) == len(tasks) or current_time >= T_end:     # jeśli wszystkie zadania zostały już wykonane albo czas przekroczony
            break

        if current_task_inx != 0:
            start_date_only = (D @ tasks[current_task_inx].start_date_time.day/tasks[current_task_inx].start_date_time.month/tasks[current_task_inx].start_date_time.year)[00:00]
            end_date_only = (D @ tasks[current_task_inx].end_date_time.day/tasks[current_task_inx].end_date_time.month/tasks[current_task_inx].end_date_time.year)[00:00]
            if start_date_only == end_date_only:     # jeśli koniec zadania nastąpił tego samego dnia (w przeciwnym wypadku czas jest kontyunowany)
                current_time = current_time + 24 * hours  # update daty przed rozpoczeciem petli nowego dnia
                current_time = (D @ current_time.day / current_time.month / current_time.year)[00:00]
        else:
            current_time = current_time + 24 * hours
            current_time = (D @ current_time.day / current_time.month / current_time.year)[00:00]

    return solution, finished

def dict_2_route(solution: Dict[BeautifulDate, List[Task]]):
    """
    Konwersja wygenerowanego rozwiązania początkowego do typu Route + idle times.
    :param solution: oryginalne rozwiązanie
    :return: nowy format rozwiązania
    """
    new_solution = []
    for key, value in solution.items():
        new_route = Route(key, value)
        new_solution.append(deepcopy(new_route))
    if not new_solution:
        return None

    for i in range(len(new_solution)):
        if i == 0:
            set_idle_time(new_solution[i], None)
        else:
            set_idle_time(new_solution[i], new_solution[i-1])

    return new_solution

