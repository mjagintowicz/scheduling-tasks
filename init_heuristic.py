# IMPLEMENTACJA HEURYSTYKI DO GENERACJI ROZWIĄZANIA POCZĄTKOWEGO / SĄSIEDZTWA

from beautiful_date import *
from model_params import Task
from typing import List, Dict
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


def get_quickest_return(task_inx: int, matrixes: List[List[List]], current_time: BeautifulDate):
    """
    Funkcja znajdująca najszybszy sposób powrotu do bazy.
    :param task_inx: indeks ostatniego wykonanego zadania
    :param matrixes: macierze odległości (ew. kosztów)
    :param current_time: obecna chwila czasowa
    :return: czas powrotu, indeks wykorzystanej macierzy
    """

    distances = []
    for matrix in matrixes:
        distances.append(matrix[task_inx][0])

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


def route_end_valid(task_inx, next_task_inx, matrixes, tasks, current_time, finished, travel_modes, transit_modes = []):

    ends = []
    return_times = []

    # utworzenie listy ze wszystkimi środkami transportu
    all_modes = []
    for mode in travel_modes:
        if mode == 'transit':
            for t_mode in transit_modes:
                all_modes.append(t_mode)
        else:
            all_modes.append(mode)

    # waiting_time = czas od current_time do next_task_start
    waiting_time = tasks[next_task_inx].get_waiting_time(current_time)

    for matrix in matrixes:
        # czekanie jest krótsze niż powrót do bazy - nie opłaca się wracać
        if waiting_time < matrix[task_inx][0]:
            ends.append(False)
            return_times.append(inf)

        else:
            return_time = matrix[task_inx][0]
            current_time += return_time * minutes
            # wyznaczenie potencjalnego najbliższego zadania po powrocie
            next_task_inx, matrix_inx = get_available_nearest(0, matrixes, tasks, current_time, finished)

            # jeśli nie ma zadań na ten dzień
            if next_task_inx == inf:
                # należy sprawdzić, co się stało z next_task - czy będzie dostępne innego dnia?
                # przekroczenie okna czasowego - nie dobrze
                window_right = tasks[next_task_inx].window_right
                if window_right < current_time + tasks[next_task_inx].duration * minutes:
                    end.append(False)
                    return_times.append(inf)
                # sprawdzanie czy jest inny dzień, w którym zadanie jest dostępne
                else:
                    current_time_tmp = current_time + 1 * day
                    current_time_tmp = (D @ current_time_tmp.day/current_time_tmp.month/current_time_tmp.year)[00:00]
                    window_right_tmp = (D @ window_right.day/window_right.month/window_right.year)[00:00]

                    found = False
                    while current_time_tmp <= window_right:     # szukanie innego dnia, w którym zadanie będzie dostępne
                        if tasks[next_task_inx].is_available_today(current_time_tmp):
                            end.append(True)
                            return_times.append(return_time)
                            break
                        current_time_tmp = current_time_tmp + 1 * day
                    # jeśli zadanie nie zostało znalezione w pętli, no to sory nie można zrobić przerwy (wszyscy wiemy, że do takiej sytuacji nigdy nie dojdzie)
                    if not found:
                        end.append(False)
                        return_times.append(inf)

            # znalezione zostało potencjalne następne zadanie w trasie
            else:
                waiting_time = tasks[next_task_inx].get_waiting_time(current_time)  # czas oczekiwania na zadanie
                # wyznaczenie nowej macierzy odległości (ew. kosztu), rozmiar 4x4 (baza, next_task)
                locations = [tasks[0].location, tasks[next_task_inx].location]
                matrix_inx = matrixes.index(matrix)
                if all_modes[matrix_inx] in ['bus', 'tram', 'rail']:
                    travel_mode = ['transit']
                    transit_mode = [all_modes[matrix_inx]]
                else:
                    travel_mode = [all_modes[matrix_inx]]
                    transit_mode = []

                matrix_tmp = get_distance_cost_matrixes(locations, travel_mode, transit_mode, current_time)[0]
                travel_time = matrix_tmp[0][0][1]   # czas podróży w nowej chwili czasowej

                if waiting_time - travel_time < 90:     # nie opłaca się wracać do bazy
                    ends.append(False)
                    matrix_inxs.append(inf)
                    return_times.append(inf)
                else:
                    ends.append(True)           # opłaca się wracać
                    matrix_inx = matrixes.index(matrix)
                    matrix_inxs.append(matrix_inx)
                    return_times.append(return_time)

    # wybor minimalnego jeśli jest jakiś true, że faktycznie warto wrocic
    possible_returns = []
    for inx in range(len(ends)):
        if ends[inx]:
            possible_returns.append(return_times[inx])

    if not possible_returns:    # jeśli w żadnej macierzy nie było możliwego powrotu - inf inf - powrót do bazy jest invalid
        return inf, inf
    # jeśli był to należy wybrać ten najkrótszy i go zwrócić
    best_return = min(possible_returns)
    matrix_inx = return_times.index(best_return)
    return best_return, matrix_inx


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

    # utworzenie listy ze wszystkimi środkami transportu
    all_modes = []
    for mode in travel_modes:
        if mode == 'transit':
            for t_mode in transit_modes:
                all_modes.append(t_mode)
        else:
            all_modes.append(mode)

    solution = {}       # rozwiązanie
    objective = 0       # wartość funkcji celu

    current_time = T_begin  # obecna chwila
    depot = tasks[0]  # ustawienie bazy
    finished = [0]  # indeksy zadań nieodwiedzonych (baza jest odwiedzona)
    locations = get_tasks_locations(tasks)  # lista lokalizacji zadań

    while True:  # przetworzenie konkretnego dnia
        current_task = depot
        current_task_inx = tasks.index(current_task)
        route = [current_task]  # kokretny kurs
        route_start_time = current_time

        while True:  # tworzenie konkretnego kursu
            # ... WARUNEK SAMOCHODU/ROWERU
            # uzyskanie macierzy odległości
            # ... (ew. kosztów)
            matrixes = get_distance_cost_matrixes(locations, travel_modes, transit_modes, current_time)[0]
            # usunięcie z macierzy niepotrzebnych już danych
            for matrix in matrixes:
                for col in range(len(matrix[0])):
                    for inx in finished:
                        if inx != 0:
                            matrix[col][inx] = inf

            # wybór indeksu najbliższego zadania
            next_task_inx, matrix_inx = get_available_nearest(current_task_inx, matrixes, tasks, current_time, finished)
            # jeśli nie ma już nic odwiedzenia - zakończenie kursu, powrót do bazy
            if next_task_inx == inf or not tasks_available(tasks, finished, current_time):
                # jeśli droga faktycznie powstała (nie jest to sama baza), to ją zapisz
                if len(route) != 1:
                    depot_last = create_depot(depot.location, T_begin, T_end)
                    travel_time, matrix_inx = get_quickest_return(current_task_inx, matrixes, current_time)
                    depot_last.travel_method = all_modes[matrix_inx]
                    start_time = current_time + travel_time * minutes
                    depot_last.start_date_time = start_time
                    route.append(depot_last)     # dołączenie bazy jako przystanka końcowego
                    solution[route_start_time] = route
                break
            else:  # jeśli wybór zadania był valid
                # zapisanie czasu rozpoczęcia i zakończenia
                # przypadki, że transit...
                tasks[next_task_inx].travel_method = all_modes[matrix_inx]
                travel_time = matrixes[matrix_inx][current_task_inx][next_task_inx]
                start_time = current_time+travel_time * minutes
                waiting_time = tasks[next_task_inx].get_waiting_time(start_time)    # czas oczekiwania
                if waiting_time != 0:
                    if current_task_inx == 0:       # jeśli jest to wyjazd z bazy - wyjazd jak najpóźniej
                        travel_search_time = current_time + waiting_time * minutes
                        # ... update travel time, póki co zostaje domyślnie poprzedni
                        start_time = travel_search_time + travel_time * minutes
                    else:   # należy sprawdzić czy zamiast czekania lepiej wrócić
                        # ... SPRAWDZENIE CZY TRAVEL MODES SĄ ZGODNE (CAR, BIKE)
                        return_time, matrix_inx = route_end_valid(current_task_inx, next_task_inx, tasks, current_time, finished, travel_modes, transit_modes)
                        if return_time != inf:      # opłacalny powrót!
                            depot_last = create_depot(depot.location, T_begin, T_end)
                            depot_last.travel_method = all_modes[matrix_inx]
                            start_time = current_time + travel_time * minutes
                            depot_last.start_date_time = start_time
                            route.append(depot_last)
                            solution[route_start_time] = route  # zakończenie kursu
                            current_task = depot
                            current_task_inx = tasks.index(current_task)
                            route = [current_task]
                            # ... czy należy dodać tutaj waiting time as well??? albo chociaż to minimalne 90 min???
                            route_start_time = current_time
                            continue    # wykonywanie pętli od nowa - nowy kurs w ciągu dnia
                        else:
                            start_time = start_time + waiting_time*minutes      # powrót nieopłacalny - wykonywany jest znaleziony task

                end_time = start_time + tasks[next_task_inx].duration * minutes
                tasks[next_task_inx].set_start_end_date_time(start_time, end_time)
                route.append(tasks[next_task_inx])  # jeśli neighbour jest ok - dodaj go do kursu

                finished.append(next_task_inx)  # zapisz indeks zadania w wykonanych
                current_time = end_time         # udpate czasu
                current_task_inx = next_task_inx    # udpate ostatniego zadania

            if not tasks_available(tasks, finished, current_time):      # sprawdzenie czy kurs można kontynuować - jeśli nie
                # powrót do bazy
                depot_last = create_depot(depot.location, T_begin, T_end)
                travel_time, matrix_inx = get_quickest_return(current_task_inx, matrixes, current_time)
                depot_last.travel_method = modes[matrix_inx]
                start_time = current_time + travel_time * minutes
                depot_last.start_date_time = start_time
                route.append(depot_last)
                solution[route_start_time] = route      # zapisanie rozwiazania
                break

        if len(finished) == len(tasks) or current_time >= T_end:     # jeśli wszystkie zadania zostały już wykonane albo czas przekroczony
            break

        start_date_only = (D @ start_time.day/start_time.month/start_time.year)[00:00]
        end_date_only = (D @ end_time.day/end_time.month/end_time.year)[00:00]
        if start_date_only == end_date_only:     # jeśli koniec zadania nastąpił tego samego dnia (w przeciwnym wypadku czas jest kontyunowany)
            current_time = current_time + 24 * hours  # update daty przed rozpoczeciem petli nowego dnia
            current_time = (D @ current_time.day / current_time.month / current_time.year)[00:00]

    return solution, finished


