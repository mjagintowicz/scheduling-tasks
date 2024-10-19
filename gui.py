from PyQt6.QtWidgets import QMainWindow, QPushButton, QHBoxLayout, QWidget, QDateEdit, QVBoxLayout, QLabel, QTimeEdit
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont

# OKNO STARTOWE


class StartWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        # tytuł okna
        self.setWindowTitle('Optymalizacja harmonogramu')

        # rozmiar okna
        self.setFixedSize(1500, 850)

        # centralny widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # przycisk startowy
        start_button = QPushButton('Pobierz listę zadań\nz kalendarza', self)
        start_button.setFixedSize(400, 200)
        start_button.setFont(QFont('Calibri', 25))

        # wybór dat
        begin_date = QDateEdit()
        begin_date.setCalendarPopup(True)
        begin_date.setDate(QDate.currentDate())     # domyślnie dziś
        begin_date.setFixedSize(100, 50)

        finish_date = QDateEdit()
        finish_date.setCalendarPopup(True)
        finish_date.setDate(QDate.currentDate().addDays(14))        # domyślnie koniec po 2 tygodniach
        finish_date.setFixedSize(100, 50)

        # wybór godzin
        begin_time = QTimeEdit()
        begin_time.setTime(QTime.currentTime())
        begin_time.setFixedSize(100, 50)

        finish_time = QTimeEdit()
        finish_time.setTime(QTime.currentTime())
        finish_time.setFixedSize(100, 50)

        # etykiety
        begin_label = QLabel('Początek harmonogramu:')
        begin_label.setFixedSize(200, 20)

        finish_label = QLabel('Koniec harmonogramu:')
        finish_label.setFixedSize(200, 20)

        # layout na informacje o dacie i godzinie
        full_date_time_layout = QVBoxLayout()

        # w nim mniejsze layouty
        # 1. - etykieta
        begin_label_layout = QHBoxLayout()
        begin_label_layout.addWidget(begin_label)

        # 2. - data i godzina początku
        begin_date_time_layout = QHBoxLayout()
        begin_date_time_layout.addWidget(begin_date)
        begin_date_time_layout.addWidget(begin_time)

        # 3. - etykieta
        finish_label_layout = QHBoxLayout()
        finish_label_layout.addWidget(finish_label)

        # 4. - data i godzina końca
        finish_date_time_layout = QHBoxLayout()
        finish_date_time_layout.addWidget(finish_date)
        finish_date_time_layout.addWidget(finish_time)

        full_date_time_layout.addLayout(begin_label_layout)
        full_date_time_layout.addLayout(begin_date_time_layout)
        full_date_time_layout.addLayout(finish_label_layout)
        full_date_time_layout.addLayout(finish_date_time_layout)
        full_date_time_layout.setContentsMargins(0, 320, 0, 320)

        # layout główny
        start_layout = QHBoxLayout()
        start_layout.addWidget(start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        start_layout.addLayout(full_date_time_layout)
        central_widget.setLayout(start_layout)
