from beautiful_date import *
from typing import List, Dict
from random import choices
from model_params import Task
from init_heuristic import initial_solution
from neighbourhood import depot_time_fix_tmp, idle_times, intra_route_reinsertion, inter_route_shift,\
    shift_from_the_most_busy_day, shift_from_the_least_busy_day


def get_objective(solution: Dict[BeautifulDate, List[Task]], weights=None):
    """
    Liczenie wartości funkcji celu dla rozwiązania.
    :param solution:
    :param weights:
    :return:
    """
    if weights is None:
        weights = [0.6, 0, 0.4]
    objective = 0
    return objective


def simmulated_annealing(T_begin: BeautifulDate, T_end: BeautifulDate, tasks: List[Task], temp_0: float,
                         temp_end: float, alpha: float, series_num: int, neighbourhood_probabilities: List[int],
                         weights: List[int], travel_modes: List[str], transit_modes: List[str] = [],
                         solution_0: Dict[BeautifulDate, List[Task]] = None):
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
    if solution_0 is None:  # rozwiazanie poczatkowe
        current_solution = initial_solution(T_begin, T_end, tasks, travel_modes, transit_modes)
    else:
        current_solution = solution_0
    best_solution = current_solution
    operators = [1, 2, 3, 4]

    while temp_0 <= temp_end:

        for i in range(series_num):     # w każdej serii
            operator_choice = choices(operators, weights)[0]    # wybór operatora
            #