def get_distance_objective(solution: Dict[BeautifulDate, List[Task]]) -> float:
    """
    Funkcja obliczająca wartość funkcji celu (czas między zadaniami).
    :param solution: rozwiązanie
    :return: wartość funkcji celu
    """

    objective = 0

    for start_date, route in solution.items():
        for i in range(1, len(route)):
            if i == 1:
                time_diff = route[i].start_date_time - start_date
                time_diff = time_diff.total_seconds() / 60
            else:
                time_diff = route[i].start_date_time - route[i-1].end_date_time
                time_diff = time_diff.total_seconds() / 60

            objective += time_diff

    return objective


def route_split_valid(solution: Dict[BeautifulDate, List[Task]], travel_modes: List[str], transit_modes: List[str] = []):

    for start_date, route in solution.items():
        # znajdź moment, w którym czekanie > 90 (najgorszy albo po kolei)
        # sprawdź czy powrót do bazy by się bardziej opłacał
        # jeśli tak, to zrób powrót (przerwa)
        # pozostałe powinny być wykonalne tego samego dnia, skoro czekanie było aż tak duże - trzeba jest ułożyć odpowiednio w tym dniu
        # jeśli by się nie dało, to dla najmniej pilnych można próbować znaleźć lepsze wstawienie albo uznać, że ta zmiana jest niewykonalna
        # ale jeśli jest wykonanlna, to należy sprawdzić czy faktycznie nastąpiła z nią poprawa rozwiązania najlepszego
        # jeśli tak, to należy zapisać to rozwiązanie jak najlepsze, jeśli nie - odrzucić i szukać dalej
        pass



