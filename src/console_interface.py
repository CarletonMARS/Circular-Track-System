from rotary_stage import rotaryStage
from vna import VNA, FreqSweepParams
from NI_pxie import voltageSetter

import click
import time
import sys
from pathlib import Path
import os
import numpy as np
from datetime import date
import re
import csv
import math

# 5/26/2023
# from matPlotLibWrapper import realTimePlot

COM_PORT = 'COM7'
CAL_STEP = 800

DBM_0V = 16.82
MV_DBM_SLOPE = 0.0220
MIN_INPUT = -60
MAX_INPUT = -70

def save_to_csv(pwr,angle,fpth):
    #if file does not exist, create it, and the open and write the data point to it at the specified angle
    with open(os.path.join(fpth,"data.csv"), 'a', newline='',  encoding='utf-8') as f:
        csv_writer = csv.writer(f)
        data = [pwr,angle]
        csv_writer.writerow(data)
        #np.savetxt(f, np.array(data),delimiter=',')
        f.close()

def make_new_dir(name):
    new_folder = date.today().strftime('%b_%d_%Y')
    p = Path('./cli_measurement/' + new_folder)

    p.mkdir(exist_ok=True)

    dirlist = os.listdir('./cli_measurement/'+new_folder+'/')
    temp = [0]
    for foldername in dirlist:
        tag = foldername[-1]
        if tag.isdigit():
            temp.append(int(tag))
    maxfolder = max(temp)+1
    
    if name == None:
        sweepname = 'measurement_' + str(maxfolder)
    elif re.match('^[\w-]*$', name):
        sweepname = 'measurement_' +name +'_'+ str(maxfolder)
    else:
        print("invalid file naming, use only letter, number dash or underscore, defaulting to standard convention (<name>_measurement)")
        sweepname = 'measurement_' + str(maxfolder)

    p = p / sweepname
    p.mkdir()
    return p

def arm_travel(degrees,dirn):
    s = rotaryStage(COM_PORT)
    time.sleep(2)

    if dirn == 'l':
        print(s.step_cw(degrees))
    elif dirn == 'r':
        print(s.step_ccw(degrees))
    else:
        print("l: cw rotation\nr: ccw rotation")
        
    time.sleep(1)
    s.disconnect()
    
def arm_home():
    s = rotaryStage(COM_PORT)
    time.sleep(2)
    
    s.reset_stage()
    
def get_sweep():
    v = VNA(False)
    v.connect(16)
    sweep_param = v.get_sweep_params()
    return sweep_param

def set_sweepGHz(freq_start,freq_stop,points):
    v = VNA(False)
    v.connect(16)
    current_params = v.get_sweep_params()
    sp = FreqSweepParams(freq_start*10.0E8,freq_stop*10.0E8,points,current_params.power,current_params.averaging,current_params.sparams)
    v.set_sweep_params(sp)
    
def set_power(power):
    v = VNA(False)
    v.connect(16)
    current_params = v.get_sweep_params()
    sp = FreqSweepParams(current_params.start,current_params.stop,current_params.points,float(power),current_params.averaging,current_params.sparams)
    v.set_sweep_params(sp)
    
def display_4():
    v = VNA(False)
    v.connect(16)
    v.display_4_channels()
    
def s_param_selection():
    pass
        
