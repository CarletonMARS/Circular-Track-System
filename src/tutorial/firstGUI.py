import sys
import logging
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget)

# Configure the logging module 
logging.basicConfig(filename='gui.log', level=logging.DEBUG)

# Redirect stdout and stderr to the log file
sys.stdout = sys.stderr = open('gui.log', 'a') # 'a' for appending


# Qt requirement
# Every GUI app must have exactly one instance of QApplication
app = QApplication([sys.argv])

#label = QLabel('Hello World')
#label.show()

# Create a window
window = QWidget()

# Create a label and set its text
label = QLabel(window)
label.setText('Hello world!')
label.move(200, 200)

window.setWindowTitle('My App')
window.setGeometry(200, 200, 200, 100)
window.show()

sys.exit(app.exec_())





#app.exec()

