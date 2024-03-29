#!/usr/bin/env python
# coding: utf-8

# # GUI Interface for LED Array
# ## When used controled by Tektronix PWS4305
# 
# ## Requirements
# Ensure that `import-ipynb` module is installed
# 
# ## Compiling
# 1. Ensure fbs is installed `pip install fbs`
# 2. Iniate a project `python3 -m fbs startproject`
# 3. Freeze the binary `python3 -m fbs freeze`
# 4. Create an installer `python3 -m fbs installer`
# 
# ## Converting to .py
# To save this file for use as a CLI, convert it to a .py file using `jupyter nbconvert --to python <filename>`

# In[1]:


import os
import sys
import re
from collections import namedtuple

# PyQt
from PyQt5 import QtGui

from PyQt5.QtCore import (
    Qt,
    QCoreApplication,
    QTimer,
    QThread
)

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QSlider,
    QMessageBox
)

# controller
# import import_ipynb # FREEZE
import led_array_controller as lac

import visa


# In[8]:


class LedArrayInterface( QWidget ):
    
    #--- window close ---
    def closeEvent( self, event ):
        self.__delete_controller()
        event.accept()
        
    
    #--- destructor ---
    def __del__( self ):
        self.__delete_controller()
        
    
    #--- initializer ---
    def __init__( self, resources ): # FREEZE
    # def __init__( self ):
        super().__init__()
        
        #--- instance variables ---
        image_folder = resources + '/images/' # FREEZE
        # image_folder = os.getcwd() + '/images/' 
        self.img_redLight = QtGui.QPixmap(    image_folder + 'red-light.png'    ).scaledToHeight( 32 )        
        self.img_greenLight = QtGui.QPixmap(  image_folder + 'green-light.png'  ).scaledToHeight( 32 )
        self.img_yellowLight = QtGui.QPixmap( image_folder + 'yellow-light.png' ).scaledToHeight( 32 )
        
        self.inst = None # the instrument
        
        #--- timers ---
        
        
        #--- init UI ---
        self.__init_ui()
        self.__register_connections()
        
        #--- init variables ---
        
