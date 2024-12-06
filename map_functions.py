# FUNKCJE DOTYCZĄCE LOKALIZACJI

import googlemaps
from re import findall
from datetime import datetime, timedelta
from typing import List, Tuple
from copy import deepcopy
from re import search
from beautiful_date import *

inf = float('inf')

with open('key.txt', 'r') as file:  # odczytanie klucza z pliku txt
    my_key = file.read().rstrip()

gmaps = googlemaps.Client(key=my_key)  # nowy klient


def get_location_working_hours(name) -> Tuple[List[str], List[str]]:
    """
    Funkcja do uzyskania informacji na temat godzin pracy wybranej lokalizacji.
    :param name: nazwa miejsca - oczekiwany precyzyjny adres/unikatowa nazwa w celu jednoznacznej identyfikacji miejsca
    :return: 7-elementowe listy z godzinami otwarcia oraz zamknięcia lokalizacji (elementy odpowiadają kolejnym dniom tygodnia)
    """

    # uzyskanie informacji id pierwszej znalezionej lokalizacji pasującej do nazwy
    place_id = gmaps.places(name)['results'][0]['place_id']

    # wybór informacji na temat godzin otwarcia

    result = gmaps.place(place_id)['result']
    if 'current_opening_hours' in result:
        weekday_text = gmaps.place(place_id)['result']['current_opening_hours']['weekday_text']

        # wybór odpowiednich danych z str
        opening_hours = []
        closing_hours = []

        pattern = r'\d+:\d+\s(?:A|P)M'  # wzorzec, do którego ma być dopasowany tekst
        hour_pattern = r'\d+:\d+'
        am_pm_pattern = r'(?:A|P)M'
        pattern_12 = r'12:\d+'

        for data in weekday_text:  # dla każdego dnia tygodnia
            data = data.replace('\u2009', "")
            matches = findall(pattern, data)  # znajdź godziny pracy w napisie

            # przypadek jeśli matchuje tylko 1. godzinę (bo z jakiegoś powodu tak może być)
            if len(matches) == 1:
                hour_matches = findall(hour_pattern, data)
                am_pm_match = findall(am_pm_pattern, data)
                matches = []
                for hour_match in hour_matches:
                    matches.append(hour_match + '\u202f' + am_pm_match[0])

            if matches:  # jeśli są

                opening_hour, opening_a_p = matches[0].split('\u202f')  # kowersja godzin do wybranego formatu
                matches_12 = findall(pattern_12, opening_hour)  # czy jest między 12:00 a 12:59
                if opening_a_p == 'PM' and not matches_12:
                    new_time = datetime.strptime(opening_hour, '%H:%M')
                    new_time = new_time + timedelta(hours=12)
                    opening_hour = new_time.strftime('%H:%M')

                opening_hours.append(opening_hour)  # dodanie godziny do listy godzin otwarcia

                # analogicznie dla godzin zamknięcia (przypadek, że zamyka się następnego dnia)
                closing_hour, closing_a_p = matches[1].split('\u202f')
                matches_12 = findall(pattern_12, closing_hour)
                if closing_a_p == 'PM' and not matches_12:
                    new_time = datetime.strptime(closing_hour, '%H:%M')
                    new_time = new_time + timedelta(hours=12)
                    closing_hour = new_time.strftime('%H:%M')

                closing_hours.append(closing_hour)

            else:  # jeśli brak dopasowań przyjęte założenie, że miejsce jest zamknięte
                opening_hours.append('-')
                closing_hours.append('-')

    else:
        opening_hours = 7 * ["00:00"]
        closing_hours = 7 * ["00:00"]

    return opening_hours, closing_hours


