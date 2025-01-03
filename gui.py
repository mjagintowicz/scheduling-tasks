from PyQt6.QtWidgets import QMainWindow, QPushButton, QHBoxLayout, QWidget, QDateEdit, QVBoxLayout, QLabel, QTimeEdit, \
    QTabWidget, QDialog, QDialogButtonBox, QGridLayout, QCheckBox, QLineEdit, QSpinBox, QDoubleSpinBox, QTableWidget,\
    QTableWidgetItem
from PyQt6.QtCore import Qt

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import dill
import os
from random import choice

from calendar_functions import *
from init_heuristic import create_depot
from map_functions import *
from sa import simmulated_annealing

matplotlib.use('QtAgg')

key_active = False


# !!! wczytanie losowego rozwiązania z wcześniej wygenerowanych
def load_random_solution(folder_path: str = 'examples'):
    """
    Wczytywanie losowego rozwiazania z wcześniej wygenerowanych.
    :param folder_path: folder z rozwiązaniami
    :return:
    """
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    pkl_files = [f for f in files if f.endswith('.pkl')]
    selected_file = choice(pkl_files)
    file_path = os.path.join(folder_path, selected_file)
    with open(file_path, 'rb') as f:
        result = dill.load(f)
        test_sol = result['solution']
        test_obj = result['obj']
    return test_sol, test_obj


if not key_active:
    test_sol, test_obj = load_random_solution()      # wczytywanie, bo klucz api jest niedostępny


# OKNO STARTOWE
class StartWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # tytuł okna
        self.setWindowTitle('Optymalizacja harmonogramu')

        # rozmiar okna
        self.setFixedSize(1000, 750)

        # layout główny
        self.tab_layout = QVBoxLayout()

        # zmienne
        self.event_ids = []  # unikalne id każdego zadania/eventu
        self.tasks_obtained = False  # flaga czy zadania zostały już pobrane
        self.tasks = []  # lista pobranych zadań
        self.T_begin = None  # początek i koniec harmonogramu
        self.T_end = None
        self.modes = []  # informacje na temat wybranych środków transportu
        self.transit_modes = []
        if not key_active:
            self.solution = test_sol
            self.objectives = test_obj
        else:
            self.solution = []
            self.objectives = []

        self.temp_0 = None
        self.temp_end = None
        self.alpha = None
        self.series_num = None

        self.neighbourhood_prob = [0, 0, 0, 0]
        self.weights = [0, 0, 0]

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

        # zakładka 3. - wyniki
        self.tab3 = ResultTab(self)
        self.tabs.addTab(self.tab3, "Wyniki")


