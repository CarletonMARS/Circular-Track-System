#!/usr/bin/python3

import sys
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QMessageBox

class Example(QWidget):
    # Constructor to initialize
    def __init__(self):
        super().__init__()

        self.initUI()

    # Pop-up confirmation window when quitting
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure you want to quit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # Quit button
    def initUI(self):
        qbtn = QPushButton('Quit', self)
        qbtn.clicked.connect(self.close)
        qbtn.resize(qbtn.sizeHint())
        qbtn.move(50, 50)

        self.setGeometry(300, 300, 350, 250)
        self.setWindowTitle('Quit button')
        self.show()

def main():
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