def time_pattern_match(distance_time_str: str):
    """
    Konwersja tekstu z wartością czasu na odpowiadającą mu liczbę minut (int).
    :param distance_time_str: tekst z czasem po angielsku (np. 1 day 2 horus)
    :return: czas w minutach
    """

    patterns = [r'(\d+)\s*day', r'(\d+)\s*hour', r'(\d+)\s*min']  # wzorce do odczytania czasu z tekstu

    distance_time = 0

    i = 0
    for pattern in patterns:
        match = search(pattern, distance_time_str)  # wyznaczenie czasu w minutach
        if match is not None:
            if i == 0:
                distance_time += int(match.group(1)) * 24 * 60
            elif i == 1:
                distance_time += int(match.group(1)) * 60
            else:
                distance_time += int(match.group(1))
        i += 1

    return distance_time


def iterate_through_matrix(rows: List, small: bool = False):
    """
    Funkcja pomocnicza do iterowania po rzędach macierzy odległości zwróconej przez klienta Pythona.
    :param rows: rzędzy macierzy odległości
    :param small: zmienna określająca, czy chodzi o specjalną macierz powrotów nx1
    :return: macierz odległości z wartościami czasów (w minutach)
    """

    size = len(rows)  # wymiary macierzy (size x size)
    if not small:
        matrix = [[inf] * size for _ in range(size)]  # inicjalizacja wyjściowej macierzy

        row_cnt = 0
        for element in rows:
            col_cnt = 0
            for item in element['elements']:

                if row_cnt == col_cnt:  # jeśli jest to element na przekątnej (dystans z A do A)
                    distance_time = inf  # uzupełnienie inf
                else:
                    distance_time_str = item['duration']['text']
                    distance_time = time_pattern_match(distance_time_str)  # konwersja str do liczby minut

                matrix[row_cnt][col_cnt] = distance_time  # aktualizacja macierzy

                col_cnt += 1

            row_cnt += 1

    if small:
        matrix = [[inf * 1 for _ in range(size)]]
        col_cnt = 0
        for element in rows:
            for item in element['elements']:
                distance_time_str = item['duration']['text']
                distance_time = time_pattern_match(distance_time_str)  # konwersja str do liczby minut

                matrix[0][col_cnt] = distance_time  # aktualizacja macierzy

                col_cnt += 1

    return matrix


def get_fare(rows: List, small: bool = False):
    """
    Uzyskanie informacji na temat kosztów biletów.
    :param rows: rzędy macierzy odległości
    :param small: zmienna określająca, czy chodzi o specjalną macierz powrotów nx1
    :return: macierz kosztów
    """

    size = len(rows)  # wymiary macierzy (size x size)
    if not small:
        matrix = [[0] * size for _ in range(size)]  # inicjalizacja wyjściowej macierzy

        row_cnt = 0
        for element in rows:
            col_cnt = 0
            for item in element['elements']:

                if row_cnt == col_cnt:  # jeśli jest to element na przekątnej (dystans z A do A)
                    fare = inf  # uzupełnienie inf
                else:
                    if 'fare' in item:  # jeśli jest informacja o koszcie
                        fare = item['fare']['value']
                    else:
                        fare = inf

                matrix[row_cnt][col_cnt] = fare  # aktualizacja macierzy

                col_cnt += 1

            row_cnt += 1

    if small:
        matrix = [[inf * 1 for _ in range(size)]]
        col_cnt = 0
        for element in rows:
            for item in element['elements']:
                if 'fare' in item:  # jeśli jest informacja o koszcie
                    fare = item['fare']['value']
                else:
                    fare = inf

                matrix[0][col_cnt] = fare  # aktualizacja macierzy

                col_cnt += 1

    return matrix