# WCZYTYWANIE DANYCH
class TaskTab(QWidget):

    def __init__(self, parent: StartWindow):

        super(TaskTab, self).__init__()

        self.parent = parent

        # przycisk startowy
        self.start_button = QPushButton('Pobierz zadania\nz kalendarza', self)
        self.start_button.setFixedSize(200, 75)
        font = self.start_button.font()
        font.setPointSize(15)
        self.start_button.setFont(font)
        self.start_button.clicked.connect(self.get_data)  # po kliknięciu funkcja

        # przycisk otwierający okno podgląd
        self.tasks_button = QPushButton('Potwierdź listę zadań', self)
        self.tasks_button.setFixedSize(200, 75)
        font = self.tasks_button.font()
        font.setPointSize(15)
        self.tasks_button.setFont(font)
        self.tasks_button.clicked.connect(self.display_tasks)

        self.log_out_button = QPushButton('Wyloguj się', self)
        self.log_out_button.setFixedSize(200, 75)
        font = self.log_out_button.font()
        font.setPointSize(15)
        self.log_out_button.setFont(font)
        self.log_out_button.clicked.connect(self.clear_data)

        # layout do przycisków
        self.button_layout = QVBoxLayout()
        self.button_layout.setContentsMargins(100, 190, 100, 190)
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
        self.begin_label.setFixedSize(200, 30)

        self.end_label = QLabel('Koniec harmonogramu:')
        self.end_label.setFixedSize(200, 30)

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
        self.full_date_time_layout.setContentsMargins(0, 270, 180, 270)

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
        if not key_active:   # załaduj losowo inne rozwiązanie, jeśli nie ma dostępu do api
            self.parent.solution, self.parent.objectives = load_random_solution()
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
            begin_dates = []  # listy zapisujące daty
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
        self.travel_tabel.setFixedSize(150, 20)

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
        self.params_label = QLabel("Parametry algorytmu:")
        self.params_label.setFixedSize(150, 20)

        self.temp_begin_layout = QHBoxLayout()
        self.temp_begin_label = QLabel("Temperatura początkowa:")
        self.temp_begin_label.setFixedSize(200, 30)
        self.temp_begin_spin = QDoubleSpinBox()
        self.temp_begin_spin.setRange(0, 100000)
        self.temp_begin_spin.setValue(100)
        self.temp_begin_spin.setFixedSize(80, 30)
        self.parent.temp_0 = self.temp_begin_spin.value()
        self.temp_begin_spin.valueChanged.connect(lambda: self.set_temp_0())
        self.temp_begin_layout.addWidget(self.temp_begin_label)
        self.temp_begin_layout.addWidget(self.temp_begin_spin)

        self.temp_end_layout = QHBoxLayout()
        self.temp_end_label = QLabel("Temperatura końcowa:")
        self.temp_end_label.setFixedSize(200, 30)
        self.temp_end_spin = QDoubleSpinBox()
        self.temp_end_spin.setRange(0.000001, 100000)
        self.temp_end_spin.setValue(0.1)
        self.temp_end_spin.setFixedSize(80, 30)
        self.parent.temp_end = self.temp_end_spin.value()
        self.temp_end_spin.valueChanged.connect(lambda: self.set_temp_end())
        self.temp_end_layout.addWidget(self.temp_end_label)
        self.temp_end_layout.addWidget(self.temp_end_spin)

        self.alpha_layout = QHBoxLayout()
        self.alpha_label = QLabel("Współczynnik chłodzenia:")
        self.alpha_label.setFixedSize(200, 30)
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0, 1)
        self.alpha_spin.setValue(0.65)
        self.alpha_spin.setFixedSize(80, 30)
        self.parent.alpha = self.alpha_spin.value()
        self.alpha_spin.valueChanged.connect(lambda: self.set_alpha())
        self.alpha_layout.addWidget(self.alpha_label)
        self.alpha_layout.addWidget(self.alpha_spin)

        self.series_layout = QHBoxLayout()
        self.series_label = QLabel("Liczba serii:")
        self.series_label.setFixedSize(200, 30)
        self.series_spin = QSpinBox()
        self.series_spin.setFixedSize(80, 30)
        self.series_spin.setRange(1, 100)
        self.parent.series = self.series_spin.value()
        self.series_spin.valueChanged.connect(lambda: self.set_series_num())
        self.series_layout.addWidget(self.series_label)
        self.series_layout.addWidget(self.series_spin)

        self.params_layout.addWidget(self.params_label)
        self.params_layout.addLayout(self.temp_begin_layout)
        self.params_layout.addLayout(self.temp_end_layout)
        self.params_layout.addLayout(self.alpha_layout)
        self.params_layout.addLayout(self.series_layout)

        # layout na sąsiedztwo
        self.neighbourhood_layout = QVBoxLayout()

        self.neighbourhood_label = QLabel("Prawdopodobieństwa operatorów sąsiedztwa [%]:")
        self.neighbourhood_label.setFixedSize(270, 30)

        self.operator1_layout = QHBoxLayout()
        self.operator1_label = QLabel("Intra-route reinsertion:")
        self.operator1_label.setFixedSize(200, 30)
        self.operator1_layout.addWidget(self.operator1_label)
        self.operator1_spin = QSpinBox()
        self.operator1_spin.setFixedSize(80, 30)
        self.operator1_spin.setRange(0, 100)
        self.operator1_spin.setValue(30)
        self.operator1_spin.valueChanged.connect(lambda: self.set_neighbourhood_probabilities())
        self.operator1_layout.addWidget(self.operator1_spin)

        self.operator2_layout = QHBoxLayout()
        self.operator2_label = QLabel("Inter-route shift random:")
        self.operator2_label.setFixedSize(200, 30)
        self.operator2_layout.addWidget(self.operator2_label)
        self.operator2_spin = QSpinBox()
        self.operator2_spin.setFixedSize(80, 30)
        self.operator2_spin.setRange(0, 100)
        self.operator2_spin.setValue(30)
        self.operator2_spin.valueChanged.connect(lambda: self.set_neighbourhood_probabilities())
        self.operator2_layout.addWidget(self.operator2_spin)

        self.operator3_layout = QHBoxLayout()
        self.operator3_label = QLabel("Inter-route shift (the most busy day):")
        self.operator3_label.setFixedSize(200, 30)
        self.operator3_layout.addWidget(self.operator3_label)
        self.operator3_spin = QSpinBox()
        self.operator3_spin.setFixedSize(80, 30)
        self.operator3_spin.setRange(0, 100)
        self.operator3_spin.setValue(30)
        self.operator3_spin.valueChanged.connect(lambda: self.set_neighbourhood_probabilities())
        self.operator3_layout.addWidget(self.operator3_spin)

        self.operator4_layout = QHBoxLayout()
        self.operator4_label = QLabel("Inter-route shift (the least busy day):")
        self.operator4_label.setFixedSize(200, 30)
        self.operator4_layout.addWidget(self.operator4_label)
        self.operator4_spin = QSpinBox()
        self.operator4_spin.setFixedSize(80, 30)
        self.operator4_spin.setRange(0, 100)
        self.operator4_spin.setValue(10)
        self.operator4_spin.valueChanged.connect(lambda: self.set_neighbourhood_probabilities())
        self.operator4_layout.addWidget(self.operator4_spin)

        self.parent.neighbourhood_prob = [self.operator1_spin.value(), self.operator2_spin.value(),
                                          self.operator3_spin.value(), self.operator4_spin.value()]
        self.weights_sum = sum([self.operator1_spin.value(), self.operator2_spin.value(), self.operator3_spin.value(),
                                self.operator4_spin.value()])
        self.neighbourhood_layout.addWidget(self.neighbourhood_label)
        self.neighbourhood_layout.addLayout(self.operator1_layout)
        self.neighbourhood_layout.addLayout(self.operator2_layout)
        self.neighbourhood_layout.addLayout(self.operator3_layout)
        self.neighbourhood_layout.addLayout(self.operator4_layout)
        self.probabilities_sum = 0

        # przycisk rozpoczęcia algorytmu
        self.algorithm_button = QPushButton("Algorytm")
        font = self.algorithm_button.font()
        font.setPointSize(15)
        self.algorithm_button.setFont(font)
        self.algorithm_button.setFixedSize(200, 75)
        self.algorithm_button.clicked.connect(lambda: self.generate_solution())

        # wpisywanie bazy
        self.depot_layout = QVBoxLayout()
        self.depot_label = QLabel("Lokalizacja bazy:")
        self.depot_label.setFixedSize(200, 30)
        self.depot_location = QLineEdit()
        self.depot_location.setFixedSize(200, 30)
        self.depot_layout.addWidget(self.depot_label)
        self.depot_layout.addWidget(self.depot_location)

        # wagi funkcji celu
        self.weights_layout = QVBoxLayout()
        self.weights_label = QLabel("Wagi kryteriów funkcji celu [%]:")
        self.weights_label.setFixedSize(200, 30)
        self.weights_layout.addWidget(self.weights_label)
        self.weights_sum = 0

        self.weight1_layout = QHBoxLayout()
        self.weight1_label = QLabel("Czas podróży:")
        self.weight1_label.setFixedSize(200, 30)
        self.weight1_spin = QSpinBox()
        self.weight1_spin.setFixedSize(80, 30)
        self.weight1_spin.setRange(0, 100)
        self.weight1_spin.setValue(50)
        self.weight1_spin.valueChanged.connect(lambda: self.set_weights())
        self.weight1_layout.addWidget(self.weight1_label)
        self.weight1_layout.addWidget(self.weight1_spin)

        self.weight2_layout = QHBoxLayout()
        self.weight2_label = QLabel("Koszt podróży:")
        self.weight2_label.setFixedSize(200, 30)
        self.weight2_spin = QSpinBox()
        self.weight2_spin.setFixedSize(80, 30)
        self.weight2_spin.setRange(0, 100)
        self.weight2_spin.setValue(0)
        self.weight2_spin.valueChanged.connect(lambda: self.set_weights())
        self.weight2_layout.addWidget(self.weight2_label)
        self.weight2_layout.addWidget(self.weight2_spin)

        self.weight3_layout = QHBoxLayout()
        self.weight3_label = QLabel("Czas oczekiwania:")
        self.weight3_label.setFixedSize(200, 30)
        self.weight3_spin = QSpinBox()
        self.weight3_spin.setFixedSize(80, 30)
        self.weight3_spin.setRange(0, 100)
        self.weight3_spin.setValue(50)
        self.weight3_spin.valueChanged.connect(lambda: self.set_weights())
        self.weight3_layout.addWidget(self.weight3_label)
        self.weight3_layout.addWidget(self.weight3_spin)

        self.parent.weights = [self.weight1_spin.value(), self.weight2_spin.value(), self.weight3_spin.value()]
        self.probabilities_sum = sum([self.weight1_spin.value(), self.weight2_spin.value(), self.weight3_spin.value()])

        self.weights_layout.addLayout(self.weight1_layout)
        self.weights_layout.addLayout(self.weight2_layout)
        self.weights_layout.addLayout(self.weight3_layout)

        self.button_layout = QVBoxLayout()
        self.button_layout.addWidget(self.algorithm_button)

        self.choice_layout = QVBoxLayout()
        self.choice_layout.addLayout(self.travel_layout)
        self.choice_layout.addLayout(self.params_layout)
        self.choice_layout.addLayout(self.neighbourhood_layout)
        self.choice_layout.addLayout(self.depot_layout)
        self.choice_layout.setContentsMargins(0, 20, 100, 20)

        self.right_layout = QVBoxLayout()
        self.right_layout.addLayout(self.weights_layout)
        self.right_layout.addLayout(self.button_layout)

        self.layout.addLayout(self.choice_layout)
        self.layout.addLayout(self.right_layout)
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

    def set_temp_0(self):
        """
        Ustawienie temperatury początkowej.
        :return:
        """
        self.parent.temp_0 = self.temp_begin_spin.value()

    def set_temp_end(self):
        """
        Ustawienie temperatury końcowej.
        :return:
        """
        self.parent.temp_end = self.temp_end_spin.value()

    def set_alpha(self):
        """
        Ustawienie współczynnika chłodzenia.
        :return:
        """
        self.parent.alpha = self.alpha_spin.value()

    def set_series_num(self):
        """
        Ustawienie liczby serii.
        :return:
        """
        self.parent.series_num = self.series_spin.value()

    def set_neighbourhood_probabilities(self):
        """
        Ustawienie prawdopodobieństw operatorów sąsiedztwa.
        :return:
        """
        self.parent.neighbourhood_prob[0] = self.operator1_spin.value()
        self.parent.neighbourhood_prob[1] = self.operator2_spin.value()
        self.parent.neighbourhood_prob[2] = self.operator3_spin.value()
        self.parent.neighbourhood_prob[3] = self.operator4_spin.value()

        self.probabilities_sum = sum(self.parent.neighbourhood_prob)

    def set_weights(self):
        """
        Ustawienie wag dla kryteriów funkcji celu.
        :return:
        """
        self.parent.weights[0] = self.weight1_spin.value()
        self.parent.weights[1] = self.weight2_spin.value()
        self.parent.weights[2] = self.weight3_spin.value()

        self.weights_sum = sum(self.parent.weights)

    def generate_solution(self):
        """
        Generacja rozwiązania początkowego (inicjalizacja).
        :return:
        """

        if not self.parent.T_begin or not self.parent.T_end or not self.parent.tasks_obtained:
            dlg = DialogWindow("Błąd!", "Pobierz zadania z kalendarza.")
            dlg.exec()
        elif not self.parent.modes:
            dlg = DialogWindow("Błąd!", "Wybierz co najmniej jedną metodę podróży.")
            dlg.exec()
        elif self.parent.temp_0 <= self.parent.temp_end:
            dlg = DialogWindow("Błąd!", "Podaj poprawne wartości temperatury.")
            dlg.exec()
        elif self.parent.alpha >= 1 or self.parent.alpha <= 0:
            dlg = DialogWindow("Błąd!", "Podaj poprawny współczynnik chłodzenia.")
            dlg.exec()
        elif self.probabilities_sum != 100:
            dlg = DialogWindow("Błąd!", "Suma prawdopodobieństw musi wynosić 100%.")
            dlg.exec()
        elif not validate_location(self.depot_location.text()):
            dlg = DialogWindow("Błąd!", "Podaj poprawny adres startowy.")
            dlg.exec()
        elif not self.weights_sum != 100:
            dlg = DialogWindow("Błąd!", "Suma wag musi wynosić 100%.")
            dlg.exec()
        elif not key_active:
            dlg = DialogWindow("BŁĄD!", "KLUCZ API NIEAKTYWNY!")
            dlg.exec()
        else:
            depot = create_depot(self.depot_location.text(), self.parent.T_begin, self.parent.T_end)
            self.parent.tasks.insert(0, depot)

            self.parent.solution, self.parent.objectives = simmulated_annealing(self.parent.T_begin, self.parent.T_end,
                                                                                self.parent.tasks, self.parent.temp_0,
                                                                                self.parent.temp_end, self.parent.alpha,
                                                                                self.parent.series_num,
                                                                                self.parent.neighbourhood_prob,
                                                                                self.parent.weights, self.parent.modes,
                                                                                self.parent.transit_modes)
            if self.parent.solution is None:
                dlg = DialogWindow("Błąd!", "Nie można wygenerować rozwiązania początkowego.")
                dlg.exec()