def measure_angle(angleswp,step,savepath,name):
    dirn = 0
    count = 0
    
    #temporary, need to fix
    #Freq = np.linspace(6, 13, 1601)
    
    s = rotaryStage(COM_PORT)
    v = VNA(False)
    v.connect(16)
    
    cparam = v.get_sweep_params()
    start = cparam.start
    end = cparam.stop
    pts = cparam.points
    Freq = np.linspace((start/10**9),(end/10**9),pts)
    
    s_angle,e_angle = angleswp
    
    #will make a new dir with current date, but if already exists, will make a new folder inside numbered sequentially with an optional name
    if savepath == None:
        p = make_new_dir(name)
        
    else:
        p = savepath
    
    # 2/05/2023 -- Function can take any step size - direction of angle sweep is now dependent on relation between start and end angle.
    step = abs(step)
    if step > abs(s_angle - e_angle):
        step = s_angle - e_angle
    elif s_angle - e_angle > 0:
        step = -step
    
    if s_angle > e_angle:
        dirn = 1
    elif s_angle < e_angle:
        dirn = 2
    else:
        print('angle values are incompatible')
        sys.exit()
    # print(dirn)
    # print(s_angle)
    # print(e_angle)
    # print(step)
    
    time.sleep(1)
    
    v.display_4_channels()
    
    Angle = (s_angle+step*count)
    v.WriteData(str(p) + '/', str(Angle), Freq)
    
    for Angle in range(2*s_angle, 2*e_angle, int(2*step)):
        
        count = count + 1
        
        if dirn == 1:
            s.step_cw(abs(step))
        elif dirn == 2 :
            s.step_ccw(abs(step))
        else:
            print('angle values are incompatible')
            sys.exit()
        
        time.sleep(8)
        
        Angle = (s_angle+step*count)
        v.WriteData(str(p) + '/', str(Angle), Freq)
    
    print(f'completed sweep for: {count} data points')
    s.disconnect()

def measure_angle_aps(angleswp,step,savepath,name):
    dirn = 0
    count = 0
    
    #temporary, need to fix
    #Freq = np.linspace(6, 13, 1601)
    
    s = rotaryStage(COM_PORT)
    #v = VNA(False)
    #v.connect(16)
    
    #cparam = v.get_sweep_params()
    #start = cparam.start
    #end = cparam.stop
    #pts = cparam.points
    # Freq = np.linspace(int(start/10**9),int(end/10**9),pts)
    #Freq = np.linspace((start/10**9),(end/10**9),pts)
    
    s_angle,e_angle = angleswp
    
    # #will make a new dir with current date, but if already exists, will make a new folder inside numbered sequentially with an optional name
    if savepath == None:
        p = make_new_dir(name)
        
    else:
        p = savepath
    
    # 2/05/2023 -- Function can take any step size - direction of angle sweep is now dependent on relation between start and end angle.
    step = abs(step)
    if step > abs(s_angle - e_angle):
        step = s_angle - e_angle
    elif s_angle - e_angle > 0:
        step = -step
    
    if s_angle > e_angle:
        dirn = 1
    elif s_angle < e_angle:
        dirn = 2
    else:
        print('angle values are incompatible')
        sys.exit(1)
    # print(dirn)
    # print(s_angle)
    # print(e_angle)
    # print(step)
    time.sleep(1)
    
    #v.display_4_channels()
    
    Angle = (s_angle+step*count)
    pwr_v = s.read_msg()
    
    if pwr_v == '':
        sleep(0.5)
        pwr_v = s.read_msg()
        
    # Plot the first value
    rtp = realTimePlot(name)
    rtp.generatePlot(s_angle,e_angle)
    rtp.updatePlot(Angle,float(pwr_v))
        
    # #normalized = DBM_0V - (float(pwr_v)/MV_DBM_SLOPE)
    # #pwr_db = 10 * math.log(normalized,10)
    save_to_csv(Angle, float(pwr_v), p)
    # #v.WriteData(str(p) + '/', str(Angle), Freq)
    
    
    for Angle in range(2*s_angle, 2*e_angle, int(2*step)):
        
        count = count + 1
        
        if dirn == 1:
            s.step_cw(abs(step))
        elif dirn == 2 :
            s.step_ccw(abs(step))
        else:
            print('angle values are incompatible')
            sys.exit()
        
        time.sleep(8)
        Angle = (s_angle+step*count)
        pwr_v = s.read_msg()
        
        if pwr_v == '':
            time.sleep(0.5)
            pwr_v = s.read_msg()
      
        # #normalized = DBM_0V - (float(pwr_v)/MV_DBM_SLOPE)
        # #pwr_db = 10 * math.log(normalized,10)
        save_to_csv(Angle, float(pwr_v), p)
        # #v.WriteData(str(p) + '/', str(Angle), Freq)
        
        rtp.updatePlot(Angle,float(pwr_v))
    
    print(f'completed sweep for: {count} data points')
    s.disconnect()
    
