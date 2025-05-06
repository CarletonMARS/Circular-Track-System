#!/usr/bin/python3

# TODO: build a log file to store all the text printed in the console
# TODO: build a splash screen with a text to enter the com port number (can also be empty)
# TODO: use fbs to build the app (https://github.com/ghassanarnouk/fbs-tutorial)

from ctypes import alignment
import sys
import os
import webbrowser
import threading
import time
import hashlib
import csv
# from console_interface import *   # TODO: uncomment the following line when the console_interface.py is ready (in the lab)
from PyQt5 import QtCore
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon, QKeySequence, QFont
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication, QMessageBox, QPushButton, QMainWindow, QMenu, QAction, QTextBrowser, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QRadioButton, QTabWidget, QHBoxLayout, QSlider, QCheckBox, QComboBox, QLCDNumber, QFrame, QSizePolicy, QSpinBox, QDoubleSpinBox, QFormLayout, QTableWidget, QTableWidgetItem
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import random

# CONSTANTS Declaration
START_END_FREQ_DIFF = 0.05      # freq diff value in GHz
MAX_ANGLE_ROTATE = 50           # angle value in degrees

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    # Launch GUI in mid screen
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # Pop-up confirmation window when quitting
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure you want to quit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # External help
    def showExternalHelp(self):
        # LaTeX-to-HTML command: $ make4ht file.tex "mathjax"
        filePath = os.path.join(os.getcwd(), '../report/main.html')
        webbrowser.open_new_tab('file://' + filePath)

    # Version number dialog
    def aboutDialog(self):
        _aboutDialog = QMessageBox()
        _aboutDialog.setText("Version: TBU")    # TODO: change the version number when ready to release
        _aboutDialog.setWindowTitle('Version & revision numbers')
        _aboutDialog.setIcon(QMessageBox.Information)
        _aboutDialog.setStandardButtons(QMessageBox.Ok)
        _aboutDialog.exec_()

    # Show authors dialog
    def showAuthors(self):
        _showAuthors = QMessageBox()
        _showAuthors.setText("Author(s) & Contributor(s):\n\nGhassan Arnouk\nDavid Song\n\nKeigan Macdonell\nDr. S. Gupta")
        _showAuthors.setWindowTitle('Author(s)')
        _showAuthors.setIcon(QMessageBox.Information)
        _showAuthors.setStandardButtons(QMessageBox.Ok)
        _showAuthors.exec_()

    # Tooltips
    def toolTip(self):
        # self.angleSlider.setToolTip('Angle must be an integer between 1 and ' + str(MAX_ANGLE_ROTATE) + ' degrees.')
        self.lcd.setToolTip('Rotation angle must be an integer between 1 and ' + str(MAX_ANGLE_ROTATE) + ' degrees.')   # TODO: the angle is not updated when the text box angle value is changed
        self.startAngle_box.setToolTip('Start angle must be a positive integer.')
        self.endAngle_box.setToolTip('End angle must be a positive integer greater than start angle.')
        self.stepSize_box.setToolTip('Step size must be a float greater than or equal to 0.5.')
        # self.power_box.setToolTip('Power must be a number between -80 dBm and +5 dBm.')
        # self.startFreq_box.setToolTip('Start frequency must be a number between 50 MHz and 19.95 GHz (Enter number in GHz).')
        # self.endFreq_box.setToolTip('End frequency must be a number greater than start frequency by 50 MHz (Enter number in GHz).')
        # self.numOfPoints_box.setToolTip('Number of points must be an integer between 101 and 1601.')

    # Update slider maximum value
    def updateSliderLimits(self):
        newMaxAngle_number = int(self.maxAngle_box.value())
        self.angleSlider.setMaximum(newMaxAngle_number)     # update the upper limit
        self.angleSlider.setMinimum(-newMaxAngle_number)    # update the lower limit

    # Start frequency decimals
    def updateStartFreqDecimals(self, value):
        if value == int(value):
            self.startFreq_box.setDecimals(0)
        else:
            self.startFreq_box.setDecimals(2)

    # End frequency decimals
    def updateEndFreqDecimals(self, value):
        if value == int(value):
            self.endFreq_box.setDecimals(0)
        else:
            self.endFreq_box.setDecimals(2)

    # Step size decimals
    def updateStepSizeDecimals(self, value):
        if value == int(value):
            self.stepSize_box.setDecimals(0)
        else:
            self.stepSize_box.setDecimals(2)

    # Run ctrack rotate command
    def run_rotate (self):
        slider_value = self.angleSlider.value()
        # print(sliderValue)
        if slider_value < 0:
            rotation_dir = 'l'
            arm_travel(abs(slider_value), rotation_dir)
            # print(str(abs(slider_value)) + ' ' + rotation_dir)
        if slider_value > 0:
            rotation_dir = 'r'
            arm_travel(slider_value, rotation_dir)
            # print(str(slider_value) + ' ' + rotation_dir)

    # Control tab
    def positionerTabUI(self):
        positionerTabLayout = QFormLayout()             # Positioner tab = QFormLayout()
        self.tab1.setLayout(positionerTabLayout)
        # UI elements declaration
        self.maxAngle_box = QSpinBox()                  # max angle box
        self.maxAngle_box.setMinimum(1)
        self.maxAngle_box.setValue(MAX_ANGLE_ROTATE)
        self.maxAngle_box.setSingleStep(5)
        self.maxAngle_box.setSuffix("  degree(s)")
        self.startAngle_box = QSpinBox()                # start angle box
        self.startAngle_box.setRange(-70, 70)
        self.startAngle_box.setValue(-1)
        self.startAngle_box.setSuffix("  degree(s)")
        self.endAngle_box = QSpinBox()                  # end angle box
        self.endAngle_box.setRange(-70, 70)
        self.endAngle_box.setValue(1)
        self.endAngle_box.setSuffix("  degree(s)")
        self.stepSize_box = QDoubleSpinBox()            # step size box
        self.stepSize_box.setMinimum(0.5)
        self.stepSize_box.setValue(0.5)
        # self.stepSize_box.setDecimals(2)
        self.stepSize_box.setSingleStep(0.5)
        # self.stepSize_box.valueChanged.connect(self.updateStepSizeDecimals)
        self.refValue_box = QDoubleSpinBox()            # reference value box
        self.refValue_box.setRange(-70, 70)
        self.refValue_box.setValue(0)
        self.refValue_box.setSuffix("  dB")
        self.refValue_box.setSingleStep(1)
        self.lcd = QLCDNumber()                                                     # lcd display
        self.angleSlider = QSlider(Qt.Horizontal)                                   # angle slider
        self.angleSlider.valueChanged.connect(self.lcd.display)
        self.angleSlider.setMinimum(-MAX_ANGLE_ROTATE)
        self.angleSlider.setMaximum(MAX_ANGLE_ROTATE)
        self.angleSlider.setValue(0)
        self.angleSlider.setTickPosition(QSlider.TicksBelow)
        self.angleSlider.setTickInterval(5)
        self.maxAngle_box.textChanged.connect(self.updateSliderLimits)              # max angle dynamic value change
        self.rotateBtn = QPushButton('Rotate')                                      # rotate button
        self.rotateBtn.clicked.connect(self.run_rotate)
        self.positionerController = QLabel("<b>Positioning Controller<b>")          # section label
        self.angleSweep = QLabel("<b>Angle Sweep<b>")                               # section label
        # UI grid positionerTabLayout assignment
        positionerTabLayout.addRow(self.positionerController)
        positionerTabLayout.addRow("Max. Angle:", self.maxAngle_box)
        positionerTabLayout.addRow(self.lcd)
        positionerTabLayout.addRow(self.angleSlider)
        positionerTabLayout.addRow(self.rotateBtn)
        positionerTabLayout.addRow(self.angleSweep, self.startAngle_box)
        positionerTabLayout.addRow("Start Angle:", self.startAngle_box)
        positionerTabLayout.addRow("End Angle:", self.endAngle_box)
        positionerTabLayout.addRow("Step Size:", self.stepSize_box)
        positionerTabLayout.addRow("Ref. Value:", self.refValue_box)

    # VNA Control tab
    def vnaControlTabUI(self):
        vnaTabLayout = QFormLayout()                                                # VNA Control tab = QFormLayout
        self.tab2.setLayout(vnaTabLayout)
        # UI elements declaration
        self.checkBS11 = QCheckBox('S(1,1)')                                        # S Parameters
        self.checkBS12 = QCheckBox('S(1,2)')
        self.checkBS21 = QCheckBox('S(2,1)')
        self.checkBS22 = QCheckBox('S(2,2)')
        self.checkBS11.setChecked(True)                                             # All S parameters are enabled by default
        self.checkBS12.setChecked(True)
        self.checkBS21.setChecked(True)
        self.checkBS22.setChecked(True)
        self.setifbw_dropdown = QComboBox()                                         # IF Bandwidth frequencies
        self.setifbw_dropdown.addItem('  10 Hz')
        self.setifbw_dropdown.addItem('  30 Hz')
        self.setifbw_dropdown.addItem('100 Hz')
        self.setifbw_dropdown.addItem('300 Hz')
        self.setifbw_dropdown.addItem('  1 kHz')
        self.setifbw_dropdown.addItem('  3 kHz')
        self.setifbw_dropdown.addItem('  6 kHz')
        self.setifbw_dropdown.setCurrentText('  1 kHz')
        self.power_box = QSpinBox()                                                 # power in dBm
        self.power_box.setRange(-80, 5)
        self.power_box.setValue(-10)
        self.power_box.setSuffix(" dBm")
        self.startFreq_box = QDoubleSpinBox()                                       # start frequency
        self.startFreq_box.setRange(0.05, 20)
        self.startFreq_box.setValue(7)
        self.startFreq_box.setSingleStep(0.1)
        self.startFreq_box.setSuffix(" GHz")
        self.endFreq_box = QDoubleSpinBox()                                         # end frequency
        self.endFreq_box.setRange(0.05, 20)
        self.endFreq_box.setValue(13)
        self.endFreq_box.setSingleStep(0.1)
        self.endFreq_box.setSuffix(" GHz")
        self.numOfPoints_box = QSpinBox()                                           # number of points
        self.numOfPoints_box.setRange(101, 1601)
        self.numOfPoints_box.setValue(1601)
        self.magnitude_box = QCheckBox('Magnitude')                                 # Components: Magnitude n Phase
        self.phase_box = QCheckBox('Phase')
        self.magnitude_box.setChecked(True)
        self.phase_box.setChecked(True)
        # UI grid vnaTabLayout assignment
        vnaTabLayout.addRow("Choose S Parameter(s):", self.checkBS11)
        vnaTabLayout.addRow(self.checkBS11, self.checkBS12)
        vnaTabLayout.addRow(self.checkBS21, self.checkBS22)
        vnaTabLayout.addRow("IF Bandwidth Frequency:", self.setifbw_dropdown)
        vnaTabLayout.addRow("Power:", self.power_box)
        vnaTabLayout.addRow("Start Frequency:", self.startFreq_box)
        vnaTabLayout.addRow("End Frequency:", self.endFreq_box)
        vnaTabLayout.addRow("Number of points:", self.numOfPoints_box)
        vnaTabLayout.addRow("Choose Component(s) Form:", self.magnitude_box)
        vnaTabLayout.addRow(self.magnitude_box, self.phase_box)

    # Data tab
    def dataTabUI(self):
        dataTabLayout = QVBoxLayout()
        self.tab3.setLayout(dataTabLayout)
        self.tableWidget = QTableWidget()
        if os.path.getsize('data.csv') == 0:
            noDataLabel = QLabel("No data available")
            dataTabLayout.addWidget(noDataLabel)
            return
        with open('data.csv', 'r') as file:
            csv_data = csv.reader(file)
            for i, row in enumerate(csv_data):
                if i == 0:  # The first row is the header
                    self.tableWidget.setColumnCount(len(row))  # Set column count
                    self.tableWidget.setHorizontalHeaderLabels(row)  # Set header labels
                else:
                    self.tableWidget.insertRow(self.tableWidget.rowCount())  # Insert a row
                    for j, cell in enumerate(row):
                        self.tableWidget.setItem(i-1, j, QTableWidgetItem(cell))  # Set item
        dataTabLayout.addWidget(self.tableWidget)

    # Abort status
    def abort_status(self):
        self.abortEnable = True

    # Action of running the `Run` button
    def run_action(self):
        startAngle_value = self.startAngle_box.value()
        endAngle_value = self.endAngle_box.value()
        stepSize_value = self.stepSize_box.value()
        reference_value = self.refValue_box.value()
        filePath = os.path.join(os.getcwd(), '')
        if startAngle_value < endAngle_value:
            angle = startAngle_value
            while angle <= endAngle_value:
                # check if Abort is pressed
                if self.abortEnable == True:
                    self.abortEnable = False
                    break
                os.system("ctrack fsweepaps -a {} -p . -c {}".format(angle, reference_value))
                rotation_dir = 'r'
                os.system("ctrack rotate -d {} {}".format(stepSize_value, rotation_dir))
                angle += stepSize_value     # increment the counter
        elif startAngle_value > endAngle_value:
            angle = startAngle_value
            while angle >= endAngle_value:
                # check if Abort is pressed
                if self.abortEnable == True:
                    self.abortEnable = False
                    break
                os.system("ctrack fsweepaps -a {} -p . -c {}".format(angle, reference_value))
                rotation_dir = 'l'
                os.system("ctrack rotate -d {} {}".format(stepSize_value, rotation_dir))
                angle -= stepSize_value     # decrement the counter
        # measure_angle((startAngle_value,endAngle_value), stepSize_value, filePath, NAME)

    # Actual plotting of data
    def plot(self):
        csv_file = 'data.csv'
        self.figure.clear()                     # Clearing old figure
        ax = self.figure.add_subplot(111)       # Create an axis
        # Read data from the CSV file
        datax = []
        datay = []
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                # Assuming the data is in the first column of each row
                datax.append(float(row[0]))
                datay.append(float(row[1]))
            file.close()
        ax.plot(datax, datay)   # Plot data
        self.canvas.draw()      # Refresh canvas

    # Calculate the hash of the file content
    def calculate_file_hash(self, filename):
        with open(filename, 'rb') as file:
            content = file.read()
            return hashlib.md5(content).hexdigest()

    # Check if the file content has changed
    def has_file_changed(self, filename, previous_hash):
        current_hash = self.calculate_file_hash(filename)
        return current_hash != previous_hash

    def process_data(self):
        # Store the hash of the initial file content
        previous_hash = self.calculate_file_hash('data.csv')
        while self.running:
            if self.has_file_changed('data.csv', previous_hash):
                with open('data.csv', 'r') as file:
                    reader = csv.reader(file)
                    # Skip rows that have already been processed
                    for _ in range(len(self.x)):
                        next(reader)
                    for row in reader:
                        x_value = float(row[0])
                        y_value = float(row[1])
                        self.x.append(x_value)
                        self.y.append(y_value)
                        # print(self.x, self.y)
                previous_hash = self.calculate_file_hash('data.csv')
            time.sleep(0.5)  # Simulate data processing time

    def runThreaded(self):
        self.runThread = threading.Thread(target=self.run_action)
        self.runThread.daemon = True
        self.runThread.start()

    def update_gui(self):
        while self.running:
            self.ax.clear()
            self.ax.plot(self.x, self.y, 'b-')
            self.canvas.draw()
            time.sleep(0.5)  # Update plot every 0.5 seconds

    def closeEventThread(self, event):
        self.running = False
        self.data_thread.join()
        self.gui_thread.join()
        self.runThread.join()
        super().closeEvent(event)

    # UI main declaration func
    def initUI(self):
        # Define a window widget to potentially contain the 2 frames
        window = QWidget()
        # Widget of frame #2
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.figure.add_subplot(111)
        self.x = []
        self.y = []
        self.running = True
        # Start data processing thread
        self.data_thread = threading.Thread(target=self.process_data)
        self.data_thread.daemon = True
        self.data_thread.start()
        # Start GUI update thread
        self.gui_thread = threading.Thread(target=self.update_gui)
        self.gui_thread.daemon = True
        self.gui_thread.start()
        self.button = QPushButton('Interact')
        self.button.clicked.connect(self.plot)
        # Widget of frame #1. Declaring 3 tabs as widgets
        tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        tabs.addTab(self.tab1, "Positioner")        # adding each individual tab created to the tabs widget
        tabs.addTab(self.tab2, "VNA Control")
        tabs.addTab(self.tab3, "Data")
        tabs.addTab(self.tab4, "Routines")
        # Run & Abort buttons
        self.abortBtn = QPushButton('Abort')
        self.runBtn = QPushButton('Run')
        # Linking the Run button to a method
        self.runBtn.clicked.connect(self.runThreaded)
        self.abortEnable = False
        self.abortBtn.clicked.connect(self.abort_status)
        # Defining layout for buttons
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.runBtn)
        btn_layout.addWidget(QLabel())
        btn_layout.addWidget(self.abortBtn)
        # creating two new frames
        frame1 = QFrame()                       # defining new frame 1 out of 2
        frame1_layout = QFormLayout()
        frame1.setLayout(frame1_layout)
        frame1_layout.addRow(tabs)
        frame1_layout.addRow(btn_layout)
        frame2 = QFrame()                       # defining new frame 2 out of 2
        frame2_layout = QVBoxLayout()
        frame2.setLayout(frame2_layout)
        frame2_layout.addWidget(self.toolbar)
        frame2_layout.addWidget(self.canvas)
        frame2_layout.addWidget(self.button)
        parent_layout = QHBoxLayout()           # Creating the parent layout to contain the 2 frames
        parent_layout.addWidget(frame1)
        parent_layout.addWidget(frame2)
        window.setLayout(parent_layout)         # adding the parent layout to the window widget (containing the 2 frames)
        self.setCentralWidget(window)           # setting the central widget of the main window to the window widget
        self.positionerTabUI()                  # setting the individual tabs
        self.vnaControlTabUI()
        self.dataTabUI()
        # Menu bar
        menubar = self.menuBar()
        # File menu
        fileMenu = menubar.addMenu('File')
        closeWindow = QAction('Close Window...', self)
        closeWindow.triggered.connect(self.close)
        # Help menu
        helpMenu = menubar.addMenu('Help')
        authors = QAction('Author(s)...', self)
        authors.triggered.connect(self.showAuthors)
        version = QAction('Version...', self)
        version.triggered.connect(self.aboutDialog)
        externalHelp = QAction('External help', self)
        externalHelp.triggered.connect(self.showExternalHelp)
        # Order of showing the menus
        # File menu
        fileMenu.addAction(closeWindow)
        # Help menu
        helpMenu.addAction(version)
        helpMenu.addAction(authors)
        helpMenu.addAction(externalHelp)
        # Tooltips
        self.toolTip()  # TODO: create a new item with a question mark icon or i icon and attach the tooltip to it
        # Keyboard shortcuts
        closeWindow.setShortcut("Ctrl+Q")
        # GUI window properties
        # self.setFixedWidth(1100)      # Fixed dimensions
        # self.setFixedHeight(550)      # Fixed dimensions
        self.resize(1100, 550)      # Resizable dimensions
        self.setWindowIcon(QIcon('rf.png'))
        self.center()
        self.setWindowTitle('Operations Manager')
        self.show()
        self.statusBar().showMessage('Ready')
        # self.setStyleSheet('background-color: #1f1b24;')

def main():
    app = QApplication(sys.argv)
    # app.setStyle('Fusion')
    app.setStyle('Macintosh')
    # TODO: change the background color of the buttons when pressed (NOT GREY)
    # Change the background color of the buttons when pressed
    # app.setStyleSheet("""
    #     QPushButton:pressed {
    #         background-color: #808080;
    #     }
    # """)
    gui = GUI()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()