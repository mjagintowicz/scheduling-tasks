# FUNKCJE DOTYCZĄCE LOKALIZACJI

import googlemaps
from re import findall
from datetime import datetime, timedelta
from typing import List, Tuple
from copy import deepcopy
from re import search
from beautiful_date import *

inf = float('inf')

with open('api_test_key_aa.txt', 'r') as file:  # odczytanie klucza z pliku txt
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
                pattern_24h = r'Open 24 hours'
                matches_24h = findall(pattern_24h, data)
                if matches_24h:
                    opening_hours.append("00:00")
                    closing_hours.append("23:59")
                else:
                    opening_hours.append('-')
                    closing_hours.append('-')

    else:
        opening_hours = 7 * ["00:00"]
        closing_hours = 7 * ["23:59"]

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


def iterate_through_matrix(rows: List, r, c):
    """
    Funkcja pomocnicza do iterowania po rzędach macierzy odległości zwróconej przez klienta Pythona.
    :param c: liczba kolumn
    :param r: liczba wierszy
    :param rows: rzędzy macierzy odległości
    :return: macierz odległości z wartościami czasów (w minutach)
    """

    matrix = [[inf] * c for _ in range(r)]  # inicjalizacja wyjściowej macierzy

    row_cnt = 0
    for element in rows:
        col_cnt = 0
        for item in element['elements']:

            if 'duration' not in item:
                distance_time = inf
            else:
                distance_time_str = item['duration']['text']
                distance_time = time_pattern_match(distance_time_str)  # konwersja str do liczby minut

            matrix[row_cnt][col_cnt] = distance_time  # aktualizacja macierzy

            col_cnt += 1

        row_cnt += 1

    return matrix


def get_fare(rows: List, r, c):
    """
    Uzyskanie informacji na temat kosztów biletów.
    :param c:
    :param r:
    :param rows: rzędy macierzy odległości
    :return: macierz kosztów
    """

    matrix = [[inf] * c for _ in range(r)]

    row_cnt = 0
    for element in rows:
        col_cnt = 0
        for item in element['elements']:

            if 'fare' in item:  # jeśli jest informacja o koszcie
                fare = item['fare']['value']
            else:
                fare = inf

            matrix[row_cnt][col_cnt] = fare  # aktualizacja macierzy

            col_cnt += 1

        row_cnt += 1

    return matrix


