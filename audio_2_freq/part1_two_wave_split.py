import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

import struct
import pyaudio

from scipy.fftpack import fft, ifft, fftfreq
import sys
import time

class AudioStream(object):
    def __init__(self):
        pg.setConfigOptions(antialias=True)
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsWindow(title='Sinwave Collection')
        self.win.setWindowTitle('Sinwave')
        self.rawwave=self.win.addPlot(
            title='rawwave', row=1, col=1, colspan=2
        )
        self.spectrum=self.win.addPlot(
            title='spectrum', row=2, col=1, colspan=1
        )
        self.inv_wave=self.win.addPlot(
            title='inverse_wave', row=3, col=1,colspan=1
        )

        self.spectrum2=self.win.addPlot(
            title='spectrum2', row=2, col=2, colspan=1
        )
        self.inv_wave2=self.win.addPlot(
            title='inverse_wave2', row=3, col=2, colspan=1
        )

        # pyaudio stuff
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024 * 2

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=False,
            frames_per_buffer=self.CHUNK,
        )
        # waveform and spectrum x points
        self.x = np.arange(0, 2 * self.CHUNK, 2)
        self.x_fft = np.linspace(0, self.RATE, self.CHUNK)

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'rawwave':
                self.traces[name] = self.rawwave.plot(pen='c', width=3)
                self.rawwave.setYRange(-0.5, 0.5, padding=0)
                self.rawwave.setXRange(0, 2 * self.CHUNK, padding=0.005)
            
         
         

            if name == 'spectrum':
                self.traces[name] = self.spectrum.plot(pen='c', width=3)
                self.spectrum.setYRange(0, 0.0012, padding=0)
                self.spectrum.setXRange(20, self.RATE/5, padding=0.005)
            if name == 'window':
                self.traces[name] = self.spectrum.plot(pen='r', width=3)

            if name == 'inverse_wave':
                self.traces[name] = self.inv_wave.plot(pen='c', width=3)
                self.inv_wave.setYRange(-0.5, 0.5, padding=0)
                self.inv_wave.setXRange(0, 2 * self.CHUNK, padding=0.005)

            if name == 'spectrum2':
                self.traces[name] = self.spectrum2.plot(pen='y', width=3)
                self.spectrum.setYRange(0, 0.0012, padding=0)
                self.spectrum2.setXRange(20, self.RATE/5, padding=0.005)
            if name == 'window2':
                self.traces[name] = self.spectrum2.plot(pen='r', width=3)

            if name == 'inverse_wave2':
                self.traces[name] = self.inv_wave2.plot(pen='y', width=3)
                self.inv_wave2.setYRange(-0.5, 0.5, padding=0)
                self.inv_wave2.setXRange(0, 2 * self.CHUNK, padding=0.005)

    def update(self):
        rw_data = self.stream.read(self.CHUNK,exception_on_overflow=False)
        rw_data = np.fromstring(rw_data, dtype=np.float32)
        rw_data = np.array(rw_data)
        fft_data = fft(rw_data)
        sample_freq = fftfreq(rw_data.size,d=1.0/self.RATE)
        fft_data_filter = fft_data.copy()
        fft_data_filter2 = fft_data.copy()

        freq_high = 2500
        freq_low = 2000

        fft_data_filter[np.abs(sample_freq) > freq_high] = 0
        fft_data_filter[np.abs(sample_freq) < freq_low] = 0
        ifft_data = ifft(fft_data_filter).real

        fft_data = np.abs(fft_data[0:self.CHUNK]) * 2 / (256 * self.CHUNK)
        max_fft = np.max(fft_data)

        window_y = np.zeros(len(fft_data))
        window_y[int((freq_low)/(self.RATE/self.CHUNK)):int((freq_high)/(self.RATE/self.CHUNK))] = 0.001 


        freq_high2 = 3500
        freq_low2 = 3000
        window_y2 = np.zeros(len(fft_data))
        window_y2[int((freq_low2)/(self.RATE/self.CHUNK)):int((freq_high2)/(self.RATE/self.CHUNK))] = 0.001 

        fft_data_filter2[np.abs(sample_freq) > freq_high2] = 0
        fft_data_filter2[np.abs(sample_freq) < freq_low2] = 0
        ifft_data2 = ifft(fft_data_filter2).real

        self.set_plotdata(name='rawwave', data_x=self.x, data_y=rw_data)
        self.set_plotdata(name='spectrum', data_x=self.x_fft, data_y=fft_data)
        self.set_plotdata(name='window', data_x=self.x_fft, data_y=window_y)
        self.set_plotdata(name='inverse_wave', data_x=self.x, data_y=ifft_data)

        self.set_plotdata(name='spectrum2', data_x=self.x_fft, data_y=fft_data)
        self.set_plotdata(name='window2', data_x=self.x_fft, data_y=window_y2)
        self.set_plotdata(name='inverse_wave2', data_x=self.x, data_y=ifft_data2)
        # print(len(self.x))
        # print(len(ifft_data))
        # print(ifft_data)
        print(len(fft_data))
        print(np.argmax(fft_data))
       

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()

if __name__ == '__main__':

    audio_app = AudioStream()
    audio_app.animation()