from PyQt6.QtWidgets import QMainWindow, QPushButton, QHBoxLayout, QWidget, QDateEdit, QVBoxLayout, QLabel, QTimeEdit, QTabWidget
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont

from calendar import get_tasks_from_calendar


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

        # zakładki
        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)
        self.setCentralWidget(self.tabs)
        self.show()

        # zakładka 1. - wczytywanie danych
        self.tab1 = GetDataTab()
        self.tabs.addTab(self.tab1, "Wczytaj zadania")

        # zakładka 2. - dodawanie nowych zadań do kalendarza
        self.tab2 = AddDataTab()
        self.tabs.addTab(self.tab2, "Dodaj zadania")


# WCZYTYWANIE DANYCH

class GetDataTab(QWidget):

    def __init__(self):

        super(QWidget, self).__init__()

        # przycisk startowy
        self.start_button = QPushButton('Pobierz zadania\nz kalendarza', self)
        self.start_button.setFixedSize(400, 200)
        self.start_button.setFont(QFont('Calibri', 25))
        self.start_button.clicked.connect(self.get_data)    # po kliknięciu funkcja

        self.tasks_obtained = False     # flaga

        # wybór dat
        self.begin_date = QDateEdit()
        self.begin_date.setCalendarPopup(True)
        self.begin_date.setDate(QDate.currentDate())  # domyślnie dziś
        self.begin_date.setFixedSize(100, 30)

        self.finish_date = QDateEdit()
        self.finish_date.setCalendarPopup(True)
        self.finish_date.setDate(QDate.currentDate().addDays(14))  # domyślnie koniec po 2 tygodniach
        self.finish_date.setFixedSize(100, 30)

        # wybór godzin
        self.begin_time = QTimeEdit()
        self.begin_time.setTime(QTime.currentTime())
        self.begin_time.setFixedSize(80, 30)

        self.finish_time = QTimeEdit()
        self.finish_time.setTime(QTime.currentTime())
        self.finish_time.setFixedSize(80, 30)

        # etykiety
        self.begin_label = QLabel('Początek harmonogramu:')
        self.begin_label.setFixedSize(200, 20)

        self.finish_label = QLabel('Koniec harmonogramu:')
        self.finish_label.setFixedSize(200, 20)

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
        self.finish_label_layout = QHBoxLayout()
        self.finish_label_layout.addWidget(self.finish_label)

        # 4. - data i godzina końca
        self.finish_date_time_layout = QHBoxLayout()
        self.finish_date_time_layout.addWidget(self.finish_date)
        self.finish_date_time_layout.addWidget(self.finish_time)

        self.full_date_time_layout.addLayout(self.begin_label_layout)
        self.full_date_time_layout.addLayout(self.begin_date_time_layout)
        self.full_date_time_layout.addLayout(self.finish_label_layout)
        self.full_date_time_layout.addLayout(self.finish_date_time_layout)
        self.full_date_time_layout.setContentsMargins(0, 320, 0, 320)

        # layout główny
        self.start_layout = QHBoxLayout()
        self.start_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.start_layout.addLayout(self.full_date_time_layout)
        self.setLayout(self.start_layout)

    # funkcja pobierająca dane
    def get_data(self):

        if self.begin_date.date() > self.finish_date.date() or \
                (self.begin_date.date() == self.finish_date.date() and
                 self.begin_time.date() >= self.finish_time.date()):
            print("error")                      # jeśli podany jest zły przedział czasowy - komunikat o błędzie

        else:
            self.tasks_obtained = get_tasks_from_calendar()
            # w przeciwnym wypadku wywoływanie właściwej funkcji pobierającej dane


class AddDataTab(QWidget):

    def __init__(self):

        super(QWidget, self).__init__()

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
