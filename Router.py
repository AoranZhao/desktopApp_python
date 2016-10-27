
from socket import *
from threading import *
import struct
import os
import time
from ButterworthFilter import *
from scipy.fftpack import fft
from scipy import signal

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

HOST = '192.168.1.115'
PORT = 8899
BUF_SIZE = 1                            # read 1 bytes from socket every time

FSC = 4642997
BETA = 1.8202
OFC = -7085
ALPHA = 0x3E8000
V_REF = 2.5
PGA = 64

class Router(Thread):
    head = []                           # array buffer storing 4 bytes last received for detect whether it is head
    tail = []                           # array buffer storing 4 bytes last received for detect whether it is tail
    body = []                           # array buffer storing 60 int
    body_c = []                         # array buffer stroing 60 calculated int
    body_ele = []                       # array buffer storing 4 bytes last received for convert to int
    body_filter = []
    body_fft = []
    body_fft_result = []
    body_fft_re_real = []
    body_fft_re_imag = []
    current_path = ''
    filename = ''
    hostIp = ''
    global g_nc_int_filter, g_attention, g_alpha_arr, g_beta_arr, g_ss_spectrum

    def __init__(self):
        
        print("initial finish.")
        
        super(Router, self).__init__()

    def run(self):
        self.current_path = os.path.abspath('.')
        self.filename = self.current_path + '/config.txt'

        try:
            configFile = open(self.filename)
            self.hostIp = configFile.readline().strip()
            configFile.close()
        except:
            print('not found config.txt file.')

        if self.hostIp == '':
            self.hostIp = HOST

        try:
            self.s = socket(AF_INET, SOCK_STREAM)
        except:
            print("fail to build up socket")
            sys.exit()
        print("build socket successfully")
        while True:
            while True:
                try:
                    print("waiting")
                    # self.s.connect((HOST, PORT))
                    self.s.connect((self.hostIp, PORT))
                    print("connect success")
                    break
                except:
                    # time.sleep(1)
                    continue
            while True:
                try:
                    data = self.s.recv(BUF_SIZE)
                except:
                    break
                    # continue
                if data:
                    if (self.detectHead(data)):                 # empty all array buffer when detect head or tail
                        self.cleanArray()
                    elif (self.detectTail(data)):
                        self.dosomething()
                        self.cleanArray()
                    else:
                        self.decode(data)

    def dosomething(self):                                       # do somethin when received package of full 60 int
        BP_b1, BP_a1 = signal.bessel(4, [8.0 / 30.0, 14.0 / 30.0], 'bandpass')        # alpha bandpass parameter
        BP_b2, BP_a2 = signal.bessel(4, [15.0 / 30.0, 29.0 / 30.0], 'bandpass')        # beta bandpass parameter

        nc_int_filter = filterloop(self.body_c)
        #print(str(len(nc_int_filter)))
        #print(nc_int_filter)

        alpha_db_filter = signal.filtfilt(BP_b1, BP_a1, nc_int_filter)
        beta_db_filter = signal.filtfilt(BP_b2, BP_a2, nc_int_filter)

        g_alpha_arr.extend(alpha_db_filter)
        g_beta_arr.extend(beta_db_filter)
        g_nc_int_filter.extend(nc_int_filter)
        if (len(self.body_fft) >= 300):
            self.body_fft = self.body_fft[60:300]
            self.body_fft.extend(nc_int_filter)
            self.body_fft_result = fft(self.body_fft)
            body_fft_result_temp = abs(self.body_fft_result)
            for i in range(len(body_fft_result_temp) / 2):
                g_ss_spectrum[i] = body_fft_result_temp[i]
            self.seperate_complexe()
            attentionLevel = self.clc_attn(self.body_fft_re_real, self.body_fft_re_imag)
            g_attention[0] = attentionLevel
            print(attentionLevel)
        else:
            self.body_fft.extend(nc_int_filter)

    def decode(self, data):
        self.body_ele.append(data)
        if (len(self.body_ele) < 4):
            return False
        else:
            b_str = ''.join(self.body_ele)
            n_int = struct.unpack('i', b_str)
            self.body.append(n_int[0])
            nc_int = self.canculate(n_int[0])
            self.body_c.append(nc_int)
            self.body_ele = []
            return True

    def canculate(self, data):
        result = (data * 1.0 / FSC / BETA + OFC * 1.0 / ALPHA) * 2 * V_REF / PGA * 1000000
        return result

    #def writefile(self, data):
    #    f = open(self.filename, 'w')
    #    temp_str = ''
    #    for i in range(len(data)):
    #        temp_str += str(data[i]) + ' '
    #    f.write(temp_str)
    #    f.close()

    def cleanArray(self):
        self.head = []
        self.tail = []
        self.body = []
        self.body_c = []
        self.body_ele = []
        self.body_filter = []
        self.body_fft_re_real = []
        self.body_fft_re_imag = []

    def detectHead(self, piece):
        self.head.append(piece)
        if (len(self.head) < 4):
            return False
        else:
            if (self.head[0] == '\xff' and self.head[1] == '\xff' and self.head[2] == '\xff' and self.head[3] == '\x7f'):
                self.head = self.head[1:4]
                return True
            else:
                self.head = self.head[1:4]
                return False

    def detectTail(self, piece):
        self.tail.append(piece)
        if (len(self.tail) < 4):
            return False
        else:
            if (self.tail[0] == '\xff' and self.tail[1] == '\xff' and self.tail[2] == '\xff' and self.tail[3] == '\x6f'):
                self.tail = self.tail[1:4]
                return True
            else:
                self.tail = self.tail[1:4]
                return False

    def clc_attn(self, input_fft_re_real, input_fft_re_imag, input_size=300, low_alpha=5.0, high_alpha=8.0, low_beta=8.0, high_beta=20.0, sample_rate=60):
        alpha = 0;
        beta = 0;

        output_frequency_Re = input_fft_re_real
        zero_imag = input_fft_re_imag

        low_alpha_i = round(low_alpha * input_size / sample_rate)
        high_alpha_i = round(high_alpha * input_size / sample_rate)
        low_beta_i = round(low_beta * input_size / sample_rate)
        high_beta_i = round(high_beta * input_size / sample_rate)

        for i in range(int(low_alpha_i), int(high_alpha_i + 1), 1):
            alpha += output_frequency_Re[i] ** 2 + zero_imag[i] ** 2

        for i in range(int(low_beta_i), int(high_beta_i + 1), 1):
            beta += output_frequency_Re[i] ** 2 + zero_imag[i] ** 2

        alpha /= high_alpha_i - low_alpha_i + 1;
        beta /= high_beta_i - low_beta_i + 1;

        result = round(100 * beta / alpha)

        return result

    def seperate_complexe(self):
        for i in range(len(self.body_fft_result)):
            self.body_fft_re_real.append(self.body_fft_result[i].real)
            self.body_fft_re_imag.append(self.body_fft_result[i].imag)