def measure_fixed_angle(Angle, savepath, name):
    v = VNA(False)
    v.connect(16)
    
    cparam = v.get_sweep_params()
    start = cparam.start
    end = cparam.stop
    pts = cparam.points
    
    print(start)
    print(end)
    
    # Freq = np.linspace(int(start/10.0**9),int(end/10.0**9),pts)
    Freq = np.linspace(start/10.0**9,end/10.0**9,pts)
    
    # print(Freq[0:20])
    
    if savepath == None:
        p = make_new_dir(name)
    else:
        p = savepath
        
    v.WriteData(str(p) + '/', str(name), Freq)
    # v.WriteData(str(p) + '/', str(Angle), Freq)
    
def gui_fsweep(Angle, savepath, name, correction):
    s = rotaryStage(COM_PORT)
    
    if savepath == None:
        p = make_new_dir(name)
    else:
        p = savepath
        
    pwr_v = s.read_msg()
    if pwr_v == '':
        time.sleep(1)
        pwr_v = s.read_msg()

    save_to_csv(Angle, float(pwr_v) - correction, p)
    print(f'Data recorded for {Angle}')
    s.disconnect()
    sys.exit()
    
def set_if_bw(Freq):
    v = VNA(False)
    v.connect(16)
    
    v.set_if_bw(Freq)
    
def get_if_bw():
    pass

def set_ni_voltage_all_channel(voltage):
    v_bias = voltage
    vs = voltageSetter();
    for ch in range(0,32):
        vs.setVoltage('ao'+str(ch), v_bias)
        
def set_ni_voltage_one_channel(voltage,channel):
    v_bias = voltage
    vs = voltageSetter();
    vs.setVoltage('ao'+str(channel), v_bias)
    
@click.group()
def cli():
    pass

@cli.command()
@click.option('-v','--voltage', type=float, required=True)
def nisetall(voltage):
    set_ni_voltage_all_channel(voltage)

@cli.command()
@click.option('-v','--voltage', type=float, required=True)
@click.option('-c','--channel', type=int, required=True)
def nisetone(voltage,channel):
    set_ni_voltage_one_channel(voltage,channel)

@cli.command()
@click.option('-a','--angleswp',nargs=2, type=int, required=True)
@click.option('-s','--step', type=float, required=True)
@click.option('-p','--savepath')
@click.option('-n', '--name')
def asweep(angleswp,step,savepath,name):
    measure_angle(angleswp,step,savepath,name)
    
@cli.command()
@click.option('-a','--angleswp',nargs=2, type=int, required=True)
@click.option('-s','--step', type=float, required=True)
@click.option('-p','--savepath')
@click.option('-n', '--name')
def asweepaps(angleswp,step,savepath,name):
    measure_angle_aps(angleswp,step,savepath,name)
    
@cli.command()
@click.option('-a','--angle', type=int, required=True)
@click.option('-p','--savepath')
@click.option('-n', '--name')
def fsweep(angle,savepath,name):
    measure_fixed_angle(angle,savepath,name)
    
@cli.command()
@click.option('-d','--degrees', type=float, required=True)
@click.argument('dirn')
def rotate(degrees,dirn):
    arm_travel(degrees,dirn)
    
@cli.command()
def getfreq():
    print(get_sweep())
    
@cli.command()
@click.option('-s','--start', type=float, required=True)
@click.option('-e','--end', type=float, required=True)
@click.option('-p','--points', type=int, required=True)
def setfreq(start,end,points):
    set_sweepGHz(start, end, points)

@cli.command()    
def display4():
    display_4()
    
@cli.command()
@click.option('-p','--power', type=float, required=True)
def setpwr(power):
    set_power(power)
    
@cli.command()
@click.option('-f','--freq', type=int, required=True)
def setIFbw(freq):
    set_if_bw(freq)

@cli.command()
def reset():
    arm_home()
    
# @cli.command()
# def csvtest():
    # save_to_csv(23,56,"./")

@cli.command()
@click.option('-a','--angle', type=float, required=True)
@click.option('-p','--savepath')
@click.option('-n', '--name')
@click.option('-c', '--correction', type=float)
def fsweepaps(angle,savepath,name, correction):
    gui_fsweep(angle,savepath,name, correction)

if __name__ == '__main__':
    cli()
