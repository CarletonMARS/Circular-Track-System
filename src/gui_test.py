#todo:
#get general layout complete
#setup debug listeners on the buttons, at least be able to move stage left, right and take manual measurements
import PySimpleGUI as sg
import time

import console_interface as ci

col0 = [[sg.Text('Arm movment')],
        [sg.Text('degrees'),sg.I()],
        [sg.Button('<- Left'),sg.Button('Right ->')]]

col1 = [[sg.Text('Sweep Start Angle')],
        [sg.Text('Sweep End Angle')],
        [sg.Text('Step Size')]]

col2 = [[sg.Input()],
        [sg.Input()],
        [sg.Input()]]

col3 = [[sg.Text('Start F (GHz)')],
        [sg.Text('Stop F (GHz')],
        [sg.Text('Power (dB')], 
        [sg.Button('Set')]]

col4 = [[sg.Input()],
        [sg.Input()],
        [sg.Input()],
        [sg.Button('default')]]

    
layout = [[col0],
          [sg.HorizontalSeparator()],
          [sg.Column(col1),sg.Column(col2),sg.VerticalSeparator(),sg.Column(col3),sg.Column(col4)],
          [sg.HorizontalSeparator()],
          [sg.Text('Save Location'),sg.InputText(),sg.FolderBrowse()],
          [sg.Text('Sweep Name '),sg.Input()],
          [sg.Button('Start Sweep'),sg.Button('Reset')]]

window = sg.Window('Circular Track Control',layout,element_justification='left')

right = window['Right ->']
left = window['<- Left']
start_swp = window['Start Sweep']

while (True):
    event,values = window.read(timeout=500)
    
    if event == sg.WIN_CLOSED or event ==  'Exit':
        break
    if event == 'Set':
        ci.set_power(values[8])
        ci.set_sweepGHz(int(values[6]),int(values[7]),1601)
    if event == 'Start Sweep':
        if values[7] != '':
                ci.measure_angle({values[2],values[3]},values[4],values[10],values[11])
        else:
                ci.measure_angle({values[2],values[3]},values[4],'',values[11])
    if event == '<- Left':
        ci.arm_travel(int(values[0]),'l')
    if event == 'Right ->':
        ci.arm_travel(int(values[0]),'r')   
    if event == 'Reset':
        print(event,values)
    
    time.sleep(0.5)

window.close()