def get_distance_cost_matrixes(locations_og: List[str], modes: List[str], transit_modes: List[str] = None,
                               departure_time: BeautifulDate = D.now(), finished: List[int] = [],
                               car_enabled: bool = True, bike_enabled: bool = True, others_enabled: bool = True):
    """
    Uzyskanie macierzy odległości i macierzy kosztów.
    :param locations_og: lista lokalizacji (wierzchołki grafu)
    :param modes: metody transportu (“driving”, “walking”, “transit” or “bicycling”)
    :param transit_modes: dodatkowe informacje, jeśli wcześniej wybrano "transit" (“bus”, “subway”, “train”, “tram”, “rail”)
    :param departure_time: chwila, w której można kontynuować kurs (domyślnie - teraz)
    :param finished: lista zadań wykonanych (zastąpienie ich infami) w celu zmniejszenia ilości elementów w zapytaniu
    :param car_enabled: zmienna określająca, czy rzeczywiście można użyć samochodu
    :param bike_enabled: zmienna określająca, czy rzeczywiście można użyć roweru
    :param others_enabled: zmienna określająca, czy rzeczywiście można użyć innych metod
    :return: lista z macierzami dystansów dla wybranych sposobów podróży (czas w minutach)
    """

    locations = deepcopy(locations_og)
    size = len(locations)
    distance_matrixes = []
    cost_matrixes = []
    removed_locations = []

    # usunięcie zbędnych (odwiedzonych lokalizacji) bez bazy
    for inx in range(len(locations)):
        if inx in finished and inx != 0:
            removed_locations.append(locations[inx])
            locations[inx] = 'inf'
    while 'inf' in locations:
        locations.remove('inf')

    for mode in modes:  # dla każdej wybranej metody

        # pobranie danych
        if mode == 'transit' and others_enabled:    # żeby skorzystać z transit musi być opcja others_enabled
            for transit_mode in transit_modes:
                rows = gmaps.distance_matrix(origins=locations, destinations=locations, mode=mode,
                                             transit_mode=transit_mode, departure_time=departure_time)['rows']

                distance_matrix_tmp = iterate_through_matrix(rows)  # utworzenie macierzy dla wybranej metody

                # jeśli są jakieś odwiedzone lokalizacje to utworzenie dodatkowej macierzy nx1 z wartościami powrotów
                if removed_locations:
                    small_row_og = gmaps.distance_matrix(origins=removed_locations, destinations=[locations[0]],
                                                         mode=mode, transit_mode=transit_mode,
                                                         departure_time=departure_time)['rows']
                    small_row = iterate_through_matrix(small_row_og, True)[0]
                    small_cost = get_fare(small_row_og, True)[0]

                # wstawienie infów w odpowiednie indeksy
                for row in range(len(distance_matrix_tmp[0])):
                    for inx in finished:
                        if inx != 0:
                            distance_matrix_tmp[row].insert(inx, inf)

                for inx in finished:
                    if inx != 0:
                        distance_matrix_tmp.insert(inx, [inf] * len(distance_matrix_tmp[0]))
                        if removed_locations:       # jeśli coś było usunięte, to zapisanie godziny powrotu
                            distance_matrix_tmp[inx][0] = small_row.pop(0)

                distance_matrixes.append(deepcopy(distance_matrix_tmp))

                cost_matrix_tmp = get_fare(rows)
                for row in range(len(cost_matrix_tmp[0])):
                    for inx in finished:
                        if inx != 0:
                            cost_matrix_tmp[row].insert(inx, inf)
                for inx in finished:
                    if inx != 0:
                        cost_matrix_tmp.insert(inx, [inf] * len(cost_matrix_tmp[0]))
                        if removed_locations:  # jeśli coś było usunięte, to zapisanie godziny powrotu
                            cost_matrix_tmp[inx][0] = small_cost.pop(0)
                cost_matrixes.append(deepcopy(cost_matrix_tmp))

        elif (mode == 'driving' and car_enabled) or (mode == 'bicycling' and bike_enabled) or (mode == 'walking' and
                                                                                               others_enabled):
            rows = gmaps.distance_matrix(origins=locations, destinations=locations, mode=mode,
                                         departure_time=departure_time)['rows']

            distance_matrix_tmp = iterate_through_matrix(rows)

            if removed_locations:
                small_row_og = gmaps.distance_matrix(origins=removed_locations, destinations=[locations[0]], mode=mode,
                                                     departure_time=departure_time)['rows']
                small_row = iterate_through_matrix(small_row_og, True)[0]
                small_cost = get_fare(small_row_og, True)[0]

            # wstawienie infów w odpowiednie indeksy
            for row in range(len(distance_matrix_tmp[0])):
                for inx in finished:
                    if inx != 0:
                        distance_matrix_tmp[row].insert(inx, inf)

            for inx in finished:
                if inx != 0:
                    distance_matrix_tmp.insert(inx, [inf] * len(distance_matrix_tmp[0]))
                    if removed_locations:  # jeśli coś było usunięte, to zapisanie godziny powrotu
                        distance_matrix_tmp[inx][0] = small_row.pop(0)

            distance_matrixes.append(deepcopy(distance_matrix_tmp))

            # analogiczny edit macierzy kosztów
            cost_matrix_tmp = get_fare(rows)

            for row in range(len(cost_matrix_tmp[0])):
                for inx in finished:
                    if inx != 0:
                        cost_matrix_tmp[row].insert(inx, inf)
            for inx in finished:
                if inx != 0:
                    cost_matrix_tmp.insert(inx, [inf] * len(cost_matrix_tmp[0]))
                    if removed_locations:  # jeśli coś było usunięte, to zapisanie godziny powrotu
                        cost_matrix_tmp[inx][0] = small_cost.pop(0)

            cost_matrixes.append(deepcopy(cost_matrix_tmp))

        else:   # jeśli któraś z metod jest zablokowana - INF (czyli nic nie jest możliwe nawet powrót)
            distance_matrix_tmp = [[inf] * size for _ in range(size)]
            distance_matrixes.append(deepcopy(distance_matrix_tmp))
            cost_matrix_tmp = [[inf] * size for _ in range(size)]
            cost_matrixes.append(deepcopy(cost_matrix_tmp))

    return distance_matrixes, cost_matrixes