g_nc_int_filter = []
g_attention = [0]
g_alpha_arr = []
g_beta_arr = []
g_ss_spectrum = [0 for i in range(150)]

g_filter_show = [0 for i in range(600)]
g_atten_show = [0 for i in range(100)]
g_alpha_show = [0 for i in range(600)]
g_beta_show = [0 for i in range(600)]
g_ss_s_show = [0 for i in range(30)]
atten_x = [float(i) / 10.0 for i in range(100)]
spec_x = [i for i in range(31)]

app = QtGui.QApplication([])
win = pg.GraphicsWindow(title="Analyzer")
win.resize(1800,1000)
win.setWindowTitle('BrainCo Electroencephalogram Analyzer')

# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

pltRaw = win.addPlot(title="Raw EEG Waveform", row=0, col=0, colspan=2)
pltRaw.setLabel('left',text="Voltage (uV)")
pltRaw.setLabel('bottom',text="Time")
pltRaw.setLimits(yMax=4000, yMin=-4000, maxYRange=8000, minYRange=300)
#pltRaw.setYRange(100, 4000, padding=0)
curve = pltRaw.plot(pen='y')

#
pltAlpha = win.addPlot(title='Alpha', row=0, col=2)
pltAlpha.setLabel('left',text='Beta')
pltAlpha.setLabel('bottom',text='Time')
pltAlpha.setLimits(yMax=1000, yMin=-1000, maxYRange=2000, minYRange=40)
curve3 = pltAlpha.plot(pen='m')

