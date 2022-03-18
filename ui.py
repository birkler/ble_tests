#!/usr/bin/python
import npyscreen
import threading
import time
#!/usr/bin/python
from bluepy import btle
import time
import binascii
import re

dev_name_uuid = btle.UUID(0x2A00)

rotorServicesUUID = btle.UUID("fb8e8220-1797-11e6-900b-0002a5d5c51b")

bootloaderServices =  btle.UUID("00060000-f8ce-11e4-abf4-0002a5d5c51b")

genericServices = btle.UUID("8ab07720-1797-11e6-a7d5-0002a5d5c51b")

device_id = "00:a0:50:ae:51:de"

class GlobalData:

    def __init__(self):
        self.devicelist = None
        self.connectedMacAddress = None
        self.is_running = True
        self.i = 0

        #0-2bit data
        self.X_00_Button = None
        self.X_04_ChargingEnabled = None
        self.X_08_AuxInd = None,
        self.X_0C_AuxEnable = None,
        self.X_10_StepperPowerCtrl = None

        #1 byte data
        self.X_48_ADC_VBus__mV = None
        self.X_49_ADC_VMotor__mV = None
        self.X_4A_ADC_V__mV = None
        self.X_4B_ADC_VBus__mV = None
        self.X_40_BoardRev__HEX = None
        self.X_4C_Horiz_Run_Current__mA = None
        self.X_4D_Vert_Run_Current__mA = None
        self.X_50_Horiz_Hold__mA = None
        self.X_51_Vert_Hold__mA = None
        self.X_5C_Batt_Percent__Percent = None

        #2byte data
        self.X_80_FirmwareVersion__HEX = None
        self.X_84_Axis_Limit_Min_VERT__tens_of_deg = None
        self.X_88_Axis_Limit_Max_VERT__tens_of_deg = None
        self.X_85_Axis_Limit_Min_HORIZ__tens_of_deg = None
        self.X_89_Axis_Limit_Max_HORIZ__tens_of_deg = None
        self.X_8c_Axis_Pos_HORIZ__tens_of_deg = None
        self.X_8d_Axis_Pos_VERT__tens_of_deg = None
        self.X_90_Run_Voltage__mV = None
        self.X_94_Hold_Voltage__mV = None

        #    0x98 : "Max Speed (in deg/s)",
        #    0x9c : "Acceleration (in deg/s2)",
        #    0xa0 : "Speed Limit Min. (in deg/s)",
        #    0xa4 : "Speed Limit Max. (in deg/s)",
        #    0xa8 : "Acceleration Limit Min. (in deg/s2)",
        #    0xac : "Acceleration Limit Max. (in deg/s2)",
        self.X_b0_Batt_Int_Resist__mOhm = None

        #    0xcc : "Axis Position With ID (in 1/10 deg)",


        #3byte data
        self.X_C4_LED_RGB__HEX = None
        self.X_D0_macaddressH__HEX = None
        self.X_D4_macaddressL__HEX = None


        self.dictCmd = {}


        for variable_name in vars(self):
            if (variable_name[0:2]=='X_'):
                cmdhex = int(variable_name[2:4],16)
                self.dictCmd[cmdhex] = variable_name
        print(vars(self))


        self.rotorServicesCmd = {
            0x00 : "Push Button Indication	Button pressed",
            0x04 : "Charging Control",
            0x08 : "Structured Light Detect Indication",
            0x0c : "Structured Light Control",
            0x10 : "Stepper Power Control",
            0x14 : "Rotor Move Completion Success (response to 0x8c)",
            0x18 : "Rotor Move Completion Aborted (response to 0x8c)",
            0x1c : "Reset Motor Origin",
            0x40 : "Board Revision",
            0x48 : "ADC Readout : ",
            0x4c : "Run Current Control (mA)",
            0x50 : "Hold Current Control (mA)",
            0x54 : "Rotor Move Completion With ID Success (response to 0xcc)",
            0x58 : "Rotor Move Completion With ID Aborted (response to 0xcc)",
            0x5c : "Battery level in percents",
            0x80 : "Firmware Version (0.9.1 would be 0x91 0x00)",
            0x84 : "Axis Limit Min. (in 1/10 deg)",
            0x88 : "Axis Limit Max. (in 1/10 deg)",
            0x8c : "Axis Position (in 1/10 deg)",
            0x90 : "Run Voltage (mV)",
            0x94 : "Hold Voltage (mV)",
            0x98 : "Max Speed (in deg/s)",
            0x9c : "Acceleration (in deg/s2)",
            0xa0 : "Speed Limit Min. (in deg/s)",
            0xa4 : "Speed Limit Max. (in deg/s)",
            0xa8 : "Acceleration Limit Min. (in deg/s2)",
            0xac : "Acceleration Limit Max. (in deg/s2)",
            0xb0 : "Internal resistance of battery (in mOhms)",
            0xc4 : "LED Control (RGB components as payload, 1 byte each)",
            0xcc : "Axis Position With ID (in 1/10 deg)",
            0xd0 : "MAC address least significant part",
            0xd4 : "MAC address most significant part"
        }



    def parseAndUpdate(self,data):
        i=0
        datalen = len(data)
        while (i<datalen):
            val_ch = ord(data[i])
            payload = (val_ch & 0xC0) >> 6
            cmd = (val_ch & 0xFC)
            chn = val_ch & 0x3
            val=0
            i+=1
            if (payload == 0) :
                val = chn
            if (payload == 1) :
                val=ord(data[i])
            if (payload == 2) :
                val=ord(data[i+1])*255 + ord(data[i])
            if (payload == 3) :
                val=ord(data[i+1])*255*255 + ord(data[i+1])*255 + ord(data[i])

            i+=payload


            #if (cmd == 0x00):
                #self.rotorButton = chn
            
            if (self.dictCmd.has_key(cmd)):
                attribute_name = self.dictCmd.get(cmd)
                setattr(self,attribute_name,val)

            if (self.rotorServicesCmd.has_key(cmd)):
                cmd_str=self.rotorServicesCmd.get(cmd)
                print("0x%02x %40s chn=0x%x val:%d" % (cmd,cmd_str,chn,val))