#         self.__updatePort()
        
        
    def __init_ui( self ):
        #--- main window ---
        self.setGeometry( 100, 100, 200, 300 )
        self.setWindowTitle( 'LED Array Controller' )
        
        lo_main = QVBoxLayout()
        lo_main.addLayout( self.__ui_mainToolbar() )
        lo_main.addLayout( self.__ui_settings() )
        lo_main.addSpacing( 35 )
        lo_main.addLayout( self.__ui_commands() )
        
        self.setLayout( lo_main )
        
        self.show()
       
    
    def __ui_mainToolbar( self ):
        lo_mainToolbar = QHBoxLayout()
        
        self.__ui_mainToolbar_connect(  lo_mainToolbar )
        
        return lo_mainToolbar
    
    
    def __ui_settings( self ):
        lo_settings = QVBoxLayout()
        
        lo_row_1 = QHBoxLayout()
        self.__ui_settings_intensity( lo_row_1 )
        
        lo_settings.addLayout( lo_row_1 )
        
        return lo_settings
    
    
    def __ui_commands( self ):
        lo_commands = QVBoxLayout()
        self.__ui_on( lo_commands )
        
        return lo_commands
        
    
    def __ui_mainToolbar_connect( self, parent ):
        # connect / disconnect
        self.lbl_statusLight = QLabel()
        self.lbl_statusLight.setAlignment( Qt.AlignCenter )
        self.lbl_statusLight.setPixmap( self.img_redLight )
        
        self.lbl_status = QLabel( 'Disconnected' )
        self.btn_connect = QPushButton( 'Connect' )
    
        lo_statusView = QVBoxLayout()
        lo_statusView.addWidget( self.lbl_statusLight )
        lo_statusView.addWidget( self.lbl_status )
        lo_statusView.setAlignment( Qt.AlignHCenter )
        
        lo_status = QHBoxLayout()
        lo_status.addLayout( lo_statusView )
        lo_status.addWidget( self.btn_connect )
        lo_status.setAlignment( Qt.AlignCenter )
        
        parent.addLayout( lo_status )
        
        
    def __ui_settings_intensity( self, parent ):        
        sb_intensity = QDoubleSpinBox()
        sb_intensity.setMinimum( 0 )
        sb_intensity.setMaximum( 1.1 ) 
        sb_intensity.setSingleStep( 0.1 )
        self.sb_intensity = sb_intensity
        
        lbl_intensity = QLabel( 'Intensity' )
        
        lo_intensity = QHBoxLayout()
        lo_intensity.addWidget( lbl_intensity )
        lo_intensity.addWidget( sb_intensity )
        
        parent.addLayout( lo_intensity )
    
    
    def __ui_on( self, parent ):
        lo_on = QHBoxLayout()
        
        self.btn_on = QPushButton( 'On' )
        lo_on.addWidget( self.btn_on )
        
        parent.addLayout( lo_on )
    
        
    
    #--- ui functionality ---
    
    def __register_connections( self ):
        self.btn_connect.clicked.connect( self.toggle_connect )    
        self.btn_on.clicked.connect( self.toggle_on )
        
        self.sb_intensity.valueChanged.connect( self.set_intensity )

    
    #--- slot functions ---
        
    def toggle_connect( self ):
        """
        Toggles connection between selected com port
        """
        # show waiting for communication
        self.lbl_status.setText( 'Waiting...' )
        self.lbl_statusLight.setPixmap( self.img_yellowLight )
        self.repaint()
        
        # create laser controller if doesn't already exist, connect
        if self.inst is None:
            try:
                self.inst = lac.LedArray()
                self.inst.connect()
                
            except Exception as err:
                self.__update_connected_ui( False )
                
                warning = QMessageBox()
                warning.setWindowTitle( 'LED Array Error' )
                warning.setText( 'Could not connect\n{}'.format( err ) )
                warning.exec()
            
        else:
            self.__delete_controller()
        
        # update ui
        if self.inst is not None:
            self.__update_connected_ui( self.inst.connected )
            
        else:
            self.__update_connected_ui( False )
            
        # set voltage and current
        self.set_intensity()

        
    def toggle_on( self ):
        if self.inst is None:
            # not connected
            return
        
        method = self.btn_on.text()
        if method == 'On':
            self.on()
            self.btn_on.setText( 'Off' )
            
        if method == 'Off':
            self.off()
            self.btn_on.setText( 'On' )
        
    
    def on( self ):
        try:
            self.inst.on()
            
        except visa.VisaIOError as err:
            self.__handle_visa_error( err )
    
    
    def off( self ):
        try:
            self.inst.off()
            
        except visa.VisaIOError as err:
            self.__handle_visa_error( err )
    
        
    def set_intensity( self ):
        if self.inst is not None:
            self.inst.intensity = self.sb_intensity.value()
        
        
    #--- helper functions ---
    
    def __delete_controller( self ):
        if self.inst is not None:
            self.off()
            self.inst.disconnect()
            del self.inst
            self.inst = None
            
    
    def __update_connected_ui( self, connected ):
        if connected == True:
            statusText = 'Connected'
            statusLight = self.img_greenLight
            btnText = 'Disconnect'
            
        elif connected == False:
            statusText = 'Disconnected'
            statusLight = self.img_redLight
            btnText = 'Connect'
            
        else:
            statusText = 'Error'
            statusLight = self.img_yellowLight
            btnText = 'Connect'
        
        self.lbl_status.setText( statusText )
        self.lbl_statusLight.setPixmap( statusLight )
        self.btn_connect.setText( btnText )
        
    
    def __handle_visa_error( self, err ):
        warning = QMessageBox()
        warning.setWindowTitle( 'LED Array Controller Error' )
        warning.setText( 'Communication timeout' )
        warning.exec()

        self.__update_connected_ui( False )
        


# In[7]:


# FREEZE
# app = QCoreApplication.instance()
# if app is None:
#     app = QApplication( sys.argv )
    
# main_window = LedArrayInterface()
# sys.exit( app.exec_() )


# In[6]:


# FREEZE
# %load_ext autoreload
# %autoreload 1


# In[ ]:




