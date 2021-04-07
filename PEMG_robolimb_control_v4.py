"""
PEMG robolimb control


All configuration settings are stored and loaded from an external configuration
file (``config.ini``).


"""

import os
import numpy as np
import math
import datetime
import time

from argparse import ArgumentParser
from configparser import ConfigParser

from PyQt5.QtGui import QColor
from axopy.gui.main import get_qtapp
from axopy.gui.canvas import Canvas, Basket, Target, Circle, Text
from axopy.daq import NoiseGenerator
from axopy import pipeline
from axopy.task import Task
from axopy.experiment import Experiment
from axopy.timing import Counter,Timer
from axopy import util
from axopy.pipeline import Windower, Pipeline

from pyqtgraph.Qt import QtGui
from PyQt5.QtWidgets import QWidget, QGridLayout, QDesktopWidget
import pyqtgraph as pg

from calibration_graphics import CalibrationWidget, ValidationWidget

from Arduinopydaqs.ArduinoPEMGdaq import ArduinoMKR_DAQ
# import sys
# sys.path.insert(1, 'D:\\dropbox file\\Dropbox\\current project\\20201116 able body experiment')
# from ArduinoPEMGdaq_v5 import ArduinoMKR_DAQ



'''create the dictionary to map the 2-channel MAVs to the MCI'''
class MCI_Mapping_Matrix():
    
    def __init__(self,origin= (0,-1),length= 2):
        self.origin = origin
        self.length = length
        self.x_dic = np.zeros((101,101))
        self.y_dic = np.zeros((101,101))
        
    def mapping_matrix(self):
        for i in range(0,101,1):
            for j in range(0,101,1):
                mag = math.sqrt((0.01*i)**2+(0.01*j)**2)
                phase = 0.75*math.pi-math.atan2(j,i)
                self.x_dic[i,j]=self.origin[0]+self.length*mag*math.cos(phase)
                self.y_dic[i,j]=self.origin[1]+self.length*mag*math.sin(phase)
        return [self.x_dic,self.y_dic]


''''mapping the MAVs to the MCI based on the dictionary'''        
class MCI_Mapping(pipeline.Block):
    
    def __init__(self, dictionary_x, dictionary_y):
        super(MCI_Mapping, self).__init__()
        self.dictionary_x = dictionary_x
        self.dictionary_y = dictionary_y
        self.grip = 0
        
    def process(self,data):
        self.x = self.dictionary_x[int(100*data[0,0]),int(100*data[1,0])]
        self.y = self.dictionary_y[int(100*data[0,0]),int(100*data[1,0])]
        self.grip = data[3,0]
        return [self.x,self.y,self.grip]




class ACTrainingVisible(Task):
    def __init__(self, pipeline):
        super(ACTrainingVisible, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6)
        self.background4 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background4)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        # self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target4 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        self.canvas.add_item(self.target4)

        container.set_widget(self.canvas)
        
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(TRAINING_TIME) 
        self.result_timer.timeout.connect(self.finish)
        
    def run(self):
        self.pipeline.clear()
        self.connect(self.daqstream.updated, self.update)
        
    def update(self, data):
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        
        if (self.previous_grip == 0) and (grip != 0):
            # self.cursor.show()
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
            self.target4.hide()
                
        self.previous_grip = int(self.grip)
        self.result_timer.increment()
        

    def finish(self):
        self.daqstream.stop()

        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)

class ACTrainingInv(Task):
    def __init__(self, pipeline):
        super(ACTrainingInv, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6)
        self.background4 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background4)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target4 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        self.canvas.add_item(self.target4)

        container.set_widget(self.canvas)
        
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(TRAINING_TIME)
        self.result_timer.timeout.connect(self.finish)
        
    def run(self):
        self.pipeline.clear()
        self.connect(self.daqstream.updated, self.update)
        
    def update(self, data):
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        
        if (self.previous_grip == 0) and (grip != 0):
            self.cursor.show()
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.cursor.hide()
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
            self.target4.hide()
                
        self.previous_grip = int(self.grip)
        self.result_timer.increment()

    def finish(self):
        self.daqstream.stop()

        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)            

