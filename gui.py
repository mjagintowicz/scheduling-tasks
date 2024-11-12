from PyQt6.QtWidgets import QMainWindow, QPushButton, QHBoxLayout, QWidget, QDateEdit, QVBoxLayout, QLabel, QTimeEdit, \
    QTabWidget, QDialog, QDialogButtonBox, QFrame
from PyQt6.QtCore import Qt, QDate, QTime, QTimer
from PyQt6.QtGui import QFont

from calendar_functions import *
from model_params import Task


# OKNO STARTOWE

class StartWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # tytuł okna
        self.setWindowTitle('Optymalizacja harmonogramu')

        # rozmiar okna
        self.setFixedSize(1500, 850)

        # layout główny
        self.tab_layout = QVBoxLayout()

        # zmienne
        self.tasks_obtained = False  # flaga czy zadania zostały już pobrane
        self.tasks = []  # lista pobranych zadań
        self.T_begin = None  # początek i koniec harmonogramu
        self.T_end = None

        # zakładki
        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)
        self.setCentralWidget(self.tabs)
        self.show()

        # zakładka 1. - wczytywanie danych
        self.tab1 = TaskTab(self)
        self.tabs.addTab(self.tab1, "Zadania")


# WCZYTYWANIE DANYCH

class TaskTab(QWidget):

    def __init__(self, parent: StartWindow):

        super(TaskTab, self).__init__()

        self.parent = parent

        # przycisk startowy
        self.start_button = QPushButton('Pobierz zadania\nz kalendarza', self)
        self.start_button.setFixedSize(400, 200)
        self.start_button.setFont(QFont('Calibri', 25))
        self.start_button.clicked.connect(self.get_data)  # po kliknięciu funkcja

        # przycisk otwierający okno podgląd
        self.tasks_button = QPushButton('Twoje zadania', self)
        self.tasks_button.setFixedSize(400, 200)
        self.tasks_button.setFont(QFont('Calibri', 25))
        self.tasks_button.clicked.connect(self.display_tasks)

        # layout do przycisków
        self.button_layout = QVBoxLayout()
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.tasks_button)

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
        self.full_date_time_layout.setContentsMargins(0, 320, 0, 320)

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

        if self.begin_date.date() > self.end_date.date() or \
                (self.begin_date.date() == self.end_date.date() and
                 self.begin_time.date() >= self.end_time.date()):
            dlg = DialogWindow("Uwaga!", "Wprowadź poprawny zakres czasu!")
            dlg.exec()  # jeśli podany jest zły przedział czasowy - komunikat o błędzie

        else:
            self.parent.T_begin, self.parent.T_end = get_schedule_limits(self.begin_date.date(), self.end_date.date(),
                                                                         self.begin_time.time(), self.end_time.time())
            self.parent.tasks, self.parent.tasks_obtained = get_tasks_from_calendar(self.parent.T_begin,
                                                                                    self.parent.T_end)

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

        dlg = TaskWindow(self.parent)
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
        self.title = 'Zadania'

        self.layout = QVBoxLayout()

        if self.parent.tasks_obtained:
            for task in self.parent.tasks:

                task_layout = QHBoxLayout()

                task_name = QLabel(task.name)
                task_location = QLabel(task.location)

                begin_date = QDateEdit()
                begin_date.setCalendarPopup(True)
                begin_date.setDate(self.parent.T_begin)
                begin_date.setFixedSize(100, 30)

                end_date = QDateEdit()
                end_date.setCalendarPopup(True)
                end_date.setDate(self.parent.T_end)
                end_date.setFixedSize(100, 30)\

                task_layout.addWidget(task_name)
                task_layout.addWidget(task_location)
                task_layout.addWidget(begin_date)
                task_layout.addWidget(end_date)
                self.layout.addLayout(task_layout)

                # timeedit
                # ok button
                # update okien czasowych przy zmianie parametrów daty w tym oknie

        else:
            info_label = QLabel("Brak zadań")
            self.layout.addWidget(info_label)

        self.setLayout(self.layout)
