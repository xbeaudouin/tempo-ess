#!/usr/local/bin/python3

import urllib3
import json
import paho.mqtt.client as mqtt
import time
import pyprowl
#import syslog

from datetime import date,datetime

# Settings
from secret import ecodevice,use_eco,gx,gxsn,chgbleu,chgblanc,chgrouge,minbleu,minblanc,minrouge,prowlkey


# Lancer ceci du 01 Oct au 31 mai
# une fois avant 22h / une fois apres 22h

# Don't touch that
# See : https://github.com/victronenergy/venus/wiki/dbus#settings
ESSwBL  = 1     # ESS "Optimized with BatteryLife)
ESSwoBL = 10    # ESS "Optimized without BatteryLife)

p = pyprowl.Prowl(prowlkey)

def sendprowl(foo):
    p.notify(event='EDF TEMPO', description='Attention EDF Tarif: '+foo,
            priority=0, appName='EDF TEMPO')

# Log !
def loggerinfo(foo):
    #syslog.syslog(syslog.LOG_INFO,foo)
    print(foo)

# Setup MQTT Client
global client

def on_connect(client, userdata, flags, rc):
    client.subscribe("$SYS/#")
    global flagConntected
    flagConntected = 1 
    loggerinfo("Broker connected.")

def on_message(client, userdata, msg):
    loggerinfo(msg.topic+" "+str(msg.payload))

def on_publish(client, userdata, mid):
    loggerinfo("Message Published.")    

def on_disconnect(client, userdata, rc):
    global flagConntected
    flagConntected = 0  
    loggerinfo("Broker disconnected.")

client = mqtt.Client("clientdynTEMPO")
flagConntected = 0
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_disconnect = on_disconnect
#client.tls_set("venus-ca.crt")
#client.username_pw_set(username, password)       

# Set the Maxmium SOC when schedule Charge
def setChargeSetpoint(chargepoint):
    loggerinfo("Set charge setpoint: " + str(chargepoint) + " %")
    if (chargepoint < 50) or (chargepoint > 100):
        loggerinfo("Chargepoint should be between 50 to 100%")
    else:
        # Control ESS over MQTT
        client.connect(gx, 1883, keepalive=60)
        client.loop_start()
        # Wait for connecting
        while not flagConntected:
            time.sleep(1)
        client.publish("W/" + gxsn + "/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/0/Soc", '{"value":' + str(chargepoint) + '}')
        client.loop_stop()  

# Set the Minimum Soc Limit
def setMinSocSetpoint(chargepoint):
    loggerinfo("Set MinSoc setpoint: " + str(chargepoint) + " %")
    if (chargepoint < 10) or (chargepoint > 40):
        loggerinfo("Chargepoint should be between 50 to 100%")
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
    loggerinfo("Set ESS State: " + str(state) )
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
        loggerinfo(" -> not published")

# Setup Prowl
try:
    p.verify_key()
except Exception as e:
    print("Error verifying Prowl API key: {}".format(e))
    exit()


http = urllib3.PoolManager()
if use_eco:
    # Setup EcoDevice
    resp = http.request("GET", "http://"+ecodevice+"/api/xdevices.json?cmd=10")

    if resp.status == 200:
        teleinfo = json.loads(resp.data)

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
        elif demaintarif == "BLAN":
            tomorrow = 1
        elif demaintarif == "ROUG":
            tomorrow = 2
        else:
            tomorrow=0

        loggerinfo("Current tarif: " + curtarif + " ("+str(today)+" / "+str(daynight) + ")")
        loggerinfo("Demain tarif:  " + demaintarif + " ("+str(tomorrow)+")")