class ACTestVisible(Task):
    
    def __init__(self, pipeline):
        super(ACTestVisible, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.num_trial1 = 0.0
        self.num_trial2 = 0.0
        self.num_trial3 = 0.0
        self.num_trial4 = 0.0
        self.num_correct1 = 0.0
        self.num_correct2 = 0.0
        self.num_correct3 = 0.0
        self.num_correct4 = 0.0
      
    def prepare_design(self, design):
        num_grip = TRIAL_PER_GRIP #the number of each grip in each block
        # num_grip = 1
        t1 = np.ones(num_grip)
        t2 = 2*np.ones(num_grip)
        t3 = 3*np.ones(num_grip)
        t4 = 4*np.ones(num_grip)
        target_grip =np.concatenate((t1,t2,t3,t4)) 
        target_grip = target_grip.astype(int)
        block = design.add_block()
        for grip in target_grip:
            block.add_trial(attrs={
                                'target_grip': str(grip),
                                'mav1':str(0),
                                'mav2':str(0),
                                'selected_grip': str(0),
                                'path_eff':str(0)
                            })   
        block.shuffle()
        
        
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_AC_Visible'+ t)
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6)
        self.background4 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background4)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target4 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        self.canvas.add_item(self.target4)
         
        '''result interface'''
        self.text_result = Text(text ='default', color ='green')
        self.text_result.x = -0.2
        self.text_result.hide()
        self.text_timeout = Text(text ='Timeout', color ='red')
        self.text_timeout.hide()
        

        self.text_Accuracy1 = Text(text ='Accuracy', color ='green')
        self.text_Accuracy1.x = -0.5
        self.text_Accuracy1.y = 0.5
        self.text_Accuracy1.hide()
        self.text_Accuracy2 = Text(text ='Accuracy', color ='green')
        self.text_Accuracy2.x = -0.5
        self.text_Accuracy2.y = 0.2
        self.text_Accuracy2.hide()
        self.text_Accuracy3 = Text(text ='Accuracy', color ='green')
        self.text_Accuracy3.x = -0.5
        self.text_Accuracy3.y = -0.1
        self.text_Accuracy3.hide()
        self.text_Accuracy4 = Text(text ='Accuracy', color ='green')
        self.text_Accuracy4.x = -0.5
        self.text_Accuracy4.y = -0.4
        self.text_Accuracy4.hide()
        
        self.canvas.add_item(self.text_result)
        self.canvas.add_item(self.text_timeout)
        self.canvas.add_item(self.text_Accuracy1)
        self.canvas.add_item(self.text_Accuracy2)
        self.canvas.add_item(self.text_Accuracy3)
        self.canvas.add_item(self.text_Accuracy4)

        container.set_widget(self.canvas)


    
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(RESULT_DISPLAY_TIME)
        self.result_timer.timeout.connect(self.finish_trial)
        
        self.trial_timer = Counter(TRIAL_TIMEOUT)
        self.trial_timer.timeout.connect(self.trial_timeout)
    
   
    def run_trial(self, trial):
        '''
        Reset the interface, set the target grip, and show the target
        
        '''
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.target_grip = trial.attrs['target_grip']
        eval("self.target"+self.target_grip+".show()") 
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        '''if a grip is selected, show the target grip and the selected grip'''
        if self.previous_grip == 0:
            if int(self.grip) != 0:
                self.trial.attrs['mav1'] = str(float(data[0,0]))
                self.trial.attrs['mav2'] = str(float(data[1,0]))
                self.trial.attrs['selected_grip'] = str(int(self.grip))
                try:
                    self.trial.attrs['path_eff'] = str(float(data[5,0]))
                except IndexError:
                    pass
                
                '''çounter for the accuracy'''
                exec("self.num_trial"+str(self.target_grip)+" = self.num_trial"+str(self.target_grip)+" + 1") 
                # self.num_trial = self.num_trial + 1
                if int(self.grip) == int(self.target_grip):
                    exec("self.num_correct"+str(self.target_grip)+"= self.num_correct"+str(self.target_grip)+"+ 1") 
                    # self.num_correct = self.num_correct + 1
                    self.text_result.qitem.setText('Correct')
                    self.text_result.qitem.setBrush(QColor('green'))
                else:
                    self.text_result.qitem.setText('Incorrect')
                    self.text_result.qitem.setBrush(QColor('red'))
                
                self.show_result()
        
        self.previous_grip = int(self.grip)
        self.trial_timer.increment()
            
                       
    def show_result(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_result.show()
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.connect(self.daqstream.updated, self.result_display)
        
    def trial_timeout(self):
        # self.num_trial1 = self.num_trial1 + 1
        exec("self.num_trial"+str(self.target_grip)+" = self.num_trial"+str(self.target_grip)+"+ 1") 
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_timeout.show()
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.connect(self.daqstream.updated, self.result_display)
        
        
    def result_display(self,data):
        self.result_timer.increment()
        
    
    def finish_trial(self):
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.result_display)
        self._reset()
        self.next_trial()    
        


    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.text_result.hide()
        self.text_timeout.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background4.show()
        self.background5.show()
        self.cursor.show()
        self.result_timer.reset()
        self.trial_timer.reset()
        

       
    def finish(self):
        
        self.daqstream.stop()
        self.accuracy1 =self.num_correct1/self.num_trial1
        self.accuracy2 =self.num_correct2/self.num_trial2
        self.accuracy3 =self.num_correct3/self.num_trial3
        self.accuracy4 =self.num_correct4/self.num_trial4
        self.text_Accuracy1.qitem.setText('Taks1 Accuracy: ' + str(self.accuracy1))
        self.text_Accuracy1.show()
        self.text_Accuracy2.qitem.setText('Taks2 Accuracy: ' + str(self.accuracy2))
        self.text_Accuracy2.show()
        self.text_Accuracy3.qitem.setText('Taks3 Accuracy: ' + str(self.accuracy3))
        self.text_Accuracy3.show()
        self.text_Accuracy4.qitem.setText('Taks4 Accuracy: ' + str(self.accuracy4))
        self.text_Accuracy4.show()
        

        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_result.hide()
        

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t