depot = create_depot("Juliana Tokarskiego 8, Kraków", (D @ 26/11/2024)[14:00], (D @ 3/12/2024)[22:00])
task1 = Task("Pracownia", 270, "AGH D2, Czarna Wieś, 30-001 Kraków, Polska", (D @ 2/12/2024)[14:00], (D @ 2/12/2024)[18:30])
task2 = Task("Gry", 210, "BarON - Pub z planszówkami i konsolami w Krakowie Stefana Batorego 1, 31-135 Kraków, Polska", (D @ 26/11/2024)[18:00], (D @ 27/11/2024)[23:30])
task3 = Task("Obiad", 60, "IKEA Kraków Josepha Conrada 66, 31-357 Kraków, Polska", (D @ 26/11/2024)[14:00], (D @ 27/11/2024)[16:00])
task4 = Task("Zakupy", 30, "Biedronka Piastowska 49, 30-211 Kraków, Polska", (D @ 26/11/2024)[14:00], (D @ 2/12/2024)[12:00])
task5 = Task("Zajęcia", 195, "Wydział Humanistyczny AGH Czarnowiejska 36/Budynek C-7, 30-054 Kraków, Polska", (D @ 28/11/2024)[16:45], (D @ 28/11/2024)[20:00])
task6 = Task("Odebranie przesyłki", 30, "Galeria Krakowska Pawia 5, 31-154 Kraków, Polska", (D @ 27/11/2024)[11:00], (D @ 29/11/2024)[9:45])
tasks = [depot, task1, task2, task3, task4, task5, task6]
modes = ["walking", "transit"]
transit_modes = ["bus"]

solution, finished = initial_solution((D @ 26/11/2024)[14:00], (D @ 3/12/2024)[22:00], tasks, modes, transit_modes)
obj = get_distance_objective(solution)
print(obj)

# DODAĆ
# warunki sprawdzające możliwość jazdy autem/rowerem
# warunek ustalający kryteria funkcji celu (koszt)
# liczenie funkcji celu - inne kryteria
# warunek funckji celu - wiele kursów 1 dnia
# route split - minimalizacja czekania, moze jednak akcja z sprawdzeniem zakonczenia kursu
# edycja rozwiązania, jeśli nie wszystkie zadania zostały wykonane