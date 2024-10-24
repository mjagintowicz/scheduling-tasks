from PyQt6.QtWidgets import QMainWindow, QPushButton, QHBoxLayout, QWidget, QDateEdit, QVBoxLayout, QLabel, QTimeEdit, \
    QTabWidget, QDialog, QDialogButtonBox, QFrame
from PyQt6.QtCore import Qt, QDate, QTime, QTimer
from PyQt6.QtGui import QFont

from calendar_functions import *


# OKNO STARTOWE

class StartWindow(QMainWindow):

    def __init__(self):
        super(StartWindow, self).__init__()

        # tytuł okna
        self.setWindowTitle('Optymalizacja harmonogramu')

        # rozmiar okna
        self.setFixedSize(1500, 850)

        # layout główny
        self.tab_layout = QVBoxLayout()

        # zmienne
        self.tasks_obtained = False  # flaga czy zadania zostały już pobrane
        self.tasks = []  # lista pobranych zadań
        self.T_begin = None # początek i koniec harmonogramu
        self.T_end = None

        # zakładki
        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)
        self.setCentralWidget(self.tabs)
        self.show()

        # zakładka 1. - wczytywanie danych
        self.tab1 = GetDataTab(self)
        self.tabs.addTab(self.tab1, "Wczytaj zadania")

        # zakładka 2. - dodawanie nowych zadań do kalendarza
        self.tab2 = AddDataTab(self)
        self.tabs.addTab(self.tab2, "Dodaj zadania")

        # zakładka 3. - zadania (możliwe, że zastąpi 2.)
        self.tab3 = TaskTab(self)
        self.tabs.addTab(self.tab3, "Zadania")


# WCZYTYWANIE DANYCH

class GetDataTab(QWidget):

    def __init__(self, parent: StartWindow):

        super(GetDataTab, self).__init__()

        self.parent = parent

        # przycisk startowy
        self.start_button = QPushButton('Pobierz zadania\nz kalendarza', self)
        self.start_button.setFixedSize(400, 200)
        self.start_button.setFont(QFont('Calibri', 25))
        self.start_button.clicked.connect(self.get_data)  # po kliknięciu funkcja

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
        self.start_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.start_layout.addLayout(self.full_date_time_layout)
        self.setLayout(self.start_layout)

    # funkcja pobierająca dane
    def get_data(self):

        if self.begin_date.date() > self.end_date.date() or \
                (self.begin_date.date() == self.end_date.date() and
                 self.begin_time.date() >= self.end_time.date()):
            dlg = DialogWindow("Uwaga!", "Wprowadź poprawny zakres czasu!")
            dlg.exec()  # jeśli podany jest zły przedział czasowy - komunikat o błędzie

        else:
            self.parent.tasks, self.parent.tasks_obtained = get_tasks_from_calendar(self.begin_date.date(),
                                                                                    self.end_date.date(),
                                                                                    self.begin_time.time(),
                                                                                    self.end_time.time())
            self.parent.T_begin, self.parent.T_end = get_schedule_limits(self.begin_date.date(), self.end_date.date(),
                                                                         self.begin_time.time(), self.end_time.time())

            # w przeciwnym wypadku wywoływanie właściwej funkcji pobierającej dane
            if self.parent.tasks_obtained:  # jeśli dane się pobrały - pokaż info
                dlg = DialogWindow("Sukces!", "Lista zadań została pobrana!")
                dlg.exec()
            else:
                dlg = DialogWindow("Niepowodzenie!", "Nie udało się pobrać listy zadań! Sprawdź swój dostęp do "
                                                     "kalendarza lub dodaj zadania manualnie w zakładce "
                                                     "'Dodaj zadania'.")
                dlg.exec()


class AddDataTab(QWidget):

    def __init__(self, parent: StartWindow):
        super(AddDataTab, self).__init__()

        self.parent = parent

        # layout główny
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # 1. utworzenie manualnie całkiem nowego setu zadań
        self.layout_1 = QHBoxLayout()
        self.layout.addLayout(self.layout_1)

        self.label_1 = QLabel("Utwórz nową listę zadań")
        self.layout_1.addWidget(self.label_1)

        # 2. dodanie manulanie zadań do pobranego setu
        self.layout_2 = QHBoxLayout()
        self.layout.addLayout(self.layout_2)

        self.label_2 = QLabel("Dodaj zadania do aktualnej listy")
        self.layout_2.addWidget(self.label_2)


class TaskTab(QWidget):

    def __init__(self, parent: StartWindow):

        super(TaskTab, self).__init__()

        self.parent = parent

        # layout główny
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_label = QLabel("Twoje zadania")
        self.layout.addWidget(self.title_label)

        # ramka, jeśli zadań nie ma
        self.info_label = QLabel("Brak zadań! Pobierz je ze swojego kalendarza lub dodaj ręcznie.")
        self.add_button = QPushButton("Dodaj zadanie +")

        self.layout_no_tasks = QVBoxLayout()
        self.layout_no_tasks.addWidget(self.info_label)
        self.layout_no_tasks.addWidget(self.add_button)
        self.frame_no_tasks = QFrame()
        self.frame_no_tasks.setLayout(self.layout_no_tasks)

        self.layout.addWidget(self.frame_no_tasks)

        # ramka, jeśli są już zadania (przycisk na razie nie działa)
        self.layout_tasks = QVBoxLayout()
        self.frame_tasks = QFrame()
        self.frame_tasks.setLayout(self.layout_tasks)

        if not self.parent.tasks_obtained:
            self.frame_tasks.hide()
            self.frame_no_tasks.show()

        if self.parent.tasks_obtained:
            for task in self.parent.tasks:
                task_label = QLabel(str(task))
                self.layout_tasks.addWidget(task_label)
            self.frame_no_tasks.hide()
            self.frame_tasks.show()

        # QTimer do odświeżania zakładki???
        # albo do sprawdzania czy nastąpiła jakaś zmiana w zmiennych
        # np. refresh_request wysłany - startwindow od nowa załadaje zakładkęs


# OKNO DIALOGOWE

class DialogWindow(QDialog):

    def __init__(self, title, message):
        super(QDialog, self).__init__()

        self.title = title
        self.message = message

        self.setWindowTitle(title)

        self.ok_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.accepted.connect(self.accept)

        self.txt = QLabel(message)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.txt)
        self.layout.addWidget(self.ok_button)
        self.setLayout(self.layout)