class ACTestInv(Task):
    
    def __init__(self, pipeline):
        super(ACTestInv, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.num_trial1 = 0.0
        self.num_trial2 = 0.0
        self.num_trial3 = 0.0
        self.num_trial4 = 0.0
        self.num_correct1 = 0.0
        self.num_correct2 = 0.0
        self.num_correct3 = 0.0
        self.num_correct4 = 0.0
      
    def prepare_design(self, design):
        num_grip = TRIAL_PER_GRIP #the number of each grip in each block
        # num_grip = 1
        t1 = np.ones(num_grip)
        t2 = 2*np.ones(num_grip)
        t3 = 3*np.ones(num_grip)
        t4 = 4*np.ones(num_grip)
        target_grip =np.concatenate((t1,t2,t3,t4)) 
        target_grip = target_grip.astype(int)
        block = design.add_block()
        for grip in target_grip:
            block.add_trial(attrs={
                                'target_grip': str(grip),
                                'mav1':str(0),
                                'mav2':str(0),
                                'selected_grip': str(0),
                                'path_eff':str(0)
                            })   
        block.shuffle()
        
        
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_AC_Inv'+ t)
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6)
        self.background4 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background4)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target4 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        self.canvas.add_item(self.target4)
         
        '''result interface'''
        self.text_result = Text(text ='default', color ='green')
        self.text_result.x = -1.2
        self.text_result.y = 1.0
        self.text_result.hide()
        self.text_timeout = Text(text ='Timeout', color ='#f1f505')
        self.text_timeout.hide()
        
        self.text_Accuracy1 = Text(text ='Accuracy', color ='green')
        self.text_Accuracy1.x = -0.5
        self.text_Accuracy1.y = 0.5
        self.text_Accuracy1.hide()
        self.text_Accuracy2 = Text(text ='Accuracy', color ='green')
        self.text_Accuracy2.x = -0.5
        self.text_Accuracy2.y = 0.2
        self.text_Accuracy2.hide()
        self.text_Accuracy3 = Text(text ='Accuracy', color ='green')
        self.text_Accuracy3.x = -0.5
        self.text_Accuracy3.y = -0.1
        self.text_Accuracy3.hide()
        self.text_Accuracy4 = Text(text ='Accuracy', color ='green')
        self.text_Accuracy4.x = -0.5
        self.text_Accuracy4.y = -0.4
        self.text_Accuracy4.hide()
        
        self.canvas.add_item(self.text_result)
        self.canvas.add_item(self.text_timeout)
        self.canvas.add_item(self.text_Accuracy1)
        self.canvas.add_item(self.text_Accuracy2)
        self.canvas.add_item(self.text_Accuracy3)
        self.canvas.add_item(self.text_Accuracy4)

        container.set_widget(self.canvas)


    
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(RESULT_DISPLAY_TIME)
        self.result_timer.timeout.connect(self.finish_trial)
        
        self.trial_timer = Counter(TRIAL_TIMEOUT)
        self.trial_timer.timeout.connect(self.trial_timeout)
    
   
    def run_trial(self, trial):
        '''
        Reset the interface, set the target grip, and show the target
        
        '''
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.target_grip = trial.attrs['target_grip']
        eval("self.target"+self.target_grip+".show()") 
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        '''if a grip is selected, show the target grip and the selected grip'''
        if self.previous_grip == 0:
            if int(self.grip) != 0:
                self.trial.attrs['mav1'] = str(float(data[0,0]))
                self.trial.attrs['mav2'] = str(float(data[1,0]))
                self.trial.attrs['selected_grip'] = str(int(self.grip))
                try:
                    self.trial.attrs['path_eff'] = str(float(data[5,0]))
                except IndexError:
                    pass
                
                '''çounter for the accuracy'''
                exec("self.num_trial"+str(self.target_grip)+" = self.num_trial"+str(self.target_grip)+" + 1") 
                # self.num_trial = self.num_trial + 1
                if int(self.grip) == int(self.target_grip):
                    exec("self.num_correct"+str(self.target_grip)+"= self.num_correct"+str(self.target_grip)+"+ 1") 
                    # self.num_correct = self.num_correct + 1
                    self.text_result.qitem.setText('Correct')
                    self.text_result.qitem.setBrush(QColor('green'))
                else:
                    self.text_result.qitem.setText('Incorrect')
                    self.text_result.qitem.setBrush(QColor('red'))
                
                self.show_result()
        
        self.previous_grip = int(self.grip)
        self.trial_timer.increment()
            
                       
    def show_result(self):
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.text_result.show()
        self.cursor.show()
        self.connect(self.daqstream.updated, self.result_display)
        
    def trial_timeout(self):
        # self.num_trial1 = self.num_trial1 + 1
        exec("self.num_trial"+str(self.target_grip)+" = self.num_trial"+str(self.target_grip)+"+ 1") 
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_timeout.show()
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.connect(self.daqstream.updated, self.result_display)
        
        
    def result_display(self,data):
        self.result_timer.increment()
        if self.result_timer.count == RESULT_DISPLAY_TIME/2:
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
            self.target4.hide()
            self.background1.hide()
            self.background2.hide()
            self.background3.hide()
            self.background4.hide()
            self.background5.hide()
            self.cursor.hide()
            self.text_result.hide()
    
    def finish_trial(self):
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.result_display)
        self._reset()
        self.next_trial()    
        


    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.text_result.hide()
        self.text_timeout.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background4.show()
        self.background5.show()
        self.cursor.hide()
        self.result_timer.reset()
        self.trial_timer.reset()
        

       
    def finish(self):
        
        self.daqstream.stop()
        self.accuracy1 =self.num_correct1/self.num_trial1
        self.accuracy2 =self.num_correct2/self.num_trial2
        self.accuracy3 =self.num_correct3/self.num_trial3
        self.accuracy4 =self.num_correct4/self.num_trial4
        self.text_Accuracy1.qitem.setText('Taks1 Accuracy: ' + str(self.accuracy1))
        self.text_Accuracy1.show()
        self.text_Accuracy2.qitem.setText('Taks2 Accuracy: ' + str(self.accuracy2))
        self.text_Accuracy2.show()
        self.text_Accuracy3.qitem.setText('Taks3 Accuracy: ' + str(self.accuracy3))
        self.text_Accuracy3.show()
        self.text_Accuracy4.qitem.setText('Taks4 Accuracy: ' + str(self.accuracy4))
        self.text_Accuracy4.show()
        

        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_result.hide()
        

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t


    
class ACPickNPlaceRecording1(Task):
    
    def __init__(self, pipeline):
        super(ACPickNPlaceRecording1, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.new_trial_flag = False
      
    def prepare_design(self, design):
        for test in range(NUM_PNP_BLOCKS):
            block = design.add_block()
            block.add_trial(attrs={
                                'time': 0
                })
            
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_AC_PickNPlace1_'+ t)
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6)
        self.background4 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background4)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target4 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        self.canvas.add_item(self.target4)
        

        '''result interface'''
        self.text_trial = Text(text ='Trial finished', color ='#f1f505')
        self.text_trial.hide()
        self.text_trial.x = -0.35
        self.text_exp = Text(text ='Experiment finished', color ='#f1f505')
        self.text_exp.hide() 
        self.text_exp.x = -0.4
        self.canvas.add_item(self.text_trial)
        self.canvas.add_item(self.text_exp)
        
        container.set_widget(self.canvas)


    
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        
    
   
    def run_trial(self, trial):
        self.new_trial_flag = True
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.Tstart = time.time()
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        
        if (self.previous_grip == 0) and (grip != 0):
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
            self.target4.hide()
                
        self.previous_grip = int(self.grip)
        
        
    
    def finish_trial(self):
        self.Tend = time.time()
        trial_time = self.Tend - self.Tstart
        self.trial.attrs['time'] = trial_time
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.qitem.setText('Trial ' + str(self.trial.attrs['block'])+ ' finished')
        self.text_trial.show()
        
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.next_trial()    
        


    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background4.show()
        self.background5.show()
        self.cursor.show()
        self.text_trial.hide()
        

       
    def finish(self):
        
        self.daqstream.stop()
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.hide()
        self.text_exp.show()
        

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        elif key == util.key_space:
            if self.new_trial_flag: #prevent repeatative data recording
                self.finish_trial()
                self.new_trial_flag = False
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t