else:
    # Use EDF "API"
    today=date.today()
    resp = http.request("GET", "https://particulier.edf.fr/services/rest/referentiel/searchTempoStore?dateRelevant="+str(today.strftime("%Y-%m-%d")))
    if resp.status == 200:
        edfapi = json.loads(resp.data)
        curcouleur = edfapi['couleurJourJ']
        demaincouleur = edfapi['couleurJourJ1']

        if curcouleur == "TEMPO_BLEU":
            today = 0
        elif curcouleur == "TEMPO_BLANC":
            today = 1
        elif curcouleur == "TEMPO_ROUGE":
            today = 2
        else:
            today = -1

        if demaincouleur == "TEMPO_BLEU":
            tomorrow = 0
        elif demaincouleur == "TEMPO_BLANC":
            tomorrow = 1
        elif demaincouleur == "TEMPO_ROUGE":
            tomorrow = 2
        elif demaincouleur == "NON_DEFINI":
            tomorrow = -1
        else:
            tomorrow = -1   # trop tot.

        now = datetime.now()
        #Heures creuses: 22h00 -> 06h00 
        loggerinfo("Current hour : "+str(now.hour))

        if now.hour >= 6 and now.hour <=22:
            loggerinfo("We are DAY")
            daynight = 1
        else:
            loggerinfo("We are NIGHT")
            daynight = 0

        loggerinfo("La couleur aujourd'hui "+str(curcouleur))
        loggerinfo("La couleur demain      "+str(demaincouleur))
if tomorrow == -1:
        loggerinfo("La couleur de demain n'est pas definie -> exit")
        quit()


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
        loggerinfo ("Rien a faire on sort")
elif today == 0:        # Bleu
    if tomorrow == 1:   # Blanc
        if daynight == 1:
            sendprowl('BLANC')
            loggerinfo ("Charge "+str(chgblanc)+"%")
            setChargeSetpoint(chgblanc)
    elif tomorrow == 2: # Rouge
        if daynight == 1:
            loggerinfo ("Charge "+str(chgrouge)+"%")
            sendprowl('ROUGE')
            setChargeSetpoint(chgrouge)
        else:
            loggerinfo ("SocMin "+str(minrouge)+"%")
            setMinSocSetpoint(minrouge)
            loggerinfo ("Battery life OFF")
            setESSstate(ESSwoBL)
elif today == 1:        # Blanc
    if tomorrow == 0:   # Bleu
        if daynight == 1:
            loggerinfo ("Charge "+str(chgbleu)+"%")
            setChargeSetpoint(chgbleu)
            sendprowl('BLEU')
        else:
            loggerinfo ("SocMin "+str(minbleu)+"%")
            setMinSocSetpoint(minbleu)
    elif tomorrow == 2: # Rouge
        if daynight == 1:
            sendprowl('ROUGE')
            loggerinfo ("Charge "+str(chgrouge)+"%")
            setChargeSetpoint(chgrouge)
        else:
            loggerinfo ("SocMin "+str(minrouge)+"%")
            setMinSocSetpoint(minrouge)
            loggerinfo ("Battery life OFF")
            setESSstate(ESSwoBL)
elif today == 2:        # Rouge
    if tomorrow == 0:   # Bleu
        if daynight == 1:
            loggerinfo ("Charge "+str(chgbleu)+"%")
            setChargeSetpoint(chgbleu)
            sendprowl('BLEU')
        else:
            loggerinfo ("SocMin "+str(minbleu)+"%")
            setMinSocSetpoint(minbleu)
            loggerinfo ("Battery life ON")
            setESSstate(ESSwBL)
    elif tomorrow == 1: # Blanc
        if daynight == 1:
            sendprowl('BLANC')
            loggerinfo ("Charge "+str(chgblanc)+"%")
            setChargeSetpoint(chgblanc)
        else:
            loggerinfo ("SocMin "+str(minblanc)+"%")
            setMinSocSetpoint(minblanc)
            loggerinfo ("Battery life ON")
            setESSstate(ESSwBL)

# Voir code : https://github.com/xbeaudouin/dynamic-ess
# ET : https://github.com/victronenergy/venus/wiki/dbus#settings
