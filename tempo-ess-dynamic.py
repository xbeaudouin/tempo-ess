#!/usr/local/bin/python3

import urllib3
import json
import paho.mqtt.client as mqtt
import time

# Settings
from secret import ecodevice,gx,gxsn,chgbleu,chgblanc,chgrouge,minbleu,minblanc,minrouge

# Lancer ceci du 01 Oct au 31 mai
# une fois avant 22h / une fois apres 22h

# Don't touch that
# See : https://github.com/victronenergy/venus/wiki/dbus#settings
ESSwBL  = 1     # ESS "Optimized with BatteryLife)
ESSwoBL = 10    # ESS "Optimized without BatteryLife)

# Setup MQTT Client
global client

def on_connect(client, userdata, flags, rc):
    client.subscribe("$SYS/#")
    global flagConntected
    flagConntected = 1 
    #logger.info("Broker connected.")
    print("Broker connected.")

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def on_publish(client, userdata, mid):
    #logger.info("Message Published.")    
    print("Message Published.")    

def on_disconnect(client, userdata, rc):
    global flagConntected
    flagConntected = 0  
    #logger.info("Broker disconnected.")
    print("Broker disconnected.")

client = mqtt.Client("clientdynTEMPO")
flagConntected = 0
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_disconnect = on_disconnect
#client.tls_set("venus-ca.crt")
#client.username_pw_set(username, password)       

# Setup logfile
#logzero.logfile("log.log", maxBytes=1e6, backupCount=3)

# Set the Maxmium SOC when schedule Charge
def setChargeSetpoint(chargepoint):
    #logger.info("Set charge setpoint: " + str(chargepoint) + " %")
    print("Set charge setpoint: " + str(chargepoint) + " %")
    if (chargepoint < 50) or (chargepoint > 100):
        #logger.info("Chargepoint should be between 50 to 100%")
        print("Chargepoint should be between 50 to 100%")
    else:
        # Control ESS over MQTT
        client.connect(gx, 1883, keepalive=60)
        client.loop_start()
        # Wait for connecting
        while not flagConntected:
            time.sleep(1)
        client.publish("W/" + gxsn + "/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/O/Soc", '{"value":' + str(chargepoint) + '}')
        client.loop_stop()  

# Set the Minimum Soc Limit
def setMinSocSetpoint(chargepoint):
    #logger.info("Set MinSoc setpoint: " + str(chargepoint) + " %")
    print("Set MinSoc setpoint: " + str(chargepoint) + " %")
    if (chargepoint < 10) or (chargepoint > 40):
        #logger.info("Chargepoint should be between 50 to 100%")
        print("Chargepoint should be between 10 to 40%")
    else:
        # Control ESS over MQTT
        client.connect(gx, 1883, keepalive=60)
        client.loop_start()
        # Wait for connecting
        while not flagConntected:
            time.sleep(1)
        client.publish("W/" + gxsn + "/settings/0/Settings/CGwacs/BatteryLife/MinimumSocLimit", '{"value":' + str(chargepoint) + '}')
        client.loop_stop()  

# Set ESS State (danger only 1 or 10 is ok)
# 1 = Optimized with Battery Life
# 10 = Optimized without battery life
# See https://github.com/victronenergy/venus/wiki/dbus#settings
def setESSstate(state):
    #logger.info("Set ESS State: " + str(state) )
    print("Set ESS State: " + str(state) )
    # Security Checks
    if (state == 1 or state == 10):
        # Control ESS over MQTT
        client.connect(gx, 1883, keepalive=60)
        client.loop_start()
        # Wait for connecting
        while not flagConntected:
            time.sleep(1)
        client.publish("W/" + gxsn + "/settings/0/Settings/CGwacs/BatteryLife/State", '{"value":' + str(state) + '}')
        lastChargeCondition = 1
        client.loop_stop()  
    else:
        #logger.info(" -> not published")
        print(" -> not published")

# Setup EcoDevice
http = urllib3.PoolManager()
resp = http.request("GET", "http://"+ecodevice+"/api/xdevices.json?cmd=10")

