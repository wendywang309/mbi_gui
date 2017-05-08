# -*- coding: utf-8 -*-
"""
Created on Tue May 02 13:28:45 2017

@author: wendy
"""
from __future__ import with_statement
import sys
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from FrontPanelAPI import ok
import os  # For listing directory methods
import csv
import time
import numpy as np
import matplotlib.image as mpimg




qtDesignerFile = "MBI_GUI.ui" 
#taken from sample code from Opal Kelly:
dev = ok.okCFrontPanel() #device
        
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtDesignerFile)

bitfile = ""
pattfile = ""

def showFrame(imgplot,histplot, frameData, DispFrame, figure):
    row = 160
    N_adc = 4
    N_adcCh = 3
    N_mux = 46
    col = N_adc*N_adc*N_mux
    indiCol = 184
    ZT = np.zeros((row, col), np.int8)
    Z = np.zeros((row, indiCol), np.int8)
    for i in range(0, row):
        for j in range(0, N_adc):
            for k in range(0,N_adcCh):
                for l in range(0, N_mux):
                    ZT[row-i-1,(col-(j*N_adcCh*N_mux+(2-k)*N_mux+45))] = frame[i*col+l*N_adc*N_adcCh+k*N_adc+j]
    if figure ==1: #left figure
        Z = ZT[:, 140:508:2] #want 140,142,...,506
    else:#figure ==2 (right figure)
        Z = ZT[:, 139:507:2] #want 139,141,...,505
    if DispFrame ==0: #ALL
        img = np.zeros((row,indiCol), np.int8)
        img = Z
    elif DispFrame ==1:#CEP
        img = np.zeros((80,60,), np.int8)
        img = Z[0:80,2:62]
    else: #DispFrame==2 #CEP-TOF
        img = np.zeros((160,120), np.int8)
        img = Z[0:160,62:182]
    
    imgplot.imshow(Z, "gray");
    histplot.hist(Z.ravel(), bins = 256)