class BLERotorUpdateThread(threading.Thread):
    def __init__(self,name,globalData,macAddress):
        super(BLERotorUpdateThread, self).__init__(name=name)
        self.globalData = globalData
        self.macAddress = macAddress
        self.daemon = True

    def run(self):
        while (self.globalData.is_running):
            self.globalData.connectedMacAddress = None
            try:
                print("Connecting to '%s'..." % device_id)
                self.dev = btle.Peripheral(deviceAddr = self.macAddress)
                self.globalData.connectedMacAddress = self.macAddress

                self.ch = self.dev.getCharacteristics(uuid=dev_name_uuid)[0]
                if (self.ch.supportsRead()):
                    self.device_name = self.ch.read()

                print("Services in '%s' %s (%s), RSSI=%d dB" % (self.device_name, self.dev.addr, self.dev.addrType, -900))

                self.rotorService=self.dev.getServiceByUUID(rotorServicesUUID)

                self.ch = self.rotorService.getCharacteristics()[0]

                while (self.globalData.is_running):
                    ch_read = self.ch.read()
                    self.globalData.parseAndUpdate(ch_read)
                    #val = binascii.b2a_hex(ch_read)
                    #print ("%s" % (val))
                    time.sleep(0.05)
                    self.globalData.i += 1

            except Exception as inst:
                print(type(inst))     # the exception instance
                print(inst.args)     # arguments stored in .args
                print(inst)           # __str__ allows args to be printed directly
                print("!")
                time.sleep(1.2)









class RotorSelectForm(npyscreen.Form):
    def create(self) :
        self.keypress_timeout = 0
        self.s_r  = self.add(npyscreen.TitleSlider, out_of=10, name = "Red")
        self.s_g  = self.add(npyscreen.TitleSlider, out_of=10, name = "Green")
        self.s_b  = self.add(npyscreen.TitleSlider, out_of=10, name = "Blue")
        self.button_rgb = self.add(npyscreen.Button,name="Set RGB")


