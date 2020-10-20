#!/usr/bin/env python
# coding: utf-8

# # LED Array Controller
# ## For use with Tektronix PWS4305

# In[2]:


import power_supply_controller as psc


# In[8]:


class LedArray( psc.PowerSupply ):
    
    def __init__( self, timeout = 10, rid = None ):
        psc.PowerSupply.__init__( self, timeout, rid )
        self.__intensity = 0
        
        # model found by curve fitting intensity using reference cell
        self.__itoc = lambda i: (
              0.69688698* i**(2) 
            + 1.84788684* i 
            - 0.1645259*  i**(1/2)
            + 0.0785805*  i**(1/3)
        )
        
    #--- public methods ---   
    @property
    def intensity( self ):
        return self.__intensity
    
    
    @intensity.setter
    def intensity( self, val ):
        # safety
        if val > 1.1:
            raise ValueError( 'Intensity too high' )
        
        elif val < 0:
            raise ValueError( 'Invalid intensity, below zero' )
        
        self.__intensity = val
        self.current = self.__itoc( val )
    
    
    @property 
    def model( self ):
        return self.__itoc
    
    
    def connect( self ):
        psc.PowerSupply.connect( self )
        # initialize power supply
        self.off()
        self.voltage = 21.5 # highest allowed voltage
        