# klasa do tworzenia pola z wykresem
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


# WIZUALIZACJA ROZWIĄZANIA
class ResultTab(QWidget):

    def __init__(self, parent: StartWindow):
        super(ResultTab, self).__init__()

        self.parent = parent

        self.main_layout = QVBoxLayout()

        self.solution_layout = QHBoxLayout()

        self.table_layout = QVBoxLayout()  # layout na tekst
        self.table_main = QTableWidget()
        self.table_main.setRowCount(1)
        self.table_main.setColumnCount(3)
        self.table_main.setColumnWidth(0, 170)
        self.table_main.setColumnWidth(1, 150)
        self.table_main.setColumnWidth(2, 120)
        self.table_main.setItem(0, 0, QTableWidgetItem("Data i godzina rozpoczęcia"))
        self.table_main.setItem(0, 1, QTableWidgetItem("Nazwa zadania"))
        self.table_main.setItem(0, 2, QTableWidgetItem("Sposób podróży"))
        self.table_layout.addWidget(self.table_main)

        self.plot_layout = QVBoxLayout()  # layout na wykres
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.sc.axes.plot([], [])
        self.sc.axes.set_xlabel("Iteracja")
        self.sc.axes.set_ylabel("F(S)")
        self.sc.axes.xaxis.set_ticks([])
        self.sc.axes.yaxis.set_ticks([])
        self.plot_layout.addWidget(self.sc)

        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(200, 100, 200, 100)
        self.display_button = QPushButton("Pokaż rozwiązanie")
        font = self.display_button.font()
        font.setPointSize(15)
        self.display_button.setFont(font)
        self.display_button.setFixedSize(200, 75)
        self.display_button.clicked.connect(lambda: self.show_solution())
        self.button_layout.addWidget(self.display_button)
        self.send_button = QPushButton("Wyślij do kalendarza")

        self.send_button.setFixedSize(200, 75)
        font = self.send_button.font()
        font.setPointSize(15)
        self.send_button.setFont(font)
        self.send_button.clicked.connect(lambda: self.update_calendar())
        self.button_layout.addWidget(self.send_button)

        self.solution_layout.addLayout(self.table_layout)
        self.solution_layout.addLayout(self.plot_layout)

        self.main_layout.addLayout(self.solution_layout)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

    def create_route_table(self):
        """
        Rysowanie tabeli z rozwiązaniem.
        :return: NIC
        """
        # liczenie ile będzie wierszy
        self.table_layout.removeWidget(self.table_main)
        self.table_main = QTableWidget()
        rows = 1
        for i in range(len(self.parent.solution)):
            rows += len(self.parent.solution[i].tasks) - 1

        self.table_main.setRowCount(rows)
        self.table_main.setColumnCount(3)
        self.table_main.setColumnWidth(0, 170)
        self.table_main.setColumnWidth(1, 150)
        self.table_main.setColumnWidth(2, 120)
        self.table_main.setItem(0, 0, QTableWidgetItem("Data i godzina rozpoczęcia"))
        self.table_main.setItem(0, 1, QTableWidgetItem("Nazwa zadania"))
        self.table_main.setItem(0, 2, QTableWidgetItem("Sposób podróży"))

        row = 1
        for i in range(len(self.parent.solution)):
            for j in range(1, len(self.parent.solution[i].tasks)):
                if self.parent.solution[i].tasks[j].name == "Dom":
                    self.table_main.setItem(row, 0, QTableWidgetItem(" "))
                    self.table_main.setItem(row, 1, QTableWidgetItem("POWRÓT"))
                    self.table_main.setItem(row, 2, QTableWidgetItem(self.parent.solution[i].tasks[j].travel_method))
                else:
                    self.table_main.setItem(row, 0, QTableWidgetItem(str(self.parent.solution[i].tasks[j].start_date_time)))
                    self.table_main.setItem(row, 1, QTableWidgetItem(self.parent.solution[i].tasks[j].name))
                    self.table_main.setItem(row, 2, QTableWidgetItem(self.parent.solution[i].tasks[j].travel_method))
                row += 1

        self.table_layout.addWidget(self.table_main)

    def create_plot(self):
        """
        Rysowanie wykresu funkcji celu przetwarzanych rozwiązać w kolejnych iteracjach.
        :return: NIC
        """
        self.plot_layout.removeWidget(self.sc)
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        iter_list = [i for i in range(1, len(self.parent.objectives)+1)]
        self.sc.axes.plot(iter_list, self.parent.objectives, color='hotpink')
        self.sc.axes.set_xlabel("Iteracja")
        self.sc.axes.set_ylabel("Wartość funkcji celu przetwarzanego rozwiązania")
        self.sc.axes.set_title("Wykres funkcji celu w kolejnych iteracjach")
        self.plot_layout.addWidget(self.sc)

    def show_solution(self):
        """
        Wyświetlenie rozwiązania.
        :return: NIC
        """
        if not self.parent.solution:
            dlg = DialogWindow("Błąd!", "Brak rozwiązania.")
            dlg.exec()
        else:
            self.create_route_table()
            self.create_plot()

    def update_calendar(self):
        """
        Aktualizacja kalendarza Google.
        :return: NIC
        """
        if not self.parent.solution:
            dlg = DialogWindow("Błąd!", "Brak rozwiązania.")
            dlg.exec()
        elif not self.parent.event_ids:
            dlg = DialogWindow("Uwaga!", "Zadania z rozwiązania mogą nachodzć na inne.")
            dlg.exec()
            add_all_tasks(self.parent.solution, self.parent.event_ids)
            dlg = DialogWindow("Sukces!", "Zadania zostały dodane!")
            dlg.exec()
        else:
            add_all_tasks(self.parent.solution, self.parent.event_ids)
            dlg = DialogWindow("Sukces!", "Zadania zostały dodane!")
            dlg.exec()
