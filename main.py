import sys
import gui
from PyQt6.QtWidgets import QApplication


def main():

    app = QApplication(sys.argv)

    window = gui.StartWindow()
    window.show()

    app.exec()


if __name__ == '__main__':
    main()
