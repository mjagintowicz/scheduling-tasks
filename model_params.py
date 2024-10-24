# KLASA OPISUJĄCA ZADANIE
class Task:

    def __init__(self, name, duration, location, window_left, window_right):

        self.name = name            # nazwa zadania
        self.duration = duration    # czas trwania
        self.location = location    # lokalizacja

        self.window_left = window_left  # okna czasowe
        self.window_right = window_right

        self.start_date_time = None

        # dodać parametry opisujące transport
        # ...

    def get_day_limits(self, date):

        # wyślij zapytanie do Maps API
        # w jakich godzinach self.location jest czynne w dniu date
        # zwróć godzinę otwarcia i godzinę zamknięcia
        return None

    def set_start(self):

        # ustalenie czasu rozpoczęcia
        pass