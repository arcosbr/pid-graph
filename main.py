# main.py

import sys
from PyQt6.QtWidgets import QApplication
from window import DarkModeWindow


def main() -> None:
    """
    Main function to run the PID controller application.
    """
    app = QApplication(sys.argv)
    window = DarkModeWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
