from PyQt6.QtWidgets import QMainWindow, QPushButton, QHBoxLayout, QWidget, QDateEdit, QVBoxLayout, QLabel, QTimeEdit, \
    QTabWidget, QDialog, QDialogButtonBox, QGridLayout, QCheckBox, QLineEdit
from PyQt6.QtCore import Qt, QDate, QTime, QTimer
from PyQt6.QtGui import QFont
from datetime import timedelta

from calendar_functions import *
from model_params import Task
from init_heuristic import initial_solution, create_depot
from map_functions import *


# OKNO STARTOWE

class StartWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # tytuł okna
        self.setWindowTitle('Optymalizacja harmonogramu')

        # rozmiar okna
        self.setFixedSize(1200, 850)

        # layout główny
        self.tab_layout = QVBoxLayout()

        # zmienne
        self.event_ids = []     # unikalne id każdego zadania/eventu
        self.tasks_obtained = False  # flaga czy zadania zostały już pobrane
        self.tasks = []  # lista pobranych zadań
        self.T_begin = None  # początek i koniec harmonogramu
        self.T_end = None
        self.modes = []     # informacje na temat wybranych środków transportu
        self.transit_modes = []
        self.solution = {}

        # zakładki
        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)
        self.setCentralWidget(self.tabs)
        self.show()

        # zakładka 1. - wczytywanie danych
        self.tab1 = TaskTab(self)
        self.tabs.addTab(self.tab1, "Zadania")

        # zakładka 2. - parametry
        self.tab2 = ParamTab(self)
        self.tabs.addTab(self.tab2, "Parametry")


# WCZYTYWANIE DANYCH

