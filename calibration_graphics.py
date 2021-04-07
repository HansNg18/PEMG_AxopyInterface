# -*- coding: utf-8 -*-
"""
Widget for plotting calibration information for Arduino PEMG system.
Tested on PEMG v2.2.x

"""


import numpy as np
from pyqtgraph.Qt import QtGui
from PyQt5.QtWidgets import QWidget, QGridLayout, QDesktopWidget
import pyqtgraph as pg



class CalibrationWidget(QWidget):
    def __init__(self, channel_names=None):
        super(CalibrationWidget, self).__init__()

        self.plot_items = []
        self.plot_data_items = []

        self.n_channels = 0
        self.channel_names = channel_names 
        
    def plot(self, data):
        nch, nsamp  = data.shape
        if nch != self.n_channels:
            self.n_channels = nch

            if self.channel_names is None:
                self.channel_names = range(self.n_channels)
                
            self._update_num_channels(data)
            
        for i, pdi in enumerate(self.plot_items):
            pdi.data = data
            pdi.emg.setData(data[i,:])
            
    def _update_num_channels(self, data):
        """
        Adds a dock for each channels
        """
        for i, name in zip(range(self.n_channels), self.channel_names):
            plot_item = NewChannel(i, self.channel_names, self.n_channels, data, self.plot_items)
            plot_item.show()
            self.plot_items.append(plot_item)  
            
    def _close_channels(self):
        for i in  range(len(self.plot_items)):
            self.plot_items[i].close_channels()


class ValidationWidget(QWidget):
    def __init__(self, channel_names=None):
        super(ValidationWidget, self).__init__()

        self.plot_items = []
        self.plot_data_items = []

        self.n_channels = 0
        self.channel_names = channel_names 
        
    def plot(self, data):
        data_raw = data[:2,:]
        data_mav = data[2:4,:]
        nch, nsamp  = data_raw.shape
        if nch != self.n_channels:
            self.n_channels = nch

            if self.channel_names is None:
                self.channel_names = range(self.n_channels)
                
            self._update_num_channels(data_raw)
            
        for i, pdi in enumerate(self.plot_items):
            pdi.data_raw = data_raw
            pdi.emg.setData(data_raw[i,:])
            pdi.bar.setOpts(height=data_mav[i,:])
            
    def _update_num_channels(self, data):
        """
        Adds a dock for each channels
        """
        for i, name in zip(range(self.n_channels), self.channel_names):
            plot_item = NewChannel(i, self.channel_names, self.n_channels, data, self.plot_items)
            plot_item.show()
            self.plot_items.append(plot_item)  
            
    def _close_channels(self):
        for i in  range(len(self.plot_items)):
            self.plot_items[i].close_channels()


class NewChannel(QtGui.QWidget):
    def __init__(self,ch_number, ch_names, n_channels, data, plot_items):
        QWidget.__init__(self)

        self.ch_number = ch_number
        self.ch_names = ch_names
        self.n_channels = n_channels

        self.data = data
        self.plot_items = plot_items

        self.setWindowTitle(self.ch_names[self.ch_number])
        
        layout = QGridLayout()
        layout.setSpacing(20)
        self.setLayout(layout)     
        
        # Widgets
        self.emgWidget = pg.PlotWidget(background=None)
        self.emg = self.emgWidget.plot(pen='b')
        self.emgWidget.hideAxis('left')
        self.emgWidget.hideAxis('bottom')
        
        self.barWidget = pg.PlotWidget(background=None)
        self.bar = pg.BarGraphItem(x=[1.],height=[0.], width=1, brush='b')
        self.barWidget.addItem(self.bar)
        self.barWidget.setYRange(0, 1)
        self.barWidget.hideAxis('bottom')
        self.barWidget.showGrid(y=True, alpha=0.5)

        layout.addWidget(self.emgWidget, 0,0,4,1)
        layout.addWidget(self.barWidget, 0,1,4,1)
        layout.setColumnStretch(1,6)
        layout.setColumnStretch(2,1)


        # determine where on screen the window will be positioned
        screen = QDesktopWidget().screenGeometry()
        
        # define positions, with a max of 2 rows
        if self.n_channels == 1:
            positions = [(0,0)]
        elif self.n_channels == 2:
            positions = [(0,0), (0,1)]
        else:
            positions = [(i,j) for i in range(2) for j in range(int(np.ceil(self.n_channels/2)))]   
        max_row = max(positions)[0]
        max_col = max(positions)[1]
        w_w = screen.width()/(max_col+1)
        w_h = min([w_w/3, screen.height()/(max_row+1)])

        self.resize(w_w, w_h)
        self.move(w_w*positions[self.ch_number][1], w_h*positions[self.ch_number][0])
        
        self.installEventFilter(self)    
        
    def close_channels(self):
        self.close()