class ACPickNPlaceRecording2(Task):
    
    def __init__(self, pipeline):
        super(ACPickNPlaceRecording2, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.new_trial_flag = False
      
    def prepare_design(self, design):
        for test in range(NUM_PNP_BLOCKS):
            block = design.add_block()
            block.add_trial(attrs={
                                'time': 0
                })
            
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_AC_PickNPlace2_'+ t)
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6)
        self.background4 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background4)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target4 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        self.canvas.add_item(self.target4)
        

        '''result interface'''
        self.text_trial = Text(text ='Trial finished', color ='#f1f505')
        self.text_trial.hide()
        self.text_trial.x = -0.35
        self.text_exp = Text(text ='Experiment finished', color ='#f1f505')
        self.text_exp.hide() 
        self.text_exp.x = -0.4
        self.canvas.add_item(self.text_trial)
        self.canvas.add_item(self.text_exp)
        
        container.set_widget(self.canvas)


    
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        
    
   
    def run_trial(self, trial):
        self.new_trial_flag = True
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.Tstart = time.time()
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        
        if (self.previous_grip == 0) and (grip != 0):
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
            self.target4.hide()
                
        self.previous_grip = int(self.grip)
        
        
    
    def finish_trial(self):
        self.Tend = time.time()
        trial_time = self.Tend - self.Tstart
        self.trial.attrs['time'] = trial_time
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.qitem.setText('Trial ' + str(self.trial.attrs['block'])+ ' finished')
        self.text_trial.show()
        
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.next_trial()    
        


    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background4.show()
        self.background5.show()
        self.cursor.show()
        self.text_trial.hide()
        

       
    def finish(self):
        
        self.daqstream.stop()
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.hide()
        self.text_exp.show()
        

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        elif key == util.key_space:
            if self.new_trial_flag: #prevent repeatative data recording
                self.finish_trial()
                self.new_trial_flag = False
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t

class ACPickNPlaceTrain(Task):
    
    def __init__(self, pipeline):
        super(ACPickNPlaceTrain, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.new_trial_flag = False
      
    def prepare_design(self, design):
        for test in range(NUM_PNP_BLOCKS):
            block = design.add_block()
            block.add_trial(attrs={
                                'time': 0
                })
            
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_AC_PickNPlaceTrain'+ t)
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6)
        self.background4 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background4)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target4 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        self.canvas.add_item(self.target4)
        

        '''result interface'''
        self.text_trial = Text(text ='Trial finished', color ='#f1f505')
        self.text_trial.hide()
        self.text_trial.x = -0.35
        self.text_exp = Text(text ='Experiment finished', color ='#f1f505')
        self.text_exp.hide() 
        self.text_exp.x = -0.4
        self.canvas.add_item(self.text_trial)
        self.canvas.add_item(self.text_exp)
        
        container.set_widget(self.canvas)


    
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        
    
   
    def run_trial(self, trial):
        self.new_trial_flag = True
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.Tstart = time.time()
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        
        if (self.previous_grip == 0) and (grip != 0):
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
            self.target4.hide()
                
        self.previous_grip = int(self.grip)
        
        
    
    def finish_trial(self):
        self.Tend = time.time()
        trial_time = self.Tend - self.Tstart
        self.trial.attrs['time'] = trial_time
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.qitem.setText('Trial ' + str(self.trial.attrs['block'])+ ' finished')
        self.text_trial.show()
        
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.next_trial()    
        


    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background4.show()
        self.background5.show()
        self.cursor.show()
        self.text_trial.hide()
        

       
    def finish(self):
        
        self.daqstream.stop()
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.hide()
        self.text_exp.show()
        

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        elif key == util.key_space:
            if self.new_trial_flag: #prevent repeatative data recording
                self.finish_trial()
                self.new_trial_flag = False
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t


class ACBoxNBlocksRecording(Task):
    
    def __init__(self, pipeline):
        super(ACBoxNBlocksRecording, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.num_trial = 0.0
        self.num_correct = 0.0
      
    def prepare_design(self, design):
        for test in range(NUM_BNB_BLOCKS):
            block = design.add_block()
            block.add_trial(attrs={
                                'block':str(test)
                })
            
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_AC_BoxNBlocks'+ t)
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6)
        self.background4 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background4)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=22.5,rotation=90, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target4 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        self.canvas.add_item(self.target4)
        

        '''result interface'''
        self.text_trial = Text(text ='Trial finished', color ='#f1f505')
        self.text_trial.hide()
        self.text_trial.x = -0.35
        self.text_exp = Text(text ='Experiment finished', color ='#f1f505')
        self.text_exp.hide() 
        self.text_exp.x = -0.4
        self.canvas.add_item(self.text_trial)
        self.canvas.add_item(self.text_exp)
        
        container.set_widget(self.canvas)


    
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(50*60)
        self.result_timer.timeout.connect(self.finish_trial)
    
   
    def run_trial(self, trial):
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        
        if (self.previous_grip == 0) and (grip != 0):
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
            self.target4.hide()
                
        self.previous_grip = grip
        self.result_timer.increment()
        
        
    
    def finish_trial(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.qitem.setText('Trial ' + str(self.trial.attrs['block'])+ ' finished')
        self.text_trial.show()
        
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.next_trial()    
        


    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background4.show()
        self.background5.show()
        self.cursor.show()
        self.text_trial.hide()
        self.result_timer.reset()
        

       
    def finish(self):
        
        self.daqstream.stop()
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.target4.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background4.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.hide()
        self.text_exp.show()
        

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t

class DCTrainingVisible(Task):
    def __init__(self, pipeline):
        super(DCTrainingVisible, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        # self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)

        container.set_widget(self.canvas)    
        
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(TRAINING_TIME)
        self.result_timer.timeout.connect(self.finish)
        
    def run(self):
        self.pipeline.clear()
        self.connect(self.daqstream.updated, self.update)
        
    def update(self, data):
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        if (grip == 3):
            grip = 2
        elif (grip == 4):
            grip = 3
        
        if (self.previous_grip == 0) and (grip != 0):
            # self.cursor.show()
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            # self.cursor.hide()
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
                
        self.previous_grip = grip
        self.result_timer.increment()
        
    def finish(self):
        self.daqstream.stop()

        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)

class DCTrainingInv(Task):
    def __init__(self, pipeline):
        super(DCTrainingInv, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)

        container.set_widget(self.canvas)    
        
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(TRAINING_TIME) 
        self.result_timer.timeout.connect(self.finish)
        
    def run(self):
        self.pipeline.clear()
        self.connect(self.daqstream.updated, self.update)
        
    def update(self, data):
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        if (grip == 3):
            grip = 2
        elif (grip == 4):
            grip = 3
        
        if (self.previous_grip == 0) and (grip != 0):
            self.cursor.show()
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.cursor.hide()
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
                
        self.previous_grip = grip
        self.result_timer.increment()
        
    def finish(self):
        self.daqstream.stop()

        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)