#print("resp.status = "+str(resp.status))
if resp.status == 200:
    #print("Having data -> decode")
    teleinfo = json.loads(resp.data)

    #print(json.dumps(teleinfo, sort_keys=True, indent=4))

    # Value of var  today   daynight
    # HPJB = Bleu   0       1
    # HCJB = Bleu   0       0
    # HPJW = Blanc  1       1
    # HCJW = Blanc  1       0
    # HPJR = Rouge  2       1
    # HCJR = Rouge  2       0
    curtarif = teleinfo['T1_PTEC']
    if curtarif == "HPJB":
            today = 0
            daynight = 1
    elif curtarif == "HCJB":
            today = 0
            daynight = 0
    elif curtarif == "HPJW":
            today = 1
            daynight = 1
    elif curtarif == "HCJW":
            today = 1
            daynight = 0
    elif curtarif == "HPJR":
            today = 2
            daynight = 1
    elif curtarif == "HCJR":
            today = 2
            daynight = 0
    else:
            today = 0
            daynight = 0

    # Value of var  tomorrow
    # ---- = Bleu   0
    # BLEU = Bleu   0
    # BLAN = Blanc  1
    # ROUG = Rouge  2
    demaintarif = teleinfo['T1_DEMAIN']
    if demaintarif == "----":
        tomorrow = 0
    elif demaintarif == "BLEU":
        tomorrow = 0
    elif demaintarif == "BLANC":
        tomorrow = 1
    elif demaintarif == "ROUG":
        tomorrow = 2
    else:
        tomorrow=0


    print("Current tarif: " + curtarif + " ("+str(today)+" / "+str(daynight) + ")")
    print("Demain tarif:  " + demaintarif + " ("+str(tomorrow)+")")

# daynight : 1 = jour / 0 nuit
#   Today       Tomorrow    Daynight    Action
#       0           0        O          Rien          
#       0           0        1          Rien          
#       0           1        0          Rien
#       0           1        1          Charge 90%
#       0           2        0          SocMin 25% / Batterlife Off
#       0           2        1          Charge 95%
#       1           0        0          SocMin 30%
#       1           0        1          Charge 80%
#       1           1        0          Rien
#       1           1        1          Rien
#       1           2        0          SocMin 25% / Batterlife Off
#       1           2        1          Charge 95%
#       2           0        0          SocMin 30% / Batterlife On
#       2           0        1          Charge 80%
#       2           1        0          SocMin 30% / Batterlife On
#       2           1        1          Charge 90%
#       2           2        0          Rien
#       2           2        1          Rien
#today = 1
#tomorrow = 0
#daynight = 0
if today == tomorrow:
        print ("Rien a faire on sort")
elif today == 0:        # Bleu
    if tomorrow == 1:   # Blanc
        if daynight == 1:
            print ("Charge 90%")
            setChargeSetpoint(chgblanc)
    elif tomorrow == 2: # Rouge
        if daynight == 1:
            print ("Charge 95%")
            setChargeSetpoint(chgrouge)
        else:
            print ("SocMin 25%")
            setMinSocSetpoint(minrouge)
            print ("Battery life OFF")
            setESSstate(ESSwoBL)
elif today == 1:        # Blanc
    if tomorrow == 0:   # Bleu
        if daynight == 1:
            print ("Charge 80%")
            setChargeSetpoint(chgbleu)
        else:
            print ("SocMin 30%")
            setMinSocSetpoint(minbleu)
    elif tomorrow == 2: # Rouge
        if daynight == 1:
            print ("Charge 95%")
            setChargeSetpoint(chgrouge)
        else:
            print ("SocMin 25%")
            setMinSocSetpoint(minrouge)
            print ("Battery life OFF")
            setESSstate(ESSwoBL)
elif today == 2:        # Rouge
    if tomorrow == 0:   # Bleu
        if daynight == 1:
            print ("Charge 80%")
            setChargeSetpoint(chgbleu)
        else:
            print ("SocMin 30%")
            setChargeSetpoint(chgbleu)
            print ("Battery life ON")
            setESSstate(ESSwBL)
    elif tomorrow == 1: # Blanc
        if daynight == 1:
            print ("Charge 90%")
            setChargeSetpoint(chgblanc)
        else:
            print ("SocMin 30%")
            setMinSocSetpoint(minblanc)
            print ("Battery life ON")
            setESSstate(ESSwBL)

# Voir code : https://github.com/xbeaudouin/dynamic-ess
# ET : https://github.com/victronenergy/venus/wiki/dbus#settings