win.nextRow()
## attention level
pltAtten = win.addPlot(title="Attention Level", row=1, col=0)
pltAtten.setLabel('left',text='Attention Level')
pltAtten.setLabel('bottom',text='Time')
pltAtten.setLimits(yMin=0, minYRange=100)
curve2 = pltAtten.plot(atten_x, g_atten_show, pen='r')
#curve2.setData(g_atten_show)


### spectrum
pltSpec = win.addPlot(title="Spectrum", row=1, col=1)
pltSpec.setLabel('left',text='enegy')
pltSpec.setLabel('bottom',text='Hz')
pltSpec.plot(spec_x, g_ss_s_show, stepMode=True, fillLevel=0, brush=(0,0,255,150))
pltSpec.setLimits(yMin=0)

#

pltBeta = win.addPlot(title='Beta', row=1, col=2)
pltBeta.setLabel('left',text='Beta')
pltBeta.setLabel('bottom',text='Time')
pltBeta.setLimits(yMax=1000, yMin=-1000, maxYRange=2000, minYRange=40)
curve4 = pltBeta.plot(pen='c')

def update():
    global g_nc_int_filter, g_filter_show, g_attention, g_atten_show, g_alpha_arr, g_alpha_show, g_beta_arr, g_beta_show
    if len(g_nc_int_filter) >= 155:
        g_filter_show.extend(g_nc_int_filter)
        g_nc_int_filter = []
    if len(g_nc_int_filter) >= 6:
        g_filter_show.extend(g_nc_int_filter[:6])
        g_nc_int_filter = g_nc_int_filter[6:]
    if len(g_filter_show) > 600:
        g_filter_show = g_filter_show[-600:]
    curve.setData(g_filter_show)

    # attention level
    if len(g_attention) >= 1:
        g_atten_show.extend(g_attention[:1])

    if len(g_atten_show) > 100:
        g_atten_show = g_atten_show[-100:]
    curve2.setData(atten_x, g_atten_show)

    # alpha
    if len(g_alpha_arr) >= 155:
        g_alpha_show.extend(g_alpha_arr)
        g_alpha_arr = []
    if len(g_alpha_arr) >= 6:
        g_alpha_show.extend(g_alpha_arr[:6])
        g_alpha_arr = g_alpha_arr[6:]
    if len(g_alpha_show) > 600:
        g_alpha_show = g_alpha_show[-600:]
    curve3.setData(g_alpha_show)

    # beta
    if len(g_beta_arr) >= 155:
        g_beta_show.extend(g_beta_arr)
        g_beta_arr = []
    if len(g_beta_arr) >= 6:
        g_beta_show.extend(g_beta_arr[:6])
        g_beta_arr = g_beta_arr[6:]
    if len(g_beta_show) > 600:
        g_beta_show = g_beta_show[-600:]
    curve4.setData(g_beta_show)

    # single side spectrum

    ## compute standard histogram

    for i in range(30):
        g_ss_s_show[i] = g_ss_spectrum[i * 5]
    ## Using stepMode=True causes the plot to draw two lines for each sample.
    ## notice that len(x) == len(y)+1
    pltSpec.clear()
    pltSpec.plot(spec_x, g_ss_s_show, stepMode=True, fillLevel=0, brush=(0,0,255,150))




timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(90)


r = Router()
r.start()

app.exec_()
