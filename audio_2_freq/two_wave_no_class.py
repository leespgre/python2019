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
T = float(CHUNK)/RATE/GROUP_NUM

count = 0
raw_data = np.zeros(CHUNK)
wave_inv2 = np.zeros(CALC_NUM)
spectrum = np.zeros(CALC_NUM)
wave_inv = np.zeros(CALC_NUM)


dataRange = 1000
spectrum_range = 5000
Amp_group = np.arange(0,dataRange)
Amp_group2 = np.arange(0,dataRange)

x = np.linspace(0,CALC_NUM-1,1)
x_spectrum = np.arange(0,spectrum_range)
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
lock2 = threading.Lock()





def audio_process():
    print("* recording")
    global lock,lock2, raw_data
    global wave_inv2, Amp_group, sum_temp, reset_cnt, amp_ave, runtime, Amp_diff, spectrum, window_y, window_y2
    global  Amp_group2, sum_temp2, reset_cnt2, amp_ave2, Amp_diff2

    for i in range(0, LOOP_COUNT):
        rw_data = stream.read(CHUNK, exception_on_overflow=False)
        rw_data = np.frombuffer(rw_data, dtype=np.float32)
        rw_data = np.array(rw_data)

        fft_data = fft(rw_data)
        sample_freq = fftfreq(rw_data.size,d=1.0/RATE)
        spectrum = np.abs(fft_data[0:CHUNK]) * 2 / (256 * CHUNK)


        fft_data_filter = fft_data.copy()
        freq_high = 3500
        freq_low = 3100
        fft_data_filter[np.abs(sample_freq) >= freq_high] = 0
        fft_data_filter[np.abs(sample_freq) <= freq_low] = 0
        ifft_data = ifft(fft_data_filter).real
        window_y = np.zeros(spectrum_range)
        window_y[freq_low:freq_high] = 0.002


        fft_data_filter2 = fft_data.copy()
        freq_high2 = 3000
        freq_low2 = 2850
        fft_data_filter2[np.abs(sample_freq) >= freq_high2] = 0
        fft_data_filter2[np.abs(sample_freq) <= freq_low2] = 0
        ifft_data2 = ifft(fft_data_filter2).real
        window_y2 = np.zeros(spectrum_range)
        window_y2[freq_low2:freq_high2] = 0.002



        for j in range(0, GROUP_NUM):
            for k in range(0, CALC_NUM):
                wave_inv2_temp = ifft_data2[int(CHUNK / GROUP_NUM) * j + k]
                wave_inv2[k] = wave_inv2_temp

                wave_inv_temp = ifft_data[int(CHUNK / GROUP_NUM) * j + k]
                wave_inv[k] = wave_inv_temp
            
            lock.acquire()
            Amp_temp = max(wave_inv) - min(wave_inv)
            Amp_diff = filterL.Work(Amp_temp - amp_ave)
            Amp_group = np.append(Amp_group, Amp_diff)
            Amp_group = np.delete(Amp_group, 0)
            lock.release()

            lock2.acquire()
            Amp_temp2 = max(wave_inv2) - min(wave_inv2)
            Amp_diff2 = filterL2.Work(Amp_temp2 - amp_ave2)
            Amp_group2 = np.append(Amp_group2, Amp_diff2)
            Amp_group2 = np.delete(Amp_group2, 0)
            lock2.release()
            

            ## reset
            if (reset_cnt < 200):
                reset_cnt += 1
                sum_temp += Amp_temp
            if (reset_cnt == 200):
                amp_ave = sum_temp / 200
            ###
            if (reset_cnt2 < 200):
                reset_cnt2 += 1
                sum_temp2 += Amp_temp2
            if (reset_cnt2 == 200):
                amp_ave2 = sum_temp2 / 200

            ####

        time_temp = time.time() - tstart
        runtime = round((i * T * GROUP_NUM), 1)
        print(len(spectrum))
        print(len(x_fft))
        print("%.1f  % .1f %.1f %.1f" % (time_temp, runtime,(time_temp-runtime), Amp_diff))
    print("* done recording")

def update():
    global raw_data, spectrum, window_y, window_y2, wave_inv, wave_inv2
    global wave, wave2, raw_wave, w3, runtime
    global fft_filter,fft_filter2, wave_diff, wave_diff2

    w2.setTitle('Run Time: %0.1f s' % runtime)
    wave.setData(wave_inv)
    wave2.setData(wave_inv2)
    fft_filter.setData(x_fft,spectrum)
    window_filter.setData(x_spectrum,window_y)
    fft_filter2.setData(x_fft,spectrum)
    window_filter2.setData(x_spectrum,window_y2)
    wave_diff.setData(Amp_group)
    wave_diff2.setData(Amp_group2)
    raw_wave.setData(wave_inv2)
   
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
   
    global sum_temp,reset_cnt, sum_temp2, reset_cnt2
    try:
        
        print('press reset')
        sum_temp = 0
        reset_cnt = 0
        sum_temp2 = 0
        reset_cnt2 = 0
        
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
w5.setYRange(0, 0.002, padding=0)
w5.setXRange(0, spectrum_range, padding=0.005)
d3.addWidget(w5,row=3,col=0,colspan=1)

w6=pg.PlotWidget(title="fft_filter2")
fft_filter2 = w6.plot(pen=pg.mkPen('y',width=1))
window_filter2 = w6.plot(pen=pg.mkPen('r',width=1))
w6.setYRange(0, 0.002, padding=0)
w6.setXRange(0, spectrum_range, padding=0.005)
d3.addWidget(w6,row=3,col=1,colspan=1)


w7=pg.PlotWidget(title="wave diff")
wave_diff = w7.plot(pen=pg.mkPen('c',width=1))
w7.setXRange(0,dataRange,padding=0.005)
w7.setYRange(-0.65,0.65,padding=0.005)
d3.addWidget(w7,row=4,col=0,colspan=1)

w8=pg.PlotWidget(title="wave diff2")
wave_diff2 = w8.plot(pen=pg.mkPen('y',width=1))
w8.setXRange(0,dataRange,padding=0.005)
w8.setYRange(-0.65,0.65,padding=0.005)
d3.addWidget(w8,row=4,col=1,colspan=1)


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

# filter
filterL = filterClass.lowPass(2,T,2)
filterL2 = filterClass.lowPass(2,T,2)
# filter.print()
filterH= filterClass.highPass(1,T,0.5)
# filterH.print()
#

tstart =time.time()
th = threading.Thread(name='audio_process', target=audio_process)
# reset_th = threading.Thread(name='reset_process', target=reset_data)


if __name__ == '__main__':
        run_thread()
        win.show()
        run_program()
        sys.exit(app.exec_())


                

                                                
   



