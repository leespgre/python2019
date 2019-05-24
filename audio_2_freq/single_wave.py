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

from scipy.fftpack import fft, ifft, fftfreq

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
raw_data = np.zeros(CHUNK)
sin_wave = np.zeros(CALC_NUM)
spectrum = np.zeros(CALC_NUM)
wave_inv = np.zeros(CALC_NUM)

dataRange = 1000
Amp_group = np.arange(0,dataRange)
Amp_group2 = np.arange(0,dataRange)

x = np.linspace(0,CALC_NUM-1,1)
x_fft = np.linspace(0, RATE, CHUNK)

sum_temp = 0
reset_cnt = 0
amp_ave = 0

sum_temp2 = 0
reset_cnt2 = 0
amp_ave2 = 0

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
win.resize(1500,1000)
win.setWindowTitle('TACTILE FEEDBACK')
d1 = Dock("Audio_Gen", size=(50, 50))
area.addDock(d1, 'left')
d3 = Dock("Audio_process", size=(1500,1000))
area.addDock(d3, 'right', d1)## place d3 at bottom edge of d1

lock = threading.Lock()





def audio_process():
    print("* recording")
    global lock, raw_data
    global sin_wave, Amp_group, sum_temp, reset_cnt, amp_ave, runtime, Amp_diff, spectrum, window_y
    global  Amp_group2, sum_temp2, reset_cnt2, amp_ave2, Amp_diff2

    for i in range(0, LOOP_COUNT):
        rw_data = stream.read(CHUNK, exception_on_overflow=False)
        rw_data = np.frombuffer(rw_data, dtype=np.float32)
        rw_data = np.array(rw_data)

        fft_data = fft(rw_data)
        sample_freq = fftfreq(rw_data.size,d=1.0/RATE)
        fft_data_filter = fft_data.copy()

        freq_high = 3500
        freq_low = 3000

        fft_data_filter[np.abs(sample_freq) >= freq_high] = 0
        fft_data_filter[np.abs(sample_freq) <= freq_low] = 0
        ifft_data = ifft(fft_data_filter).real

        spectrum = np.abs(fft_data[0:CHUNK]) * 2 / (256 * CHUNK)

        window_y = np.zeros(len(spectrum))
        window_y[int((freq_low)/(RATE/CHUNK)):int((freq_high)/(RATE/CHUNK))] = 0.001 



        for j in range(0, GROUP_NUM):
            for k in range(0, CALC_NUM):
                sin_wave_temp = rw_data[int(CHUNK / GROUP_NUM) * j + k]
                sin_wave[k] = sin_wave_temp
                
                wave_inv_temp = ifft_data[int(CHUNK / GROUP_NUM) * j + k]
                wave_inv[k] = wave_inv_temp
            
            lock.acquire()
            Amp_temp = max(sin_wave) - min(sin_wave)
            Amp_diff = filterL.Work(Amp_temp - amp_ave)
            Amp_group = np.append(Amp_group, Amp_diff)
            Amp_group = np.delete(Amp_group, 0)


    


            lock.release()


            ## reset
            if (reset_cnt < 200):
                reset_cnt += 1
                sum_temp += Amp_temp
            if (reset_cnt == 200):
                amp_ave = sum_temp / 200
            ###
            

            ####

        time_temp = time.time() - tstart
        runtime = round((i * T), 1)
        print(len(spectrum))
        print(len(x_fft))
        # print("%.1f  % .1f %.1f %.1f" % (time_temp, runtime,(time_temp-runtime), Amp_diff))
    print("* done recording")

def update():
    global raw_data, spectrum, window_y, wave_inv
    global wave, wave2, raw_wave, w3, runtime
    global fft_filter,fft_filter2, wave_diff, wave_diff2

    w2.setTitle('Run Time: %0.1f s' % runtime)
    wave.setData(wave_inv)
    wave2.setData(sin_wave)
    fft_filter.setData(x_fft,spectrum)
    window_filter.setData(x_fft,window_y)
    fft_filter2.setData(x_fft,spectrum)
    wave_diff.setData(Amp_group)
    wave_diff2.setData(Amp_group)
    raw_wave.setData(sin_wave)
   
    app.processEvents()  ## force complete redraw for every plot

def run_program():
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

def run_thread():
        global close_flag, th
        if(close_flag!=1):
                th.start()

# placereset_data after run_program


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


def reset_data(channel):
   
    global sum_temp,reset_cnt
    try:
        
        print('press reset')
        sum_temp = 0
        reset_cnt = 0
        
        
    except:
        print("cannot reset")

        




w1 = pg.LayoutWidget()
# w1.addWidget(p1,row=0,col=0)
label = QtGui.QLabel(""" Audiotest """)
resetbtn = QtGui.QPushButton('Reset')

w1.addWidget(resetbtn,row=1,col=0)
resetbtn.clicked.connect(reset_data)
closebtn = QtGui.QPushButton('Close')

w1.addWidget(closebtn,row=3,col=0)
closebtn.clicked.connect(close)
d1.addWidget(w1)


d3.hideTitleBar()




w2= pg.PlotWidget(title="Raw Amp")
raw_wave = w2.plot(pen=pg.mkPen('w',width=1))
w2.setXRange(0,(CALC_NUM-1),padding=0.005)
w2.setYRange(-1.0,1.0,padding=0.005)
d3.addWidget(w2,row=1,col=0,colspan=2)

w3=pg.PlotWidget(title="wave")
wave = w3.plot(pen=pg.mkPen('c',width=1))
w3.setXRange(0,(CALC_NUM-1),padding=0.005)
w3.setYRange(-1.0,1.0,padding=0.005)
d3.addWidget(w3,row=2,col=0,colspan=1)

w4=pg.PlotWidget(title="wave2")
wave2 = w4.plot(pen=pg.mkPen('y',width=1))
w4.setXRange(0,(CALC_NUM-1),padding=0.005)
w4.setYRange(-1.0,1.0,padding=0.005)
d3.addWidget(w4,row=2,col=1,colspan=1)


w5=pg.PlotWidget(title="fft_filter")
fft_filter = w5.plot(pen=pg.mkPen('c',width=1))
window_filter = w5.plot(pen=pg.mkPen('r',width=1))
w5.setYRange(0, 0.0012, padding=0)
w5.setXRange(20, RATE/5, padding=0.005)
d3.addWidget(w5,row=3,col=0,colspan=1)

w6=pg.PlotWidget(title="fft_filter2")
fft_filter2 = w6.plot(pen=pg.mkPen('y',width=1))
w6.setYRange(0, 0.0012, padding=0)
w6.setXRange(20, RATE/5, padding=0.005)
d3.addWidget(w6,row=3,col=1,colspan=1)


w7=pg.PlotWidget(title="wave diff")
wave_diff = w7.plot(pen=pg.mkPen('c',width=1))
w7.setXRange(0,dataRange,padding=0.005)
w7.setYRange(-0.05,0.05,padding=0.005)
d3.addWidget(w7,row=4,col=0,colspan=1)

w8=pg.PlotWidget(title="wave diff2")
wave_diff2 = w8.plot(pen=pg.mkPen('y',width=1))
w8.setXRange(0,dataRange,padding=0.005)
w8.setYRange(-0.05,0.05,padding=0.005)
d3.addWidget(w8,row=4,col=1,colspan=1)


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

# filter
filterL = filterClass.lowPass(2,T,10)
filterL2 = filterClass.lowPass(2,T,10)
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


                

                                                
   