class TaskTab(QWidget):

    def __init__(self, parent: StartWindow):

        super(TaskTab, self).__init__()

        self.parent = parent

        # przycisk startowy
        self.start_button = QPushButton('Pobierz zadania\nz kalendarza', self)
        self.start_button.setFixedSize(200, 75)
        self.start_button.setFont(QFont('Calibri', 15))
        self.start_button.clicked.connect(self.get_data)  # po kliknięciu funkcja

        # przycisk otwierający okno podgląd
        self.tasks_button = QPushButton('Potwierdź listę zadań', self)
        self.tasks_button.setFixedSize(200, 75)
        self.tasks_button.setFont(QFont('Calibri', 15))
        self.tasks_button.clicked.connect(self.display_tasks)

        self.log_out_button = QPushButton('Wyloguj się', self)
        self.log_out_button.setFixedSize(200, 75)
        self.log_out_button.setFont(QFont('Calibri', 15))
        self.log_out_button.clicked.connect(self.clear_data)

        # layout do przycisków
        self.button_layout = QVBoxLayout()
        self.button_layout.setContentsMargins(200, 250, 100, 250)
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.tasks_button)
        self.button_layout.addWidget(self.log_out_button)

        # wybór dat
        self.begin_date = QDateEdit()
        self.begin_date.setCalendarPopup(True)
        self.begin_date.setDate(QDate.currentDate())  # domyślnie dziś
        self.begin_date.setFixedSize(100, 30)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(14))  # domyślnie koniec po 2 tygodniach
        self.end_date.setFixedSize(100, 30)

        # wybór godzin
        self.begin_time = QTimeEdit()
        self.begin_time.setTime(QTime.currentTime())
        self.begin_time.setFixedSize(80, 30)

        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime.currentTime())
        self.end_time.setFixedSize(80, 30)

        # etykiety
        self.begin_label = QLabel('Początek harmonogramu:')
        self.begin_label.setFixedSize(200, 20)

        self.end_label = QLabel('Koniec harmonogramu:')
        self.end_label.setFixedSize(200, 20)

        # layout na informacje o dacie i godzinie
        self.full_date_time_layout = QVBoxLayout()

        # w nim mniejsze layouty
        # 1. - etykieta
        self.begin_label_layout = QHBoxLayout()
        self.begin_label_layout.addWidget(self.begin_label)

        # 2. - data i godzina początku
        self.begin_date_time_layout = QHBoxLayout()
        self.begin_date_time_layout.addWidget(self.begin_date)
        self.begin_date_time_layout.addWidget(self.begin_time)

        # 3. - etykieta
        self.end_label_layout = QHBoxLayout()
        self.end_label_layout.addWidget(self.end_label)

        # 4. - data i godzina końca
        self.end_date_time_layout = QHBoxLayout()
        self.end_date_time_layout.addWidget(self.end_date)
        self.end_date_time_layout.addWidget(self.end_time)

        self.full_date_time_layout.addLayout(self.begin_label_layout)
        self.full_date_time_layout.addLayout(self.begin_date_time_layout)
        self.full_date_time_layout.addLayout(self.end_label_layout)
        self.full_date_time_layout.addLayout(self.end_date_time_layout)
        self.full_date_time_layout.setContentsMargins(0, 320, 200, 320)

        # layout główny
        self.start_layout = QHBoxLayout()
        self.start_layout.addLayout(self.button_layout)
        self.start_layout.addLayout(self.full_date_time_layout)
        self.setLayout(self.start_layout)

    # funkcja pobierająca dane
    def get_data(self):

        """
        Pobieranie danych z kalendarza Google.
        :return:
        """

        # nieistniejący zakres czasu
        if self.begin_date.date() > self.end_date.date() or \
                (self.begin_date.date() == self.end_date.date() and
                 self.begin_time.time() >= self.end_time.time()):
            dlg = DialogWindow("Uwaga!", "Wprowadź poprawny zakres czasu!")
            dlg.exec()  # jeśli podany jest zły przedział czasowy - komunikat o błędzie

        # jeśli zakres jest poprawny ale zawiera daty z przeszłości
        if self.begin_date.date() < QDate.currentDate() or (self.begin_date.date() == QDate.currentDate()
                                                            and self.begin_time.time() < QTime.currentTime()):
            dlg = DialogWindow("Uwaga!", "Przedział nie może zawierać dat z przeszłości!")
            dlg.exec()  # jeśli podany jest zły przedział czasowy - komunikat o błędzie

        else:
            self.parent.T_begin, self.parent.T_end = get_time_limits(self.begin_date.date(), self.end_date.date(),
                                                                     self.begin_time.time(), self.end_time.time())
            self.parent.tasks, self.parent.event_ids, self.parent.tasks_obtained = \
                get_tasks_from_calendar(self.parent.T_begin, self.parent.T_end)

            # w przeciwnym wypadku wywoływanie właściwej funkcji pobierającej dane
            if self.parent.tasks_obtained:  # jeśli dane się pobrały - pokaż info
                dlg = DialogWindow("Sukces!", "Lista zadań została pobrana!")
                dlg.exec()
            else:
                dlg = DialogWindow("Niepowodzenie!", "Nie udało się pobrać listy zadań! Sprawdź swój dostęp do "
                                                     "kalendarza lub dodaj zadania manualnie w zakładce "
                                                     "'Dodaj zadania'.")
                dlg.exec()

    def display_tasks(self):
        """
        Wyświetlanie okna z zadaniami.
        :return: NIC
        """
        dlg = TaskWindow(self.parent)
        dlg.exec()

    def clear_data(self):
        """
        Wylogowanie z konta Google i wyczyszczenie wszystkich danych.
        :return: NIC
        """
        log_out()
        self.parent.event_ids = []
        self.parent.tasks_obtained = False
        self.parent.tasks = []
        self.parent.T_begin = None
        self.parent.T_end = None
        self.parent.modes = []
        self.parent.transit_modes = []
        dlg = DialogWindow("Gotowe!", "Wylogowanie zakończone sukcesem. Dane zostały usunięte.")
        dlg.exec()


# OKNO DIALOGOWE

class DialogWindow(QDialog):

    def __init__(self, title, message):
        super(QDialog, self).__init__()

        self.title = title

        self.setWindowTitle(title)

        self.ok_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.accepted.connect(self.accept)

        self.txt = QLabel(message)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.txt)
        self.layout.addWidget(self.ok_button)
        self.setLayout(self.layout)


# OKNO Z DOSTĘPNYMI ZADANIAMI

