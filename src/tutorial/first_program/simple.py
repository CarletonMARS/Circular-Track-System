#!/usr/bin/python3

import sys
from PyQt5.QtWidgets import QApplication, QWidget

def main():
    # Qt requirement
    # Every gui application must have one instance of QApplication
    app = QApplication(sys.argv)

    window = QWidget()  # initializing
    window.resize(250, 150)
    window.move(300, 300)
    window.setWindowTitle('Simple')
    window.show()   # displaying

    # exec_ has an undersocre since exec is a python keyword. Thus, exec_ is used instead
    sys.exit(app.exec_())   # ensures a clean exit


if __name__ == "__main__":
    main()
