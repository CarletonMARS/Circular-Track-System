from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QTabWidget
from PyQt5.QtCore import Qt

app = QApplication([])
window = QWidget()


tabs1 = QTabWidget()
tabs2 = QTabWidget()

tab1 = QWidget()
tab2 = QWidget()
tab3 = QWidget()
tab4 = QWidget()

tabs1.addTab(tab1, "Tab 1")
tabs1.addTab(tab2, "Tab 2")
tabs2.addTab(tab3, "Tab 3")
tabs2.addTab(tab4, "Tab 4")



frame1 = QFrame()
frame1_layout = QHBoxLayout()
frame1.setLayout(frame1_layout)
frame1_layout.addWidget(tabs1)

frame2 = QFrame()
frame2_layout = QHBoxLayout()
frame2.setLayout(frame2_layout)
frame2_layout.addWidget(tabs2)

parent_layout = QHBoxLayout()
parent_layout.addWidget(frame1)
parent_layout.addWidget(frame2)



button1 = QPushButton('Click me 1')
button2 = QPushButton('Click me 2')
button3 = QPushButton('Click me 3')
button4 = QPushButton('Click me 4')


tab1Layout = QHBoxLayout()
tab1.setLayout(tab1Layout)
tab1Layout.addWidget(button1)


tab2Layout = QHBoxLayout()
tab2.setLayout(tab2Layout)
tab2Layout.addWidget(button2)


tab3Layout = QHBoxLayout()
tab3.setLayout(tab3Layout)
tab3Layout.addWidget(button3)


tab4Layout = QHBoxLayout()
tab4.setLayout(tab4Layout)
tab4Layout.addWidget(button4)


window.setLayout(parent_layout)
window.show()

app.exec_()