class TaskWindow(QDialog):

    def __init__(self, parent: StartWindow):
        super(QDialog, self).__init__()

        self.parent = parent

        self.layout = QGridLayout()

        self.data_layout = QHBoxLayout()

        # 5 layoutow (nazwa, lokalizacja, początek, koniec)
        self.names_layout = QVBoxLayout()
        self.locations_layout = QVBoxLayout()
        self.start_date_time_layout = QVBoxLayout()
        self.end_date_time_layout = QVBoxLayout()
        self.fixed_layout = QVBoxLayout()

        # etykiety
        self.name_label = QLabel("NAZWA")
        self.names_layout.addWidget(self.name_label)
        self.location_label = QLabel("LOKALIZACJA")
        self.locations_layout.addWidget(self.location_label)
        self.start_label = QLabel("NAJWCZEŚNIEJSZA DATA I GODZINA ROZPOCZĘCIA")
        self.start_date_time_layout.addWidget(self.start_label)
        self.end_label = QLabel("NAJPÓŹNIEJSZA DATA I GODZINA ZAKOŃCZENIA")
        self.end_date_time_layout.addWidget(self.end_label)
        self.ok_layout = QHBoxLayout()

        if self.parent.tasks_obtained:
            begin_dates = []    # listy zapisujące daty
            end_dates = []
            begin_times = []
            end_times = []
            for task in self.parent.tasks:

                start_layout = QHBoxLayout()
                end_layout = QHBoxLayout()

                task_name = QLabel(task.name)
                task_name.setFixedHeight(30)

                task_location = QLabel(task.location)
                task_location.setFixedHeight(30)

                begin_date = QDateEdit()
                begin_date.setCalendarPopup(True)
                begin_date.setDate(QDate(task.window_left.year, task.window_left.month, task.window_left.day))
                begin_date.setFixedSize(100, 30)
                begin_dates.append(begin_date)

                end_date = QDateEdit()
                end_date.setCalendarPopup(True)
                end_date.setDate(QDate(task.window_right.year, task.window_right.month, task.window_right.day))
                end_date.setFixedSize(100, 30)
                end_dates.append(end_date)

                begin_time = QTimeEdit()
                begin_time.setTime(QTime(task.window_left.hour, task.window_left.minute))
                begin_time.setFixedSize(80, 30)
                begin_times.append(begin_time)

                end_time = QTimeEdit()
                end_time.setTime(QTime(task.window_right.hour, task.window_right.minute))
                end_time.setFixedSize(80, 30)
                end_times.append(end_time)

                start_layout.addWidget(begin_date)
                start_layout.addWidget(begin_time)
                end_layout.addWidget(end_date)
                end_layout.addWidget(end_time)

                self.names_layout.addWidget(task_name)
                self.locations_layout.addWidget(task_location)
                self.start_date_time_layout.addLayout(start_layout)
                self.end_date_time_layout.addLayout(end_layout)

            self.data_layout.addLayout(self.names_layout)
            self.data_layout.addLayout(self.locations_layout)
            self.data_layout.addLayout(self.start_date_time_layout)
            self.data_layout.addLayout(self.end_date_time_layout)
            self.data_layout.addLayout(self.fixed_layout)

            # przycisk zatwierdzający zmienione daty/godziny
            ok_button = QPushButton("Zatwierdź")
            ok_button.clicked.connect(lambda: self.task_data_update(begin_dates, begin_times, end_dates, end_times))

            self.layout.addLayout(self.data_layout, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(ok_button, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            self.layout.setRowStretch(0, 1)
            self.layout.setRowStretch(2, 1)

            self.setWindowTitle("Pobrane zadania")

        else:
            info_label = QLabel("Brak zadań!")
            ok_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            ok_button.accepted.connect(self.accept)

            self.layout.addWidget(info_label, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(ok_button, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)

            self.setWindowTitle("Uwaga!")
            self.setFixedSize(200, 70)

        self.setLayout(self.layout)

    def task_data_update(self, begin_dates, begin_times, end_dates, end_times):

        """
        Metoda aktualizująca okna czasowe zadań.
        :param begin_dates: lista dat rozpoczęcia
        :param begin_times: lista godzin rozpoczęcia
        :param end_dates: lista dat zakończenia
        :param end_times: lista godzin zakończenia
        :return: NIC
        """
        cnt = 0
        for i in range(len(self.parent.tasks)):

            begin_date_time, end_date_time = get_time_limits(begin_dates[i].date(), end_dates[i].date(),
                                                             begin_times[i].time(), end_times[i].time())

            if begin_date_time + timedelta(minutes=self.parent.tasks[i].duration) > end_date_time:
                dlg = DialogWindow("Niepowodzenie!", "Sprawdź poprawność wprowadzonych terminów.")
                dlg.exec()
                break
            else:
                cnt += 1
                self.parent.tasks[i].set_time_windows(begin_date_time, end_date_time)

        if cnt == len(self.parent.tasks):
            dlg = DialogWindow("Sukces!", "Terminy zostały zaktualizowane.")
            dlg.exec()


# PARAMETRY ALGORYTMU ITP.
class ParamTab(QWidget):

    def __init__(self, parent: StartWindow):

        super(ParamTab, self).__init__()

        self.parent = parent

        self.layout = QHBoxLayout()

        # checkboxy
        self.travel_tabel = QLabel("Metody transportu:")

        self.check_walking = QCheckBox("Pieszo")
        self.check_walking.stateChanged.connect(lambda: self.update_travel("walking"))
        self.check_driving = QCheckBox("Samochód")
        self.check_driving.stateChanged.connect(lambda: self.update_travel("driving"))
        self.check_bus = QCheckBox("Autobus")
        self.check_bus.stateChanged.connect(lambda: self.update_travel("bus"))
        self.check_tram = QCheckBox("Tramwaj")
        self.check_tram.stateChanged.connect(lambda: self.update_travel("tram"))
        self.check_rail = QCheckBox("Kolej")
        self.check_rail.stateChanged.connect(lambda: self.update_travel("rail"))
        self.check_bike = QCheckBox("Rower")
        self.check_bike.stateChanged.connect(lambda: self.update_travel("bicycling"))

        # layout na checkboxy
        self.travel_layout = QVBoxLayout()
        self.travel_layout.addWidget(self.travel_tabel)
        self.travel_layout.addWidget(self.check_walking)
        self.travel_layout.addWidget(self.check_driving)
        self.travel_layout.addWidget(self.check_bus)
        self.travel_layout.addWidget(self.check_tram)
        self.travel_layout.addWidget(self.check_rail)
        self.travel_layout.addWidget(self.check_bike)

        self.params_layout = QVBoxLayout()
        self.params_label = QLabel("Parametry:")
        self.params_layout.addWidget(self.params_label)

        # przycisk rozpoczęcia algorytmu
        self.algorithm_button = QPushButton("Algorytm")
        self.algorithm_button.setFixedSize(200, 75)
        self.algorithm_button.clicked.connect(self.generate_initial_solution)
        self.depot_location = QLineEdit("Lokalizacja bazy:")

        self.button_layout = QVBoxLayout()
        self.button_layout.addWidget(self.depot_location)
        self.button_layout.addWidget(self.algorithm_button)
        self.button_layout.setContentsMargins(100, 300, 200, 300)

        self.choice_layout = QVBoxLayout()
        self.choice_layout.addLayout(self.travel_layout)
        self.choice_layout.addLayout(self.params_layout)
        self.choice_layout.setContentsMargins(200, 300, 100, 300)

        self.layout.addLayout(self.choice_layout)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def update_travel(self, mode):

        """
        Metoda do zapisywania wybranych metod transportu.
        :param mode: wybrana metoda transportu
        :return: NIC
        """

        if mode == "walking":
            if self.check_walking.isChecked():
                self.parent.modes.append(mode)
            else:
                self.parent.modes.remove(mode)

        elif mode == "driving":
            if self.check_driving.isChecked():
                self.parent.modes.append(mode)
            else:
                self.parent.modes.remove(mode)

        elif mode == "bicycle":
            if self.check_bike.isChecked():
                self.parent.modes.append(mode)
            else:
                self.parent.modes.remove(mode)

        elif mode == "bus":
            if self.check_bus.isChecked():
                if "transit" not in self.parent.modes:
                    self.parent.modes.append("transit")
                self.parent.transit_modes.append(mode)
            else:
                if not self.check_tram.isChecked() and not self.check_rail.isChecked():
                    self.parent.modes.remove("transit")
                self.parent.transit_modes.remove(mode)

        elif mode == "tram":
            if self.check_tram.isChecked():
                if "transit" not in self.parent.modes:
                    self.parent.modes.append("transit")
                self.parent.transit_modes.append(mode)
            else:
                if not self.check_bus.isChecked() and not self.check_rail.isChecked():
                    self.parent.modes.remove("transit")
                self.parent.transit_modes.remove(mode)

        elif mode == "rail":
            if self.check_rail.isChecked():
                if "transit" not in self.parent.modes:
                    self.parent.modes.append("transit")
                self.parent.transit_modes.append(mode)
            else:
                if not self.check_bus.isChecked() and not self.check_tram.isChecked():
                    self.parent.modes.remove("transit")
                self.parent.transit_modes.remove(mode)

    def generate_initial_solution(self):
        """
        Generacja rozwiązania początkowego (inicjalizacja).
        :return:
        """

        if not self.parent.T_begin or not self.parent.T_end or not self.parent.tasks_obtained:
            dlg = DialogWindow("Błąd!", "Pobierz zadania z kalendarza.")
            dlg.exec()
        elif validate_location(self.depot_location.text()):
            depot = create_depot(self.depot_location.text(), self.parent.T_begin, self.parent.T_end)
            self.parent.tasks.insert(0, depot)
            self.parent.solution = initial_solution(self.parent.T_begin, self.parent.T_end, self.parent.tasks, self.parent.modes)       # na razie testy tylko dla walking
        else:
            dlg = DialogWindow("Błąd!", "Podaj poprawny adres startowy.")
            dlg.exec()