class DCTestVisible(Task):
    
    def __init__(self, pipeline):
        super(DCTestVisible, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.num_trial = 0.0
        self.num_correct = 0.0
      
    def prepare_design(self, design):
        num_grip = TRIAL_PER_GRIP #the number of each grip in each block
        t1 = np.ones(num_grip)
        t2 = 2*np.ones(num_grip)
        t3 = 3*np.ones(num_grip)
        target_grip =np.concatenate((t1,t2,t3)) 
        target_grip = target_grip.astype(int)
        block = design.add_block()
        for grip in target_grip:
            block.add_trial(attrs={
                                'target_grip': str(grip),
                                'mav1':str(0),
                                'mav2':str(0),
                                'selected_grip': str(0),
                                'path_eff':str(0)
                            })   
        block.shuffle()
        
        
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_DC_Visible'+ t)
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        # self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
         
        '''result interface'''
        self.text_result = Text(text ='default', color ='green')
        self.text_result.x = -0.2
        self.text_result.hide()
        self.text_timeout = Text(text ='Timeout', color ='red')
        self.text_timeout.hide()
        self.text_endTrial = Text(text ='Accuracy', color ='yellow')
        self.text_endTrial.x = -0.3
        self.text_endTrial.hide()
        self.canvas.add_item(self.text_result)
        self.canvas.add_item(self.text_timeout)
        self.canvas.add_item(self.text_endTrial)

        container.set_widget(self.canvas)

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(RESULT_DISPLAY_TIME)
        self.result_timer.timeout.connect(self.finish_trial)
        
        self.trial_timer = Counter(TRIAL_TIMEOUT)
        self.trial_timer.timeout.connect(self.trial_timeout)
        
    def run_trial(self, trial):
        '''
        Reset the interface, set the target grip, and show the target
        
        '''
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.target_grip = trial.attrs['target_grip']
        eval("self.target"+self.target_grip+".show()") 
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        '''map the control state to the target number'''
        grip = int(self.grip)
        if (grip == 3):
            grip =2
        elif (grip ==4):
            grip = 3
            
        '''if a grip is selected, show the target grip and the selected grip'''
        if self.previous_grip == 0:
            if int(self.grip) != 0:
                self.trial.attrs['mav1'] = str(float(data[0,0]))
                self.trial.attrs['mav2'] = str(float(data[1,0]))
                self.trial.attrs['selected_grip'] = str(int(grip))
                try:
                    self.trial.attrs['path_eff'] = str(float(data[5,0]))
                except IndexError:
                    pass
                
                '''çounter for the accuracy'''
                self.num_trial = self.num_trial + 1
                if grip == int(self.target_grip):
                    self.num_correct = self.num_correct + 1
                    self.text_result.qitem.setText('Correct')
                    self.text_result.qitem.setBrush(QColor('green'))
                else:
                    self.text_result.qitem.setText('Incorrect')
                    self.text_result.qitem.setBrush(QColor('red'))
                
                self.show_result()
        
        self.previous_grip = grip
        self.trial_timer.increment()
        
    def show_result(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_result.show()
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.connect(self.daqstream.updated, self.result_display)
        
    def trial_timeout(self):
        self.num_trial = self.num_trial + 1
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_timeout.show()
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.connect(self.daqstream.updated, self.result_display)
        
    def result_display(self,data):
        self.result_timer.increment()
        
    
    def finish_trial(self):
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.result_display)
        self._reset()
        self.next_trial()    
        
    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.text_result.hide()
        self.text_timeout.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background5.show()
        self.cursor.show()
        self.result_timer.reset()
        self.trial_timer.reset()
        
    def finish(self):
        
        self.daqstream.stop()
        self.accuracy =self.num_correct/self.num_trial
        self.text_endTrial.qitem.setText('Accuracy: ' + str(self.accuracy))
        self.text_endTrial.show()
        

        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_result.hide()
        

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t

class DCTestInv(Task):
    
    def __init__(self, pipeline):
        super(DCTestInv, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.num_trial = 0.0
        self.num_correct = 0.0
      
    def prepare_design(self, design):
        num_grip = TRIAL_PER_GRIP #the number of each grip in each block
        t1 = np.ones(num_grip)
        t2 = 2*np.ones(num_grip)
        t3 = 3*np.ones(num_grip)
        target_grip =np.concatenate((t1,t2,t3)) 
        target_grip = target_grip.astype(int)
        block = design.add_block()
        for grip in target_grip:
            block.add_trial(attrs={
                                'target_grip': str(grip),
                                'mav1':str(0),
                                'mav2':str(0),
                                'selected_grip': str(0),
                                'path_eff':str(0)
                            })   
        block.shuffle()
        
        
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_DC_Inv'+ t)
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background5)

        
        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
         
        '''result interface'''
        self.text_result = Text(text ='default', color ='green')
        self.text_result.x = -1.2
        self.text_result.y = 1.0
        self.text_result.hide()
        self.text_timeout = Text(text ='Timeout', color ='#f1f505')
        self.text_timeout.hide()
        self.text_endTrial = Text(text ='Accuracy', color ='yellow')
        self.text_endTrial.x = -0.3
        self.text_endTrial.hide()
        self.canvas.add_item(self.text_result)
        self.canvas.add_item(self.text_timeout)
        self.canvas.add_item(self.text_endTrial)

        container.set_widget(self.canvas)

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(RESULT_DISPLAY_TIME)
        self.result_timer.timeout.connect(self.finish_trial)
        
        self.trial_timer = Counter(TRIAL_TIMEOUT)
        self.trial_timer.timeout.connect(self.trial_timeout)
        
    def run_trial(self, trial):
        '''
        Reset the interface, set the target grip, and show the target
        
        '''
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.target_grip = trial.attrs['target_grip']
        eval("self.target"+self.target_grip+".show()") 
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        '''if a grip is selected, show the target grip and the selected grip'''
        grip = int(self.grip)
        if (grip == 3):
            grip =2
        elif (grip ==4):
            grip = 3
        
        if self.previous_grip == 0:
            if int(self.grip) != 0:
                self.trial.attrs['mav1'] = str(float(data[0,0]))
                self.trial.attrs['mav2'] = str(float(data[1,0]))
                self.trial.attrs['selected_grip'] = str(int(grip))
                try:
                    self.trial.attrs['path_eff'] = str(float(data[5,0]))
                except IndexError:
                    pass
                
                '''çounter for the accuracy'''
                self.num_trial = self.num_trial + 1
                if grip == int(self.target_grip):
                    self.num_correct = self.num_correct + 1
                    self.text_result.qitem.setText('Correct')
                    self.text_result.qitem.setBrush(QColor('green'))
                else:
                    self.text_result.qitem.setText('Incorrect')
                    self.text_result.qitem.setBrush(QColor('red'))

                
                self.show_result()
        
        self.previous_grip = grip
        self.trial_timer.increment()
        
    def show_result(self):
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.cursor.show()
        self.text_result.show()
        self.connect(self.daqstream.updated, self.result_display)
        
    def trial_timeout(self):
        self.num_trial = self.num_trial + 1
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_timeout.show()
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.connect(self.daqstream.updated, self.result_display)
        
    def result_display(self,data):
        self.result_timer.increment()
        if self.result_timer.count == RESULT_DISPLAY_TIME/2:
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
            self.background1.hide()
            self.background2.hide()
            self.background3.hide()
            self.background5.hide()
            self.cursor.hide()
            self.text_result.hide()
        
    
    def finish_trial(self):
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.result_display)
        self._reset()
        self.next_trial()    
        
    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.text_result.hide()
        self.text_timeout.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background5.show()
        self.cursor.hide()
        self.result_timer.reset()
        self.trial_timer.reset()
        
    def finish(self):
        
        self.daqstream.stop()
        self.accuracy =self.num_correct/self.num_trial
        self.text_endTrial.qitem.setText('Accuracy: ' + str(self.accuracy))
        self.text_endTrial.show()
        

        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_result.hide()
        

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t
    