class RotorHeroForm(npyscreen.Form):
    def __init__(self,parentApp, name,globalData):
        self.globalData = globalData
        super(RotorHeroForm, self).__init__(parentApp,name)
        print("!!@")
        self.updateForm()


    def create(self) :
        self.keypress_timeout = 1
        self.connected = self.add(npyscreen.TitleText, name = "Connected:",value="")
        self.s_r  = self.add(npyscreen.TitleSlider, out_of=10, name = "Red")
        self.s_g  = self.add(npyscreen.TitleSlider, out_of=10, name = "Green")
        self.s_b  = self.add(npyscreen.TitleSlider, out_of=10, name = "Blue")
        self.button_rgb = self.add(npyscreen.Button,name="Set RGB")
        self.t  = self.add(npyscreen.TitleText, name = "BLE iter:",value="100")

        
        self.auto_widgets = {}
        self.widget_unit = {}
        cmds = self.globalData.dictCmd.keys()
        cmds = sorted(cmds)
        cnt = 0
        for cmd in cmds:
            variable_name = self.globalData.dictCmd[cmd]
            var_name = "widget_" + variable_name
            name_text_data = variable_name[5:]
            unit_name = ""
            label_and_unit = re.split("__",name_text_data)
            name_text = label_and_unit[0]
            if (len(label_and_unit) >= 2):
                unit_name = label_and_unit[1]
            self.auto_widgets[var_name] = variable_name
            self.widget_unit[var_name] = unit_name
            if (cnt & 0x1):
                self.nextrelx= 50
            else:
                self.nextrelx= 4
            widget = self.add(widgetClass = npyscreen.TitleText,max_width=45,begin_entry_at=23, name=name_text,value=0)
            self.nextrely -= 1
            if (cnt & 0x1):
                self.nextrely += 1
            setattr(self,var_name,widget)
            cnt+=1


        #self.batteryPercent  = self.add(npyscreen.TitleText, name = "Battery percent:",value=100)
        #self.firmwareVer  = self.add(npyscreen.TitleText, name = "Firmware Ver:",value=None)
        #self.fn = self.add(npyscreen.TitleFilename, name = "Filename:")
        #self.fn2 = self.add(npyscreen.TitleFilenameCombo, name="Filename2:")
        self.i = 0
        

    def updateForm(self) :
        for widgetname,variablename in self.auto_widgets.items():
            variablevalue = getattr(self.globalData,variablename,0)
            widget = getattr(self,widgetname)
            unit = self.widget_unit[widgetname]
            if (isinstance(variablevalue, int)):
                if (unit == "HEX"):
                    widget.value = "0x%08x %s" % (variablevalue,unit)
                else:
                    int_val = int(variablevalue)
                    widget.value = "%d %s" % (int_val,unit)


        self.connected.value = self.globalData.connectedMacAddress
        #self.firmwareVer.value = "%d.%d.%d" % ((self.globalData.X_80_FirmwareVersion >> 8 & 0xF), (self.globalData.X_80_FirmwareVersion >> 4 & 0xF), (self.globalData.X_80_FirmwareVersion >> 0 & 0xF))
        self.t.set_value("%d" % self.globalData.i)


    def while_editing(self,widget) :
        self.updateForm()
        self.display()


    def while_waiting(self) :
        self.updateForm()
        self.display()



class RotorTestApp(npyscreen.NPSAppManaged):
    def __init__(self):
        super(RotorTestApp, self).__init__()
        self.globalData = GlobalData()

    def onStart(self):
        npyscreen.setTheme(npyscreen.Themes.BlackOnWhiteTheme)
        print("!")
        self.addForm(
            f_id="MAIN",
            FormClass = RotorHeroForm,
            name = "InsideMaps HERO rotor BLE connection",
            globalData = self.globalData)



if __name__ == "__main__":
    app = RotorTestApp()
    mythread = BLERotorUpdateThread(
        name = "Thread-BLE",
        globalData = app.globalData,
        macAddress = device_id)  # ...Instantiate a thread and pass a unique ID to it
    mythread.start()                                   # ...Start the thread

    app.run()

    time.sleep(100.2)




