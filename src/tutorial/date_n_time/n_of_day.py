#!/usr/bin/python3

from PyQt5.QtCore import QDate, Qt

now = QDate.currentDate()

d = QDate(2023, 2, 19)

print(f"Days in month: {d.daysInMonth()}")
print(f'Days in year: {d.daysInYear()}')