class DCPickNPlaceRecording1(Task):
    
    def __init__(self, pipeline):
        super(DCPickNPlaceRecording1, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.new_trial_flag = False
      
    def prepare_design(self, design):
        for test in range(NUM_PNP_BLOCKS):
            block = design.add_block()
            block.add_trial(attrs={
                                'time': 0
                })
            
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_DC_PickNPlace1_'+ t)    
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background5)

        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        # self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        
        '''result interface'''
        self.text_trial = Text(text ='Trial finished', color ='#f1f505')
        self.text_trial.hide()
        self.text_trial.x = -0.35
        self.text_exp = Text(text ='Experiment finished', color ='#f1f505')
        self.text_exp.hide() 
        self.text_exp.x = -0.4
        self.canvas.add_item(self.text_trial)
        self.canvas.add_item(self.text_exp)
        
        container.set_widget(self.canvas)
        
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
    
   
    def run_trial(self, trial):
        self.new_trial_flag = True
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.Tstart = time.time()
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        if (grip == 3):
            grip =2
        elif (grip ==4):
            grip = 3
        
        if (self.previous_grip == 0) and (grip != 0):
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
                
        self.previous_grip = grip
        
    def finish_trial(self):
        self.Tend = time.time()
        trial_time = self.Tend - self.Tstart
        self.trial.attrs['time'] = trial_time
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.qitem.setText('Trial ' + str(self.trial.attrs['block'])+ ' finished')
        self.text_trial.show()
        
        
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.next_trial()  
        
    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background5.show()
        self.cursor.show()
        self.text_trial.hide()
       
    def finish(self):
        
        self.daqstream.stop()
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.hide()
        self.text_exp.show()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        elif key == util.key_space:
            if self.new_trial_flag: #prevent repeatative data recording
                self.finish_trial()
                self.new_trial_flag = False
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t   


class DCPickNPlaceRecording2(Task):
    
    def __init__(self, pipeline):
        super(DCPickNPlaceRecording2, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.new_trial_flag = False
      
    def prepare_design(self, design):
        for test in range(NUM_PNP_BLOCKS):
            block = design.add_block()
            block.add_trial(attrs={
                                'time': 0
                })
            
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_DC_PickNPlace2_'+ t)    
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background5)

        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        # self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        
        '''result interface'''
        self.text_trial = Text(text ='Trial finished', color ='#f1f505')
        self.text_trial.hide()
        self.text_trial.x = -0.35
        self.text_exp = Text(text ='Experiment finished', color ='#f1f505')
        self.text_exp.hide() 
        self.text_exp.x = -0.4
        self.canvas.add_item(self.text_trial)
        self.canvas.add_item(self.text_exp)
        
        container.set_widget(self.canvas)
        
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
    
   
    def run_trial(self, trial):
        self.new_trial_flag = True
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.Tstart = time.time()
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        if (grip == 3):
            grip =2
        elif (grip ==4):
            grip = 3
        
        if (self.previous_grip == 0) and (grip != 0):
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
                
        self.previous_grip = grip
        
    def finish_trial(self):
        self.Tend = time.time()
        trial_time = self.Tend - self.Tstart
        self.trial.attrs['time'] = trial_time
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.qitem.setText('Trial ' + str(self.trial.attrs['block'])+ ' finished')
        self.text_trial.show()
        
        
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.next_trial()  
        
    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background5.show()
        self.cursor.show()
        self.text_trial.hide()
       
    def finish(self):
        
        self.daqstream.stop()
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.hide()
        self.text_exp.show()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        elif key == util.key_space:
            if self.new_trial_flag: #prevent repeatative data recording
                self.finish_trial()
                self.new_trial_flag = False
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t   
    
