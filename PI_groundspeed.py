##########################################################################################################
# PI_groundspeed_fse.py by Kristian80
# 
# Enables Hotkeys for increasing or decreasing your ground or simulation speed by 1
# Since X-Plane only shows the sim speed information when it matches multiples of 2
# there is also the possibility to show the speed settings in the lower left corner
#
# Additional this version sets your sim speed to 1 when changing the ground speed 
# This is an additional safety feature for FSEconomy, as the client will cancel your flight
# when you exceed 16-times game acceleration (=ground speed * sim speed)
#
# Published under the GPLv3 License
#
##########################################################################################################


#import pygame
#import numpy as np

from XPLMDefs import *
from XPLMProcessing import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMDataAccess import *
from XPLMUtilities import *
from XPLMPlugin import *
from math import *

import os.path
import random
import time

class PythonInterface:

    def XPluginStart(self):

        self.Name = "ShowSetspeed1"
        self.Sig =  "ka.Python.ShowSetspeed1"
        self.Desc = "Shows the speed of the simulator and lets you adjust the ground speed."
        
        #####################################################################################################################
        # If you like to have the output deactivated on default, replace the following line with: self.show_output = 0
        self.show_output = 1
        #####################################################################################################################
        self.time_gs = XPLMFindDataRef("sim/time/ground_speed")
        self.time_sp = XPLMFindDataRef("sim/time/sim_speed")
        self.time_sact = XPLMFindDataRef("sim/time/sim_speed_actual")    
        self.fa_fuel_flow = XPLMFindDataRef("sim/flightmodel/engine/ENGN_FF_")
        self.fa_fuel_weight = XPLMFindDataRef("sim/flightmodel/weight/m_fuel")
        self.i_replay = XPLMFindDataRef("sim/operation/prefs/replay_mode")
        self.i_paused = XPLMFindDataRef("sim/time/paused")
        
        self.CmdGndSpeedUpCB = self.CmdGndSpeedUpCallback
        self.CmdGndSpeedDownCB = self.CmdGndSpeedDownCallback
        self.CmdToogleOutputCB = self.CmdToogleOutputCallback
        
        self . CmdGroundSpeedUp = XPLMCreateCommand ( "ground_speed/ground_speed_up" , "Increase ground speed by 1" )
        self . CmdGroundSpeedDown = XPLMCreateCommand ( "ground_speed/ground_speed_down" , "Decrease ground speed by 1" )
        self . CmdToogleOutput = XPLMCreateCommand ( "ground_speed/show_sim_speed" , "Toogles the simspeed window" )
        
        XPLMRegisterCommandHandler ( self , self . CmdGroundSpeedUp , self . CmdGndSpeedUpCB , 0 , 0 )
        XPLMRegisterCommandHandler ( self , self . CmdGroundSpeedDown , self . CmdGndSpeedDownCB , 0 , 0 )
        XPLMRegisterCommandHandler ( self , self . CmdToogleOutput , self . CmdToogleOutputCB , 0 , 0 )

        self.DrawWindowCB = self.DrawWindowCallback
        self.KeyCB = self.KeyCallback
        self.MouseClickCB = self.MouseClickCallback
        self.WindowId = XPLMCreateWindow(self, 10, 300, 500, 500, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
        
        self.FlightLoopCB = self.FlightLoopCallback
        XPLMRegisterFlightLoopCallback(self, self.FlightLoopCB, -1, 0)
        
        return self.Name, self.Sig, self.Desc


    def XPluginStop(self):
        XPLMDestroyWindow(self, self.WindowId)
        XPLMUnregisterCommandHandler ( self , self . CmdGroundSpeedUp , self . CmdGndSpeedUpCB , 0 , 0 )
        XPLMUnregisterCommandHandler ( self , self . CmdGroundSpeedDown , self . CmdGndSpeedDownCB , 0 , 0 )
        XPLMUnregisterCommandHandler ( self , self . CmdToogleOutput , self . CmdToogleOutputCB , 0 , 0 )
        pass


    def XPluginEnable(self):
        return 1


    def XPluginDisable(self):
        pass



    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass
        
    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        data_time_gs = XPLMGetDatai(self.time_gs) - 1 #reduce by one as 1x is correct
        data_paused = XPLMGetDatai(self.i_paused)
        data_replay = XPLMGetDatai(self.i_replay)
        data_fa_fuel_flow = []
        XPLMGetDatavf(self.fa_fuel_flow, data_fa_fuel_flow, 0, 8)
        
        data_fa_fuel_weight = []
        XPLMGetDatavf(self.fa_fuel_weight, data_fa_fuel_weight, 0, 9)
        
        if (data_paused == 0) and (data_replay == 0):
            fuel_flow = 0
            for index in range(0,8):
                fuel_flow += data_fa_fuel_flow[index]
            
            fuel_reduce = data_time_gs * fuel_flow * elapsedMe
            
            fuel_tanks = 0
            for index in range(0,9):
                if (data_fa_fuel_weight[index] > fuel_reduce):
                    fuel_tanks += 1
            
            if (fuel_tanks > 0):
                for index in range(0,9):
                    if (data_fa_fuel_weight[index] > fuel_reduce):
                        data_fa_fuel_weight[index] -= (fuel_reduce / fuel_tanks)
                XPLMSetDatavf(self.fa_fuel_weight, data_fa_fuel_weight, 0, 9)
    
        return -1;



    def DrawWindowCallback(self, inWindowID, inRefcon):
        
        lLeft = []; lTop = []; lRight = []; lBottom = []
        XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
        left = int(lLeft[0]); top = int(lTop[0]); right = int(lRight[0]); bottom = int(lBottom[0])

        color = 1.0, 1.0, 1.0
        
        
        data_time_gs = XPLMGetDatai(self.time_gs)
        data_time_sp = XPLMGetDatai(self.time_sp)
        data_time_sact = XPLMGetDataf(self.time_sact)
        gResult = XPLMDrawTranslucentDarkBox(left, top, right, bottom)
        
        if (self.show_output > 0):
            gResult = XPLMDrawString(color, left + 5, top - 10, "Ground Speed Acceleration: " + str(data_time_gs), 0, xplmFont_Basic)
            gResult = XPLMDrawString(color, left + 5, top - 20, "Sim Speed Acceleration: " +  "{:.2f}".format(data_time_sp), 0, xplmFont_Basic)
            gResult = XPLMDrawString(color, left + 5, top - 30, "True Sim Speed: " + "{:.2f}".format(data_time_sact), 0, xplmFont_Basic)
        return 0


    def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
        return 0


    def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
        return 0
        
    
    def CmdToogleOutputCallback( self , cmd , phase , refcon ) :
        if ( phase == 0 ) :
            self.show_output = 1 - self.show_output
        return 0
        
    def CmdGndSpeedUpCallback( self , cmd , phase , refcon ) :
        if ( phase == 0 ) :
            data_time_gs = XPLMGetDatai(self.time_gs) * 2
            if (data_time_gs) > 16:
                data_time_gs = 16
            if (data_time_gs) < 1:
                data_time_gs = 1
            #XPLMSetDatai(self.time_sp, 1)
            XPLMSetDatai(self.time_gs, data_time_gs)
        return 0
        
    def CmdGndSpeedDownCallback( self , cmd , phase , refcon ) :
        if ( phase == 0 ) :
            data_time_gs = XPLMGetDatai(self.time_gs) / 2
            if (data_time_gs) > 16:
                data_time_gs = 16
            if (data_time_gs) < 1:
                data_time_gs = 1
            #XPLMSetDatai(self.time_sp, 1)
            XPLMSetDatai(self.time_gs, data_time_gs)
        return 0
    
