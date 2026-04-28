import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from data.db import DB_PATH


def main() -> None:
    app = QApplication(sys.argv)

    if not DB_PATH.exists():
        QMessageBox.critical(
            None,
            "Database Missing",
            f"Question database not found at:\n{DB_PATH}\n\n"
            "Run:  python data/seed/seeder.py",
        )
        sys.exit(1)

    from ui.main_window import MainWindow  # import after QApplication exists

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
