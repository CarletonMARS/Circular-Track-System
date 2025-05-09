#!/usr/bin/python3

import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtGui
from PyQt5.QtGui import QIcon

class Example(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Icon')
        # line below NOT WORKING
        self.setWindowIcon(QIcon('./dummy.png')) 
        self.show()

def main():
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
