from beautiful_date import *
from typing import List, Dict
from random import choices, choice, uniform
from copy import deepcopy
from math import exp
from model_params import Task, Route, set_idle_time
from init_heuristic import initial_solution, dict_2_route
from neighbourhood import intra_route_reinsertion, inter_route_shift,\
    shift_from_the_most_busy_day, shift_from_the_least_busy_day, verify_shift

inf = float('inf')


def get_objective(solution: List[Route], weights=None):
    """
    Liczenie wartości funkcji celu dla rozwiązania.
    :param solution:
    :param weights:
    :return:
    """
    if weights is None:
        weights = [0.6, 0, 0.4]

    objective = 0
    for route in solution:
        route.set_objective(weights)
        objective += route.objective
    return objective


def simmulated_annealing(T_begin: BeautifulDate, T_end: BeautifulDate, tasks: List[Task], temp_0: float,
                         temp_end: float, alpha: float, series_num: int, neighbourhood_probabilities: List[int],
                         weights: List[int], travel_modes: List[str], transit_modes: List[str] = [],
                         solution_0: Route = None):
    """
    Główny algorytm symulowanego wyżarzania.
    :param T_begin: początek horyzontu
    :param T_end: koniec horyzontu
    :param tasks: lista zadań
    :param temp_0: temperatura początkowa
    :param temp_end: temperatura końcowa
    :param alpha: współczynnik chłodzenia
    :param series_num: liczba serii
    :param weights: wagi w funkcji celu
    :param neighbourhood_probabilities: prawdopodobieństwa operatorów
    :param travel_modes: metody transportu
    :param transit_modes: szczegóły komunikacji miejskiej
    :param solution_0: rozwiązanie początkowe (lub None)
    :return:
    """
    finished = []
    if solution_0 is None:  # rozwiazanie poczatkowe
        current_solution, finished = initial_solution(T_begin, T_end, tasks, travel_modes, transit_modes)
        if len(finished) == len(tasks):
            current_solution = dict_2_route(current_solution)
        else:
            return None, None
    else:
        current_solution = deepcopy(solution_0)

    best_solution = deepcopy(current_solution)
    weights_actual = []
    for w in weights:
        weights_actual.append(w/100)
    best_objectve = get_objective(current_solution, weights_actual)
    operators = [1, 2, 3, 4]
    temp = temp_0
    all_objectives = [best_objectve]

    while temp >= temp_end:

        for i in range(series_num):     # w każdej serii
            operator_choice = choices(operators, neighbourhood_probabilities)[0]    # wybór operatora

            if operator_choice == 1:
                # wybór kursu, w którym możliwe jest potencjalne wstawienie
                valid = False
                for route in current_solution:
                    if len(route.tasks) > 3:
                        valid = True
                        break
                random_route = None
                if valid:
                    random_route = choice(current_solution)
                    while len(random_route.tasks) <= 3:
                        random_route = choice(current_solution)
                # wybór nowej drogi
                if valid and random_route is not None:
                    new_route = intra_route_reinsertion(random_route, travel_modes, transit_modes)
                    if new_route is None:
                        current_objective = get_objective(current_solution, weights_actual)
                        all_objectives.append(current_objective)
                        temp *= alpha
                        continue
                    new_route.depot_fix()
                    new_solution = deepcopy(current_solution)
                    random_route_inx = current_solution.index(random_route)
                    del new_solution[random_route_inx]
                    new_solution.append(new_route)
                    new_solution.sort(key=lambda x: x.start_date_og)
                    # weryfikacja
                    feasible = True
                    for j in range(1, len(new_solution)):
                        if not verify_shift(new_solution[j], new_solution[j - 1]):
                            feasible = False
                            break
                    if not feasible:
                        temp *= alpha
                        current_objective = get_objective(current_solution, weights_actual)
                        all_objectives.append(current_objective)
                        continue

            elif operator_choice == 2:
                # wybór 2 kursów
                if len(current_solution) == 1:      # jak jest 1 kurs to sie nie da tego wykonac
                    temp *= alpha
                    current_objective = get_objective(current_solution, weights_actual)
                    all_objectives.append(current_objective)
                    continue
                random_route1 = choice(current_solution)
                random_route2 = choice(current_solution)
                while random_route2 == random_route1:
                    random_route2 = choice(current_solution)
                new_route1, new_route2 = inter_route_shift(random_route1, random_route2, travel_modes, transit_modes)
                if new_route1 is None and new_route2 is None:
                    temp *= alpha
                    current_objective = get_objective(current_solution, weights_actual)
                    all_objectives.append(current_objective)
                    continue
                elif new_route1 is None and new_route2 is not None:
                    new_route2.depot_fix()
                    new_solution = deepcopy(current_solution)
                    random_route_inx1 = current_solution.index(random_route1)
                    del new_solution[random_route_inx1]
                    random_route_inx2 = current_solution.index(random_route2)
                    if random_route_inx2 < random_route_inx1:
                        del new_solution[random_route_inx2]
                    else:
                        del new_solution[random_route_inx2 - 1]
                    # jeśli jedyne zadanie z kursu 1. zostało przeniesione, to usunięcie całego kursu 1
                    new_solution.append(new_route2)
                    new_solution.sort(key=lambda x: x.start_date_og)
                    feasible = True
                    for j in range(1, len(new_solution)):
                        if not verify_shift(new_solution[j], new_solution[j - 1]):
                            feasible = False
                            break
                    if not feasible:
                        temp *= alpha
                        current_objective = get_objective(current_solution, weights_actual)
                        all_objectives.append(current_objective)
                        continue
                elif new_route1 is not None and new_route2 is not None:
                    new_route1.depot_fix()
                    new_route2.depot_fix()
                    new_solution = deepcopy(current_solution)
                    random_route_inx1 = current_solution.index(random_route1)
                    del new_solution[random_route_inx1]
                    random_route_inx2 = current_solution.index(random_route2)
                    if random_route_inx2 < random_route_inx1:
                        del new_solution[random_route_inx2]
                    else:
                        del new_solution[random_route_inx2-1]
                    new_solution.append(new_route1)
                    new_solution.append(new_route2)
                    new_solution.sort(key=lambda x: x.start_date_og)
                    feasible = True
                    for j in range(1, len(new_solution)):
                        if not verify_shift(new_solution[j], new_solution[j - 1]):
                            feasible = False
                            break
                    if not feasible:
                        temp *= alpha
                        current_objective = get_objective(current_solution, weights_actual)
                        all_objectives.append(current_objective)
                        continue

            elif operator_choice == 3:
                new_solution = shift_from_the_most_busy_day(current_solution, T_begin, T_end, travel_modes,
                                                            transit_modes)
                if new_solution == current_solution:
                    temp *= alpha
                    current_objective = get_objective(current_solution, weights_actual)
                    all_objectives.append(current_objective)
                    continue
                # weryfikacja, jeśli w którymś miejscu się okaże, że jest źle, to znaczy, że nie ma co
                feasible = True
                for j in range(1, len(new_solution)):
                    if not verify_shift(new_solution[j], new_solution[j-1]):
                        feasible = False
                        break
                if not feasible:
                    temp *= alpha
                    current_objective = get_objective(current_solution, weights_actual)
                    all_objectives.append(current_objective)
                    continue

            elif operator_choice == 4:
                new_solution = shift_from_the_least_busy_day(current_solution, T_begin, T_end, travel_modes,
                                                             transit_modes)
                if new_solution == current_solution:
                    temp *= alpha
                    current_objective = get_objective(current_solution, weights_actual)
                    all_objectives.append(current_objective)
                    continue
                feasible = True
                for j in range(1, len(new_solution)):
                    if not verify_shift(new_solution[j], new_solution[j - 1]):
                        feasible = False
                        break
                if not feasible:
                    temp *= alpha
                    current_objective = get_objective(current_solution, weights_actual)
                    all_objectives.append(current_objective)
                    continue

            if get_objective(current_solution, weights_actual) >= get_objective(new_solution, weights_actual):
                current_solution = new_solution
                current_objective = get_objective(current_solution, weights_actual)
                all_objectives.append(current_objective)
                # aktualizacja idle_times
                for j in range(len(current_solution)):
                    if j == 0:
                        set_idle_time(new_solution[j], None)
                    else:
                        set_idle_time(new_solution[j], new_solution[j-1])

                if get_objective(new_solution, weights_actual) <= get_objective(best_solution, weights_actual):
                    best_solution = deepcopy(new_solution)

            else:
                P = exp(-(get_objective(new_solution, weights_actual) - get_objective(current_solution, weights_actual)) / temp)
                prob_random = uniform(0, 1)
                if prob_random < P:
                    current_solution = new_solution
                    for j in range(len(current_solution)):
                        if j == 0:
                            set_idle_time(new_solution[j], None)
                        else:
                            set_idle_time(new_solution[j], new_solution[j - 1])
                    current_objective = get_objective(current_solution, weights_actual)
                    all_objectives.append(current_objective)
                else:
                    current_objective = get_objective(current_solution, weights_actual)
                    all_objectives.append(current_objective)
                    temp *= alpha
                    continue
        temp *= alpha

    return best_solution, all_objectives


# i co robić z niedopuszczalnymi -- niedopuszczone
