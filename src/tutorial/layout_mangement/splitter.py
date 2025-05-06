#!/usr/bin/python

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSplitter, QApplication, QTabWidget, QLabel, QGridLayout)

class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):

        # defining the main layout
        hbox = QHBoxLayout(self)

        # creating the frames n splitters
        topleft = QFrame(self)
        topleft.setFrameShape(QFrame.StyledPanel)

        topright = QFrame(self)
        topright.setFrameShape(QFrame.StyledPanel)

        # creating tabs
        tabs = QTabWidget()

        tab1 = QWidget()
        tab2 = QWidget()

        tabs.addTab(tab1, "Positioner")
        tabs.addTab(tab2, "Routines")



        splitter1 = QSplitter(Qt.Horizontal)
        splitter1.addWidget(topleft)
        splitter1.addWidget(topright)

        hbox.addWidget(splitter1)
        self.setLayout(hbox)

        



        self.setWindowTitle('QSplitter')
        self.show()


def main():
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