class DCPickNPlaceTrain(Task):
    
    def __init__(self, pipeline):
        super(DCPickNPlaceTrain, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
        self.new_trial_flag = False
      
    def prepare_design(self, design):
        for test in range(NUM_PNP_BLOCKS):
            block = design.add_block()
            block.add_trial(attrs={
                                'time': 0
                })
            
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_DC_PickNPlaceTrain'+ t)    
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background5)

        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        # self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        
        '''result interface'''
        self.text_trial = Text(text ='Trial finished', color ='#f1f505')
        self.text_trial.hide()
        self.text_trial.x = -0.35
        self.text_exp = Text(text ='Experiment finished', color ='#f1f505')
        self.text_exp.hide() 
        self.text_exp.x = -0.4
        self.canvas.add_item(self.text_trial)
        self.canvas.add_item(self.text_exp)
        
        container.set_widget(self.canvas)
        
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
    
   
    def run_trial(self, trial):
        self.new_trial_flag = True
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.Tstart = time.time()
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        if (grip == 3):
            grip =2
        elif (grip ==4):
            grip = 3
        
        if (self.previous_grip == 0) and (grip != 0):
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
                
        self.previous_grip = grip
        
    def finish_trial(self):
        self.Tend = time.time()
        trial_time = self.Tend - self.Tstart
        self.trial.attrs['time'] = trial_time
        
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.qitem.setText('Trial ' + str(self.trial.attrs['block'])+ ' finished')
        self.text_trial.show()
        
        
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.next_trial()  
        
    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background5.show()
        self.cursor.show()
        self.text_trial.hide()
       
    def finish(self):
        
        self.daqstream.stop()
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.hide()
        self.text_exp.show()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        elif key == util.key_space:
            if self.new_trial_flag: #prevent repeatative data recording
                self.finish_trial()
                self.new_trial_flag = False
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t  

    
class DCBoxNBlocksRecording(Task):
    
    def __init__(self, pipeline):
        super(DCBoxNBlocksRecording, self).__init__()
        self.pipeline = pipeline
        
        self.previous_grip = 1
      
    def prepare_design(self, design):
        for test in range(NUM_BNB_BLOCKS):
            block = design.add_block()
            block.add_trial(attrs={
                                'block':str(test)
                })
            
    def prepare_storage(self, storage):
        t = self.read_time()
        self.writer = storage.create_task(storage.subject_id+'_DC_BoxNBlocks'+ t)    
        
    def prepare_graphics(self, container):
        origin=(0,-1)

        '''build the background'''
        self.canvas = Canvas(draw_border=False, bg_color='k')
        self.background1 = Basket(xy_origin=origin, size=0.6)
        self.background2 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6)
        self.background3 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6)
        self.background5 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6)
        self.canvas.add_item(self.background1)
        self.canvas.add_item(self.background2)
        self.canvas.add_item(self.background3)
        self.canvas.add_item(self.background5)

        '''build the cursor and target'''       
        self.cursor = Circle(CURSOR_SIZE, color='red')
        # self.cursor.hide()
        self.target1 = Target(xy_origin=origin,theta_target=22.5,rotation=112.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target2 = Target(xy_origin=origin,theta_target=45,rotation=67.5, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target3 = Target(xy_origin=origin,theta_target=22.5,rotation=45, r1=2, r2=0.6,linewidth=0.03,color='yellow')
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.canvas.add_item(self.cursor)
        self.canvas.add_item(self.target1)
        self.canvas.add_item(self.target2)
        self.canvas.add_item(self.target3)
        
        '''result interface'''
        self.text_trial = Text(text ='Trial finished', color ='#f1f505')
        self.text_trial.hide()
        self.text_trial.x = -0.35
        self.text_exp = Text(text ='Experiment finished', color ='#f1f505')
        self.text_exp.hide() 
        self.text_exp.x = -0.4
        self.canvas.add_item(self.text_trial)
        self.canvas.add_item(self.text_exp)
        
        container.set_widget(self.canvas)
        
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.result_timer = Counter(50*60)
        self.result_timer.timeout.connect(self.finish_trial)
    
   
    def run_trial(self, trial):
        self._reset()
        trial.add_array('data_Arduino', stack_axis=1)
        self.pipeline.clear()        
        self.connect(self.daqstream.updated, self.cursor_following)
        
    def cursor_following(self, data):
        self.trial.arrays['data_Arduino'].stack(data)
        self.pos_x,self.pos_y,self.grip = self.pipeline.process(data)
        self.cursor.pos = ((self.pos_x,self.pos_y))
        
        grip = int(self.grip)
        if (grip == 3):
            grip =2
        elif (grip ==4):
            grip = 3
        
        if (self.previous_grip == 0) and (grip != 0):
            eval("self.target"+str(grip)+".show()") 
        elif (self.previous_grip != 0) and (grip == 0):
            self.target1.hide()
            self.target2.hide()
            self.target3.hide()
                
        self.previous_grip = grip
        self.result_timer.increment()
        
    def finish_trial(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.qitem.setText('Trial ' + str(self.trial.attrs['block'])+ ' finished')
        self.text_trial.show()
        
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.cursor_following)
        self.next_trial()  
        
    def _reset(self):
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.show()
        self.background2.show()
        self.background3.show()
        self.background5.show()
        self.cursor.show()
        self.text_trial.hide()
        self.result_timer.reset()
       
    def finish(self):
        
        self.daqstream.stop()
        self.target1.hide()
        self.target2.hide()
        self.target3.hide()
        self.background1.hide()
        self.background2.hide()
        self.background3.hide()
        self.background5.hide()
        self.cursor.hide()
        self.text_trial.hide()
        self.text_exp.show()
        

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)
              
            
    def read_time(self):
        current_time = datetime.datetime.now()
        t = current_time.strftime("%Y%m%d%H%M%S")
        return t

'''Module to visualize the MAV during calibration'''
class SYSCalibration(Task):
    def __init__(self):
        super(SYSCalibration, self).__init__()
        self.pipeline = self.make_pipeline()
        
    def make_pipeline(self):
        print('Pipeline calib ok...')
        pipeline = Pipeline([
            Windower(int(RAW_S_RATE * WIN_SIZE))])
        return pipeline
    
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.timer = Counter(RAW_S_RATE/CAL_SAMPLE_SIZE*8)
        self.timer.timeout.connect(self.finish)
    
    def prepare_graphics(self, container):
        self.scope = CalibrationWidget(channel_names)
        
    def run(self):
        self.pipeline.clear()
        self.connect(self.daqstream.updated, self.update)

    def update(self, data):
        data_raw = self.pipeline.process(data)
        self.scope.plot(data_raw)
        self.timer.increment()
        
    def key_press(self, key):
        super(self).key_press(key)
        if key == util.key_escape:
            self.finish()
                    
    def finish(self):
        print('Pipeline calib finished')
        # self.scope._close_channels()
        self.disconnect(self.daqstream.updated, self.update)
        self.daqstream.stop()
        # self.finished.emit()

        
class CalibValidation(Task):
    def __init__(self):
        super(CalibValidation, self).__init__()
        self.pipeline = self.make_pipeline()
        
    def make_pipeline(self):
        print('Pipeline visual ok...')
        pipeline = Pipeline([
            Windower(int(RAW_S_RATE * VAL_WIN_SIZE))])
        return pipeline
    
    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        
        self.timer = Counter(RAW_S_RATE/CAL_SAMPLE_SIZE*30)
        self.timer.timeout.connect(self.finish)
    
    def prepare_graphics(self, container):
        self.scope = ValidationWidget(channel_names)
        
    def run(self):
        self.pipeline.clear()
        self.connect(self.daqstream.updated, self.update)

    def update(self, data):
        data_raw = self.pipeline.process(data)
        self.scope.plot(data_raw)
        self.timer.increment()
        
    def key_press(self, key):
        super(self).key_press(key)
        if key == util.key_escape:
            self.finish()
                    
    def finish(self):
        print('Pipeline visual finished')
        # self.scope._close_channels()
        self.disconnect(self.daqstream.updated, self.update)
        self.daqstream.stop()
        # self.finished.emit()
            

        
      

      
if __name__ == '__main__':
    parser = ArgumentParser()
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument('--ACtrainVisible', action='store_true')
    task.add_argument('--ACtrainInv', action='store_true')
    task.add_argument('--ACtestVisible', action='store_true')
    task.add_argument('--ACtestInv', action='store_true')
    task.add_argument('--ACPNPTrain', action='store_true')
    task.add_argument('--ACPNP1', action='store_true')
    task.add_argument('--ACPNP2', action='store_true')
    task.add_argument('--ACBNB', action='store_true')
    task.add_argument('--DCtrainVisible', action='store_true')
    task.add_argument('--DCtrainInv', action='store_true')
    task.add_argument('--DCtestVisible', action='store_true')
    task.add_argument('--DCtestInv', action='store_true')
    task.add_argument('--DCPNPTrain', action='store_true')
    task.add_argument('--DCPNP1', action='store_true')
    task.add_argument('--DCPNP2', action='store_true')
    task.add_argument('--DCBNB', action='store_true')
    task.add_argument('--Calibration', action='store_true')
    task.add_argument('--CalibrationLow', action='store_true')
    task.add_argument('--Validation', action='store_true')
    task.add_argument('--SetACtrl', action='store_true')
    task.add_argument('--SetDCtrl', action='store_true')
    task.add_argument('--SetLDACtrl', action='store_true')
    task.add_argument('--ReadCalibration', action='store_true')
    args = parser.parse_args()
    
    
    cp = ConfigParser()
    cp.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'config.ini'))
    CURSOR_SIZE = cp.getfloat('graphic', 'cursor_size')
    TRAINING_TIME = cp.getint('training', 'training_time')
    TRIAL_PER_GRIP = cp.getint('test','trial_per_grip')
    RESULT_DISPLAY_TIME = cp.getint('test','result_display_time')
    TRIAL_TIMEOUT = cp.getint('test','trial_timeout')
    NUM_PNP_BLOCKS = cp.getint('test','num_pnp_blocks')
    NUM_BNB_BLOCKS = cp.getint('test','num_bnb_blocks')
    S_RATE = cp.getint('calibration','sample_rate')
    RAW_S_RATE = cp.getint('calibration','raw_sample_rate')
    WIN_SIZE = cp.getint('calibration','window_size')
    VAL_WIN_SIZE = cp.getint('calibration','val_window_size')
    CAL_SAMPLE_SIZE = cp.getint('calibration','cal_sample_per_read')
    SUBJECT_NAME = cp['setting']['subject_name']
    
    
    n_channels = 2
    channel_names = ['EMG ' + str(i) for i in range(1, n_channels+1)]    
    

    """load DAQ"""
    daq = ArduinoMKR_DAQ(samples_per_read=1)
    """calculate the dictionary to map MAV to the MCI"""
    m=MCI_Mapping_Matrix(origin= (0,-1),length= 2)
    [x_dic,y_dic] = m.mapping_matrix()
    PEMG_pipeline=pipeline.Pipeline([
    MCI_Mapping(x_dic,y_dic)
    ])

    exp = Experiment(daq=daq, subject=SUBJECT_NAME)
    if args.ACtrainVisible:
        exp.run(ACTrainingVisible(PEMG_pipeline))
    elif args.ACtrainInv:
        exp.run(ACTrainingInv(PEMG_pipeline))
    elif args.ACtestVisible:
        exp.run(ACTestVisible(PEMG_pipeline))
    elif args.ACtestInv:
        exp.run(ACTestInv(PEMG_pipeline))
    elif args.ACPNPTrain:
        exp.run(ACPickNPlaceTrain(PEMG_pipeline))
    elif args.ACPNP1:
        exp.run(ACPickNPlaceRecording1(PEMG_pipeline))
    elif args.ACPNP2:
        exp.run(ACPickNPlaceRecording2(PEMG_pipeline))
    elif args.ACBNB:
        exp.run(ACBoxNBlocksRecording(PEMG_pipeline))
    elif args.DCtrainVisible:
        exp.run(DCTrainingVisible(PEMG_pipeline))
    elif args.DCtrainInv:
        exp.run(DCTrainingInv(PEMG_pipeline))       
    elif args.DCtestVisible:
        exp.run(DCTestVisible(PEMG_pipeline))
    elif args.DCtestInv:
        exp.run(DCTestInv(PEMG_pipeline))
    elif args.DCPNPTrain:
        exp.run(DCPickNPlaceTrain(PEMG_pipeline))
    elif args.DCPNP1:
        exp.run(DCPickNPlaceRecording1(PEMG_pipeline))
    elif args.DCPNP2:
        exp.run(DCPickNPlaceRecording2(PEMG_pipeline))
    elif args.DCBNB:
        exp.run(DCBoxNBlocksRecording(PEMG_pipeline)) 
    elif args.Calibration:
        daq = ArduinoMKR_DAQ(samples_per_read = CAL_SAMPLE_SIZE,rate = RAW_S_RATE, mode = 'calibration')
        exp = Experiment(daq=daq, subject=SUBJECT_NAME)
        exp.run(SYSCalibration())
    elif args.CalibrationLow:
        daq = ArduinoMKR_DAQ(samples_per_read = CAL_SAMPLE_SIZE,rate = RAW_S_RATE, mode = 'calibration_low')
        exp = Experiment(daq=daq, subject=SUBJECT_NAME)
        exp.run(SYSCalibration())
    elif args.Validation:
        daq = ArduinoMKR_DAQ(samples_per_read = CAL_SAMPLE_SIZE,rate = RAW_S_RATE, mode = 'visualization')
        exp = Experiment(daq=daq, subject=SUBJECT_NAME)
        exp.run(CalibValidation())
    elif args.SetACtrl:
        daq = ArduinoMKR_DAQ(ctrl = 'abstract_ctrl')
        daq.setArduino()
    elif args.SetDCtrl:
        daq = ArduinoMKR_DAQ(ctrl = 'direct_ctrl')
        daq.setArduino()
    elif args.SetLDACtrl:
        daq = ArduinoMKR_DAQ(ctrl = 'LDA_ctrl')
        daq.setArduino()
    elif args.ReadCalibration:
        cal_data = daq.readCalibration()
        print(cal_data)
        
        cal_path = os.path.dirname(os.path.realpath(__file__))
        now = datetime.datetime.now()
        timelabel = now.strftime("%Y%m%d%H%M%S")
        cal_file = cal_path + "\data\\" + SUBJECT_NAME + "\calibration"+timelabel+".txt"
        

        text_file = open(cal_file, "w")
        text_file.write(cal_data)
        text_file.close()