def get_transit_route_details(origin: str, destination: str, transit_mode: str,
                              departure_time: BeautifulDate = D.now()) -> List[Tuple]:
    """
    Uzyskanie dodatkowych informacji na temat trasy komunikacji miejskiej.
    :param origin: początek trasy
    :param destination: koniec trasy
    :param transit_mode: rodzaj komunikacji miejskiej (“bus”, “subway”, “train”, “tram”, “rail”)
    :param departure_time: czas rozpoczęcia trasy (domyślnie teraz)
    :return: lista krotek (czas, rodzaj przemieszczenia, opcj. przystanek początkowy, końcowy, linia)
    """

    route_details = []

    # kolejne elementy trasy
    steps = gmaps.directions(origin=origin, destination=destination, mode='transit', transit_mode=transit_mode,
                             departure_time=departure_time)[0]['legs'][0]['steps']

    for step in steps:

        duration_txt = step['duration']['text']
        duration = time_pattern_match(duration_txt)  # wyznaczenie czasu

        mode = step['travel_mode']

        if mode == 'TRANSIT':  # jeśli jest to fragment z przejazdem to zapisz dodatkowe info (skąd, dokąd, czym)
            departure_stop = step['transit_details']['departure_stop']['name']
            arrival_stop = step['transit_details']['arrival_stop']['name']

            if 'short_name' in step['transit_details']['line']:
                line = step['transit_details']['line']['short_name']
                step_info = (duration, mode, departure_stop, arrival_stop, line)
            elif 'name' in step['transit_details']['line']:
                line = step['transit_details']['line']['name']
                step_info = (duration, mode, departure_stop, arrival_stop, line)
            else:
                step_info = (duration, mode, departure_stop, arrival_stop)

        else:
            step_info = (duration, mode)

        route_details.append(step_info)

    return route_details


def validate_location(location: str):
    """
    Weryfikacja lokalizacji na podstawie tego, czy jej współrzędne są znajdowane na mapie
    :param location: nazwa lokalizacji
    :return: tak/nie
    """

    validation = gmaps.addressvalidation(location)['result']
    if 'geocode' in validation:
        return True
    return False
