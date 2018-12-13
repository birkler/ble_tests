#!/usr/bin/python
from bluepy import btle
import time
import binascii

dev_name_uuid = btle.UUID(0x2A00)

rotorServicesUUID = btle.UUID("fb8e8220-1797-11e6-900b-0002a5d5c51b")

bootloaderServices =  btle.UUID("00060000-f8ce-11e4-abf4-0002a5d5c51b")

genericServices = btle.UUID("8ab07720-1797-11e6-a7d5-0002a5d5c51b")


device_id = "00:a0:50:ae:51:de"

print("Connecting to '%s'..." % device_id)
dev = btle.Peripheral(device_id)

device_name = "";

ch = dev.getCharacteristics(uuid=dev_name_uuid)[0]
if (ch.supportsRead()):
    device_name = ch.read()

print("Services in '%s' %s (%s), RSSI=%d dB" % (device_name, dev.addr, dev.addrType, -900))


rotorServicesCmd = {
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


#for svc in dev.services:
#    print(str(svc))

rotorService=dev.getServiceByUUID(rotorServicesUUID)

def parseString(data):
    i=0;
    datalen = len(data);
    while (i<datalen):
        val_ch = ord(data[i])
        payload = (val_ch & 0xC0) >> 6
        cmd = (val_ch & 0xFC)
        chn = val_ch & 0x3
        cmd_str = "UNKNOWN"
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

        if (rotorServicesCmd.has_key(cmd)):
            cmd_str=rotorServicesCmd.get(cmd)
            print("0x%02x %40s chn=0x%x val:%d" % (cmd,cmd_str,chn,val))






ch = rotorService.getCharacteristics()[0]

while 1:
    ch_read = ch.read()
    parseString(ch_read);
    val = binascii.b2a_hex(ch_read)
    print ("%s" % (val))
    time.sleep(0.2)