def get_distance_cost_matrixes(origins_og: List[str], destinations_og: List[str], modes: List[str],
                               transit_modes: List[str] = None, departure_time: BeautifulDate = D.now(),
                               car_enabled: bool = True, bike_enabled: bool = True, others_enabled: bool = True):
    """
    Uzyskanie macierzy odległości i macierzy kosztów wersja zaktualizowana. Tworzone tylko konkretny rząd macierzy.
    :param origins_og: origins - lokalizacja Z
    :param destinations_og: pozostałe lokalizacje DO
    :param modes: metody transportu (“driving”, “walking”, “transit” or “bicycling”)
    :param transit_modes: dodatkowe informacje, jeśli wcześniej wybrano "transit" (“bus”, “subway”, “train”, “tram”, “rail”)
    :param departure_time: chwila, w której można kontynuować kurs (domyślnie - teraz)
    :param car_enabled: zmienna określająca, czy rzeczywiście można użyć samochodu
    :param bike_enabled: zmienna określająca, czy rzeczywiście można użyć roweru
    :param others_enabled: zmienna określająca, czy rzeczywiście można użyć innych metod
    :return: lista z macierzami dystansów dla wybranych sposobów podróży (czas w minutach)
    """

    origins = deepcopy(origins_og)
    destinations = deepcopy(destinations_og)
    distance_matrixes = []
    cost_matrixes = []
    split = False
    if len(destinations) > 200:
        return None, None
    if len(destinations) > 100: # założenie, że zadań jest zawsze <= 200 (api może wygenerować 100 elementów/zapytanie)
        split = True
        destinations1 = deepcopy(destinations[0:100])
        destinations2 = deepcopy(destinations[10:])

    for mode in modes:  # dla każdej wybranej metody

        # pobranie danych
        if mode == 'transit' and others_enabled:    # żeby skorzystać z transit musi być opcja others_enabled
            for transit_mode in transit_modes:
                if not split:
                    rows = gmaps.distance_matrix(origins=origins, destinations=destinations, mode=mode,
                                                 transit_mode=transit_mode, departure_time=departure_time)['rows']

                    distance_matrix_tmp = iterate_through_matrix(rows, len(origins), len(destinations))
                    cost_matrix_tmp = get_fare(rows, len(origins), len(destinations))

                else:   # jeśli trzeba rozdzielać to rozdzielam
                    rows_11 = gmaps.distance_matrix(origins=origins, destinations=destinations1, mode=mode,
                                                    transit_mode=transit_mode, departure_time=departure_time)['rows']
                    distance_matrix_tmp11 = iterate_through_matrix(rows_11, len(origins), len(destinations1))
                    cost_matrix_tmp11 = get_fare(rows_11, len(origins), len(destinations1))
                    rows_22 = gmaps.distance_matrix(origins=origins, destinations=destinations2, mode=mode,
                                                    transit_mode=transit_mode, departure_time=departure_time)['rows']
                    distance_matrix_tmp22 = iterate_through_matrix(rows_22, len(origins), len(destinations2))
                    cost_matrix_tmp22 = get_fare(rows_22)

                    distance_matrix_tmp = []
                    for r in range(len(distance_matrix_tmp11)):
                        list_tmp = distance_matrix_tmp11[r] + distance_matrix_tmp22[r]
                        distance_matrix_tmp.append(deepcopy(list_tmp))

                    cost_matrix_tmp = []
                    for r in range(len(cost_matrix_tmp11)):
                        list_tmp = cost_matrix_tmp11[r] + cost_matrix_tmp22[r]
                        cost_matrix_tmp.append(deepcopy(list_tmp))
                # ostateczne przypisanie macierzy
                distance_matrixes.append(deepcopy(distance_matrix_tmp))
                cost_matrixes.append(deepcopy(cost_matrix_tmp))

        elif (mode == 'driving' and car_enabled) or (mode == 'bicycling' and bike_enabled) or (mode == 'walking' and
                                                                                               others_enabled):
            if not split:
                rows = gmaps.distance_matrix(origins=origins, destinations=destinations, mode=mode,
                                             departure_time=departure_time)['rows']

                distance_matrix_tmp = iterate_through_matrix(rows, len(origins), len(destinations))

            else:  # jeśli trzeba rozdzielać to rozdzielam
                rows_11 = gmaps.distance_matrix(origins=origins, destinations=destinations1, mode=mode,
                                                departure_time=departure_time)['rows']
                distance_matrix_tmp11 = iterate_through_matrix(rows_11, len(origins), len(destinations1))
                rows_22 = gmaps.distance_matrix(origins=origins, destinations=destinations2, mode=mode,
                                                departure_time=departure_time)['rows']
                distance_matrix_tmp22 = iterate_through_matrix(rows_22, len(origins), len(destinations2))

                distance_matrix_tmp = []
                for r in range(len(distance_matrix_tmp11)):
                    list_tmp = distance_matrix_tmp11[r] + distance_matrix_tmp22[r]
                    distance_matrix_tmp.append(deepcopy(list_tmp))

            # ostateczne zapisanie macierzy
            distance_matrixes.append(deepcopy(distance_matrix_tmp))
            cost_matrix_tmp = [[inf] * len(destinations) for _ in range(len(origins))]
            cost_matrixes.append(deepcopy(cost_matrix_tmp))

        else:   # jeśli któraś z metod jest zablokowana - INF (czyli nic nie jest możliwe nawet powrót)
            distance_matrix_tmp = [[inf] * len(destinations) for _ in range(len(origins))]
            distance_matrixes.append(deepcopy(distance_matrix_tmp))
            cost_matrix_tmp = [[inf] * len(destinations) for _ in range(len(origins))]
            cost_matrixes.append(deepcopy(cost_matrix_tmp))

    return distance_matrixes, cost_matrixes


def validate_location(location: str):
    """
    Weryfikacja lokalizacji na podstawie tego, czy jej współrzędne są znajdowane na mapie
    :param location: nazwa lokalizacji
    :return: tak/nie
    """

    validation = gmaps.addressvalidation(location)
    if 'result' not in validation:
        return False
    validation = validation['result']
    if 'geocode' in validation:
        return True
    return False