class MBI_GUI(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.LoadBitFile.clicked.connect(self.bit_load) #when Load Bit File button is clicked
        self.LoadPattFile.clicked.connect(self.patt_load) #when Load Camera Pattern File button is clicked
        self.DispFrame.currentIndexChanged.connect(self.disp_change) #DispFrame selection changed
        self.DispImage.toggled.connect(self.disp_image) #when Display Image button is clicked
        self.RecVideo.toggled.connect(self.rec_video) #when Record Video button is clicked
        self.RecVideo.setEnabled(False)
        self.SaveImages.clicked.connect(self.save_img) #when save images button is clicked
        #img=mpimg.imread('test.png')
        #self.mplimg1.canvas.axes.imshow(img, "gray")
        #self.mplhist1.canvas.axes.hist(img.ravel(),bins =256)
    def bit_load(self): #load bit file for FPGA config
        global bitfile, error
        bitfile, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', 
         'c:\\',"*bit")
        #according to Opal Kelly examples:
        dev.OpenBySerial("") 
        error= dev.ConfigureFPGA(str(bitfile))
    def patt_load(self): #load camera pattern file
        if str(bitfile)!='': #check if bit file is loaded first
            global pattfile
            pattfile, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', 'c:\\',"*csv")
            with open(str(pattfile), 'rb') as csvfile:
                pattern = csv.reader(csvfile)
                # Send brief reset signal to initialize the FIFO.(code from Opal Kelly)
                dev.SetWireInValue(0x10, 0xff, 0x01)
                dev.UpdateWireIns()
                dev.SetWireInValue(0x10, 0x00, 0x01)
                dev.UpdateWireIns()
                dataout = bytearray(str(pattern))
                buf = bytearray(len(str(pattern)))
                # Send pattern to PipeIn endpoint with address 0x80
                data = dev.WriteToPipeIn(0x80, dataout) #data must be mutable type bytearray
                # Read pattern from PipeOut endpoint with address 0xB0
                #data = dev.ReadFromPipeOut(0xB0,buf) #why 0xB0?
        else:
            errorBox = QtWidgets.QMessageBox()
            errorBox.setWindowTitle('Error')
            errorBox.setText('Please load bit file first.')
            errorBox.addButton(QtWidgets.QPushButton('OK'), QtWidgets.QMessageBox.YesRole)
            errorBox.exec_()
    def disp_change(self): #if DispFrame selection has changed
        #stop displaying images and/or recording video
        change = "" #placeholder code
    def disp_image(self):
        #displays image based on settings
        if (self.DispImage.isChecked()): #if display image button is checked
            if str(bitfile)=="":
                #make error box pop up if bit file not loaded
                errorBox = QtWidgets.QMessageBox()
                errorBox.setWindowTitle('Error')
                errorBox.setText('Please load bit file first.')
                errorBox.addButton(QtWidgets.QPushButton('OK'), QtWidgets.QMessageBox.YesRole)
                errorBox.exec_()
                self.DispImage.setChecked(False) #reset button
            elif str(pattfile)=="":
                #make error box pop up if pattern file not loaded
                errorBox = QtWidgets.QMessageBox()
                errorBox.setWindowTitle('Error')
                errorBox.setText('Please load camera pattern file first.')
                errorBox.addButton(QtWidgets.QPushButton('OK'), QtWidgets.QMessageBox.YesRole)
                errorBox.exec_()
                self.DispImage.setChecked(False) #reset button
            else:
                #get input values
                global exposure, numMasks, numMaskChanges, numSubPer, frame
                exposure = self.Exposure.text()
                numMasks = self.Masks.text()
                numMaskChanges = self.MaskChanges.text()
                numSubPer = self.SubChange.text()
                frame = self.DispFrame.currentText()
                valid = True #flag, 0 if any inputs are not valid
                #determine if exposure value is valid input:
                try:
                    exposure = int(exposure) #change into integer type
                    if exposure!=abs(exposure):
                        valid = False
                except ValueError: #if not an int
                    valid = False
                #determine if number of masks is valid:
                try:
                    numMasks = int(numMasks) #change into integer type
                    if numMasks!=abs(numMasks): #make sure its a positive integer
                        valid = False
                except ValueError: #if not an int
                    valid = False
                #determine if mask changes is valid:
                try:
                    numMaskChanges = int(numMaskChanges) #change into integer type
                    if numMaskChanges!=abs(numMaskChanges): #make sure its a positive integer
                        valid = False
                except ValueError: #if not an int
                    valid = False
                #determine if number of subscenes is valid:
                try:
                    numSubPer = int(numSubPer) #change into integer type
                    if numSubPer!=abs(numSubPer): #make sure its a positive integer
                        valid = False
                except ValueError: #if not an int
                    valid = False
                if valid:
                    self.RecVideo.setEnabled(True) #allow video to be recorded
                    #write values to wirein endpoints
                    dev.SetWireInValue(0x11,exposure)
                    dev.UpdateWireIns()
                    dev.SetWireInValue(0x12,numMasks)
                    dev.UpdateWireIns()
                    dev.SetWireInValue(0x13,numMaskChanges)
                    dev.UpdateWireIns()
                    dev.SetWireInValue(0x14,numSubPer)
                    dev.UpdateWireIns()
                    #retrieve values on wireout endpoints
                    #dev.UpdateWireOuts()
                    #exposureRead = dev.GetWireOutValue(0x22)
                    #numMasksRead = dev.GetWireOutValue(0x23)
                    #numMaskChangesRead = dev.GetWireOutValue(0x24)
                    #activate the counter
                    dev.ActivateTriggerIn(0x53, 0x01)
                    #time.sleep(1)
                    stuckCt = 0
                    while(self.DispImage.isChecked()):
                        #read if full or oneFrameReady flag is triggered
                        dev.UpdateTriggerOuts()
                        full = dev.IsTriggered(0x6A, 0x01)
                        oneFrameReady = dev.IsTriggered(0x6A,0x02)
                        time.sleep(0.001)
                        stuckCt = stuckCt +1
                        if stuckCt==50:
                            stuckCt = 1
                            #reset fifo:
                            dev.SetWireInValue(0x10, 0xff, 0x01)
                            dev.UpdateWireIns()
                            dev.SetWireInValue(0x10, 0x00, 0x01)
                            dev.UpdateWireIns()
                            dev.ActivateTriggerIn(0x53,0x01)
                        elif full:
                            stuckCt = 1
                            buf = bytearray(262144)
                            fullFrame = dev.ReadFromPipeOut(0xA0,buf)
                            showFrame(self.mplimg1.canvas.axes(),
                                      self.mplhist1.canvas.axes(), 
                                      fullFrame, frame, 1)
                            showFrame(self.mplimg2.canvas.axes(),
                                      self.mplhist2.canvas.axes(), 
                                      fullFrame, frame, 2)
                            
                    #display images
                else:
                     #display error telling user to input valid parameters
                     errorBox = QtWidgets.QMessageBox()
                     errorBox.setWindowTitle('Error')
                     errorBox.setText('Please input valid parameter values.')
                     errorBox.addButton(QtWidgets.QPushButton('OK'), QtWidgets.QMessageBox.YesRole)
                     errorBox.exec_()
                     self.DispImage.setChecked(False) #reset button
                
        else: #if display image button is not checked
            self.RecVideo.setEnabled(False) #disable recording video button
            #stop recording
            filler= ""
    def save_img(self):
        self.SaveImages.setEnabled(False)
        
    def rec_video(self):
        if str(bitfile)=="":
            errorBox = QtWidgets.QMessageBox()
            errorBox.setWindowTitle('Error')
            errorBox.setText('Please load bit file first.')
            errorBox.addButton(QtWidgets.QPushButton('OK'), QtWidgets.QMessageBox.YesRole)
            errorBox.exec_()
        elif str(pattfile)=="":
            errorBox = QtWidgets.QMessageBox()
            errorBox.setWindowTitle('Error')
            errorBox.setText('Please load camera pattern file first.')
            errorBox.addButton(QtWidgets.QPushButton('OK'), QtWidgets.QMessageBox.YesRole)
            errorBox.exec_()
        else:
            #code to record video 
            filler = ""
def main():
    app = QtWidgets.QApplication(sys.argv)  # A new instance of QApplication
    form = MBI_GUI()  # We set the form to be our app
    form.show()  # Show the form
    app.exec_()  # and execute the app
    
    
if __name__ == "__main__":
    main()