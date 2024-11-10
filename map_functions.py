# FUNKCJE DOTYCZĄCE LOKALIZACJI

import googlemaps
from re import findall
from datetime import datetime, timedelta

my_key = 'AIzaSyCwEhmwpCvZfGfhwgn_GY2dpIkPV5P68ME'

gmaps = googlemaps.Client(key=my_key)  # nowy klient


def get_location_working_hours(name):

    """
    Funkcja do uzyskania informacji na temat godzin pracy wybranej lokalizacji.
    :param name: nazwa miejsca - oczekiwany precyzyjny adres/unikatowa nazwa w celu jednoznacznej identyfikacji miejsca
    :return: 7-elementowe listy z godzinami otwarcia oraz zamknięcia lokalizacji (elementy odpowiadają kolejnym dniom tygodnia)
    """

    # uzyskanie informacji id pierwszej znalezionej lokalizacji pasującej do nazwy
    place_id = gmaps.places(name)['results'][0]['place_id']

    # wybór informacji na temat godzin otwarcia
    weekday_text = gmaps.place(place_id)['result']['current_opening_hours']['weekday_text']

    # wybór odpowiednich danych z str
    opening_hours = []
    closing_hours = []

    pattern = r'\d+:\d+\s(?:A|P)M'  # wzorzec, do którego ma być dopasowany tekst

    for data in weekday_text:       # dla każdego dnia tygodnia
        data = data.replace('\u2009', "")
        matches = findall(pattern, data)        # znajdź godziny pracy w napisie

        if matches:     # jeśli są

            opening_hour, opening_a_p = matches[0].split('\u202f')      # kowersja godzin do wybranego formatu
            if opening_a_p == 'PM':
                new_time = datetime.strptime(opening_hour, '%H:%M')
                new_time = new_time + timedelta(hours=12)
                opening_hour = new_time.strftime('%H:%M')

            opening_hours.append(opening_hour)      # dodanie godziny do listy godzin otwarcia

            # analogicznie dla godzin zamknięcia
            closing_hour, closing_a_p = matches[1].split('\u202f')
            if closing_a_p == 'PM':
                new_time = datetime.strptime(closing_hour, '%H:%M')
                new_time = new_time + timedelta(hours=12)
                closing_hour = new_time.strftime('%H:%M')

            closing_hours.append(closing_hour)

        else:       # jeśli brak dopasowań przyjęte założenie, że miejsce jest zamknięte
            opening_hours.append('-')
            closing_hours.append('-')

    return opening_hours, closing_hours
