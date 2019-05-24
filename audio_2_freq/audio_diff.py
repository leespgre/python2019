# import GPIO module

import threading
from pyqtgraph.Qt import QtGui, QtCore
import sys
import pyqtgraph as pg
from pyqtgraph.dockarea import *
import numpy as np
import pyaudio
import math
import time

import filterClass
#####
CHUNK = 200
FORMAT = pyaudio.paFloat32
CHANNEL = 1
RATE = 44100
RECORD_SECONDS = 500
GROUP_NUM = 4
CALC_NUM= 14
LOOP_COUNT= int(RECORD_SECONDS/0.004)
T = float(CHUNK)/RATE

count = 0
sin_wave = np.zeros(CALC_NUM)
dataRange = 1000
Amp_group = np.arange(0,dataRange)

sum_temp = 0
reset_cnt = 0
amp_ave = 0

close_flag=0
runtime=0

feedback_flag = 0
ThresH = 0.01
######################################




Amp_diff  = 0.0


#############################################################


##--------------------------
#################################################
flag_run = 0
close_flag = 0
i = 0


p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                channels=CHANNEL,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK)


app = QtGui.QApplication([])
win = QtGui.QMainWindow()
area = DockArea()
win.setCentralWidget(area)
win.resize(1000,500)
win.setWindowTitle('TACTILE FEEDBACK')
d1 = Dock("Audio_Gen", size=(50, 50))
area.addDock(d1, 'left')
d3 = Dock("Audio_process", size=(500,500))
area.addDock(d3, 'right', d1)## place d3 at bottom edge of d1

lock = threading.Lock()


# place run_program first in every code
def run_program():
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()




def audio_process():
    print("* recording")
    global sin_wave, Amp_group, sum_temp, reset_cnt, amp_ave, runtime, Amp_diff
    for i in range(0, LOOP_COUNT):
        rw_data = stream.read(CHUNK, exception_on_overflow=False)
        rw_data = np.frombuffer(rw_data, dtype=np.float32)
        rw_data = np.array(rw_data)
        for j in range(0, GROUP_NUM):
            for k in range(0, CALC_NUM):
                sin_wave_temp = rw_data[int(CHUNK / GROUP_NUM) * j + k]
                sin_wave[k] = sin_wave_temp
            Amp_temp = max(sin_wave) - min(sin_wave)
            Amp_diff = filterL.Work(Amp_temp - amp_ave)
            Amp_group = np.append(Amp_group, Amp_diff)
            Amp_group = np.delete(Amp_group, 0)
            ## reset
            if (reset_cnt < 200):
                reset_cnt += 1
                sum_temp += Amp_temp
            if (reset_cnt == 200):
                amp_ave = sum_temp / 200
            ###

        time_temp = time.time() - tstart
        runtime = round((i * T), 1)
        print("%.1f  % .1f %.1f %.1f" % (time_temp, runtime,(time_temp-runtime), Amp_diff))
    print("* done recording")

def update():
    global curve, w3, runtime, raw_curve
    w3.setTitle('Run Time: %0.1f s' % runtime)
    curve.setData(Amp_group)
    raw_curve.setData(sin_wave)
    app.processEvents()  ## force complete redraw for every plot

def run_thread():
        global close_flag, th
        if(close_flag!=1):
                th.start()

# placereset_data after run_program

def reset_data(channel):
   
    global sum_temp,reset_cnt,lock
    try:
        lock.acquire()
        print('press reset')
        sum_temp = 0
        reset_cnt = 0
        lock.release()
    except:
        print("cannot reset")
def close(channel):
    global close_flag, app, p , stream, th
    close_flag=1
    try:
        stream.close()
        p.terminate()
        timer.stop()
        # th.join()
        print('close')   
    except:
        print("cannot close")
    finally:
        sys.exit("exit")
        




w1 = pg.LayoutWidget()
# w1.addWidget(p1,row=0,col=0)
label = QtGui.QLabel(""" Audiotest """)
resetbtn = QtGui.QPushButton('Reset')
w1.addWidget(resetbtn,row=1,col=0)
resetbtn.clicked.connect(reset_data)
closebtn = QtGui.QPushButton('Close')
w1.addWidget(closebtn,row=2,col=0)
closebtn.clicked.connect(close)
d1.addWidget(w1)

# w2 = pg.LayoutWidget()
# resetbtn = QtGui.QPushButton('Reset')
# resetbtn.setGeometry(QtCore.QRect(20,10,250,50))
# w2.addWidget(resetbtn,1,1)
# resetbtn.clicked.connect(reset_data)
# d1.addWidget(w2)



d3.hideTitleBar()
w3=pg.PlotWidget(title="Changed Amp")
curve = w3.plot(pen=pg.mkPen('y',width=1))
w3.setXRange(0,dataRange,padding=0.005)
w3.setYRange(-0.05,0.05,padding=0.005)
d3.addWidget(w3,row=1,col=0)
w4= pg.PlotWidget(title="Raw Amp")
raw_curve = w4.plot(pen=pg.mkPen('r',width=1))
w4.setXRange(0,(CALC_NUM-1),padding=0.005)
w4.setYRange(-1.0,1.0,padding=0.005)
d3.addWidget(w4,row=2,col=0)








timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

# filter
filterL = filterClass.lowPass(2,T,10)
# filter.print()
filterH= filterClass.highPass(1,T,0.5)
# filterH.print()
#

tstart =time.time()
th = threading.Thread(name='audio_process', target=audio_process,  daemon=True)
# reset_th = threading.Thread(name='reset_process', target=reset_data)


if __name__ == '__main__':
        run_thread()
        win.show()
        run_program()
        sys.exit(app.exec_())


                

                                                
   



