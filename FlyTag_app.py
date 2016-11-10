from Tkinter import *
import pygatt.backends
import paho.mqtt.client as mqtt
import time
import timeit
import threading
import sys
import binascii
import os
import tempfile
from PIL import ImageTk, Image
import webbrowser

global continuousRead
global client
continuousRead = []
global devices

class BLEdevice:

    deviceCount = 0
    busy = False
    
    def __init__(self, name, mac, interval, command):
        self.name = name
        self.mac = mac
        self.interval = interval
        self.command = command
        self.newCommand = ""
        self.commandToSend = False
        self.end = False
        BLEdevice.deviceCount += 1

    def lowerCount(self):
        BLEdevice.deviceCount -= 1

    def makeBusy(self):
        BLEdevice.busy = True

    def free(self):
        BLEdevice.busy = False

    def endThread(self):
        self.end = True

    def changeCommand(self, newCommand, newInterval):
        self.command = newCommand
        self.interval = newInterval

class myThread(threading.Thread):

    def __init__(self, threadID, device):
        print("Thread initialized!")
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.device = device

        loopRead(self.threadID, self.device)		

def writeCommand(firefly, endNode, cmd):
    cmd = endNode + cmd
    #print(cmd)
    firefly.char_write_handle(24, map(ord, cmd))

def tryConnect(adapter2, mac):

    error = 0
    
    while True:
        try:
            print("Trying to connect...")
            if(error > 3):
                return 'null'
            else:
                return(adapter2.connect(mac, 5, 'random'))
            break
        except pygatt.exceptions.NotConnectedError:
            error += 1
            #print("Had an Error...")
            time.sleep(2)
            pass

def callback(event):
    webbrowser.open_new(r"https://www.FireFly-IoT.com")

def callback1(event):
    webbrowser.open_new(r"https://developer.ibm.com/recipes/tutorials/?s=firefly-iot")    
        
def loopRead(thread, device):
    #print("normal")
    error = 0
    connection = None
    adapterTmp = pygatt.backends.GATTToolBackend()
    #adapterTmp.reset()
    adapterTmp.start()
    passed = False
    
    if(passed == False):
        time1 = time.clock()

    try:
        if(error > 2):
            error = 0
            connection = None

        if(connection is None and device.busy == False):
            device.makeBusy()
            connection = tryConnect(adapterTmp, device.mac)
            try:
                writeCommand(connection, device.name, device.command)
            except:
                pass
            device.free()
            time.sleep(0.1)
        if(connection != None):
            received = connection.char_read_hnd(24)
            #print(received)
            if(len(received) > 30):
                publishMQTT(received)
                error = 0
            if(device.commandToSend == True):
                try:
                    writeCommand(connection, device.name, device.newCommand)
                except:
                    pass
                device.commandToSend = False
    except pygatt.exceptions.NotificationTimeout:
        error += 1
        passed = True
        #print("passed ")
        #print(thread)

    connection.disconnect()
    connection = None
        
def publishMQTT(data):

    g2x = (data[4] << 8) | (data[5])
    g2y = (data[6] << 8) | (data[7])
    g2z = (data[8] << 8) | (data[9])

    gx = g2x * 0.003125
    gy = g2y * 0.003125
    gz = g2z * 0.003125

    ax = (data[10] << 8) | data[11]
    ay = (data[12] << 8) | data[13] 
    az = (data[14] << 8) | data[15] 

    a1x = ax / 16384.0
    a1y = ay / 16384.0
    a1z = az / 16384.0

    if (data[10] > 127):
        a1x = a1x - 4.0
    if (data[12]> 127):
        a1y = a1y - 4.0
    if (data[14]> 127):
        a1z = a1z - 4.0

    mx = (data[16] << 8) | data[17]
    my = (data[18] << 8) | data[19] 
    mz = (data[20] << 8) | data[21]

    if (data[16] > 127):
        mx = mx - 65536
    if (data[18]> 127):
        my = my - 65536
    if (data[20]> 127):
        mz = mz - 65536

    lux = (data[26] << 8) | data[27]
    print "lux"
    print lux

    t = (data[22] << 8) | data[23]
    temp = ((175.72 * t) / 65536) - 46.85
    print "temp"
    print temp
    
    rh = (data[24] << 8) | data[25]
    humid = ((125.0 * rh) / 65536) - 6
    print "humid"
    print humid

    degree_sign=u'\N{DEGREE SIGN}'
    temp = ("%.1f" % (temp))
    temp1 = str(temp) + " " + degree_sign + "C"
    label8.config(text = temp1)

    humid = ("%.1f" % (humid))
    humid1 = str(humid) + " %rH"
    label9.config(text = humid1)

    lux1 = str(lux) + " Lux"
    label10.config(text = lux1)

    analog = data[30]        

def scanForDevices():
    #print("Scanning...")
    return(adapter.scan(3,True))
    
def findAddress(endNode, adapter1):
    endNode = "FF-" + endNode
    #print(devices)
    for i in range(len(devices)):
        if(devices[i]['name'] == endNode):
            #print(devices[i]['address'])
            return(devices[i]['address'])
    #print("Device not present")
    return("null")

def setOutputs (nodeID, outputs):

        mac = findAddress(nodeID, adapter)
        #print "mac"
        #print mac
	
	#print outputs
	if(mac != 'null'):
		print('connecting!')
		connection = tryConnect(adapter, mac)
		print('connected!')
		writeCommand(connection, nodeID, outputs)
	
        connection.disconnect()
	
		

def sel():
   adapter = pygatt.backends.GATTToolBackend()
   adapter.reset()
   adapter.start() 
   position = var.get()
   position1 = str(position)
   degree_sign=u'\N{DEGREE SIGN}'   
   selection = "Rotation = " + str(position) + " " + degree_sign
   label.config(text = selection)
   #print(str(position))
   if(position<100):
    position1 = '0' + str(position)
    if (position<9):
     position1 = '0' + str(position1)
     
   index = lb1.curselection()[0]
   #print "index"
   #print index
   seltext =lb1.get(index)
   nodeID = seltext
   nodeID1 = nodeID.split("-")
   #print "nodeID1[1]"
   #print nodeID1[1]
   nodeID2 = nodeID1[1]
   output = nodeID2 + '6' + position1
   setOutputs(nodeID2, output) 
   
def sel1():
   scan()

def sel3():
    adapter = pygatt.backends.GATTToolBackend()
    adapter.reset()
    adapter.start()
    index = lb1.curselection()[0]
    seltext =lb1.get(index)
    nodeID = seltext
    nodeID1 = nodeID.split("-")
    #print "name1"
    #print nodeID1[1]
    nodeID2 = nodeID1[1]
    mac = findAddress(nodeID2, adapter)
    #print "address1"
    #print mac
    device = BLEdevice(nodeID2, mac, 5, '0001305')
    myThread(device.deviceCount, device)
    

def sel2():
   adapter = pygatt.backends.GATTToolBackend()
   adapter.reset()
   adapter.start() 
   if (green.get()==1):
       LED1 = 0
   else:
       LED1 = 1
       
   if (yellow.get()==1):
       LED2 = 0
   else:
       LED2 = 1
       
   if (red.get()==1):
       LED3 = 0
   else:
       LED3 = 1       
       
   p0_15 = 0
   p0_27 = 0
	
   value = 0
   value = value | (LED1    <<	0)
   value = value | (LED2    <<	1)
   value = value | (LED3    <<	2)
   value = value | (p0_15   <<	3)
   value = value | (p0_27   <<	4)

   output = chr(value)

   index = lb1.curselection()[0]
   #print output
   seltext =lb1.get(index)
   nodeID = seltext
   nodeID1 = nodeID.split("-")
   #print "nodeID1[1]"
   #print nodeID1[1]
   nodeID2 = nodeID1[1]   
   output = nodeID2 + '3' + chr(value)
   setOutputs(nodeID2, output)

def scan():
   global devices
   adapter = pygatt.backends.GATTToolBackend()
   adapter.reset()
   adapter.start()
   devices = scanForDevices()
   #print(devices)
   lb1.delete(0, END)
   for i in range(len(devices)):
        #print(devices[i]['name'])
        lb1.insert(i, devices[i]['name'])  
   
   
root = Tk()
adapter = pygatt.backends.GATTToolBackend()
adapter.reset()
adapter.start()
#devices = scanForDevices()

button1 = Button(root, text="Start Scan", command=sel1)
button1.grid(row=2, column=1, padx=1, pady=1)

var1 = StringVar()
label1 = Label(root, textvariable=var1)
var1.set("FireFlies nearby (select one):")
label1.grid(row=2, column=2, padx=1, pady=1, sticky = EW)

#Setting it up
img = ImageTk.PhotoImage(Image.open("FF_logo.png"))
#Displaying it
imglabel = Label(root, image=img).grid(row=0, column=1)

sep3 = Frame(root, height=2, width=700, bd=1, relief=SUNKEN)
sep3.grid(row=1, column=0, columnspan=4, padx=5, pady=5)

lb1 = Listbox(root, height=5)
lb1.grid(row=3, column=2, padx=1, pady=5, sticky = S)

sep2 = Frame(root, height=2, width=700, bd=1, relief=SUNKEN)
sep2.grid(row=6, column=0, columnspan=4, padx=5, pady=5)

var2 = StringVar()
label2 = Label(root, textvariable=var2)
var2.set("Move servo motor[degree]:")
label2.grid(row=12, column=1, padx=5, pady=5)

var = IntVar()
scale = Scale( root, variable = var, from_=0, to=180, orient=HORIZONTAL, resolution=1, length = 500, activebackground='#000fff000')
scale.grid(row=12, column=2, padx=5, pady=5)

button = Button(root, text="Move motor", command=sel)
button.grid(row=14, column=2, padx=1, pady=1)

label = Label(root)
label.grid(row=15, column=2, padx=1, pady=1)

sep1 = Frame(root, height=2, width=700, bd=1, relief=SUNKEN)
sep1.grid(row=16, column=0, columnspan=4, padx=5, pady=5)

var3 = StringVar()
label3 = Label(root, textvariable=var3)
var3.set("LED:")
label3.grid(row=17, column=1, padx=1, pady=1)

red = IntVar()
yellow = IntVar()
green = IntVar()

C1 = Checkbutton(root, text = "red", variable = red, \
                 onvalue = 1, offvalue = 0, height=1, \
                 width = 5, anchor="w", bg="red")
C1.grid(row=18, column=2, padx=1, pady=1, sticky = SW)

C2 = Checkbutton(root, text = "yellow", variable = yellow, \
                 onvalue = 1, offvalue = 0, height=1, \
                 width = 5, anchor="w", bg="yellow")
C2.grid(row=19, column=2, padx=1, pady=1, sticky = SW)

C3 = Checkbutton(root, text = "green", variable = green, \
                 onvalue = 1, offvalue = 0, height=1, \
                 width = 5, anchor="w", bg="green")
C3.grid(row=20, column=2, padx=1, pady=1, sticky = SW)

button2 = Button(root, text="Set LED", command=sel2)
button2.grid(row=17, column=2, padx=5, pady=5)

sep = Frame(root, height=2, width=700, bd=1, relief=SUNKEN)
sep.grid(row=21, column=0, columnspan=4, padx=5, pady=5)

var4 = StringVar()
label4 = Label(root, textvariable=var4)
var4.set("Sensor data:")
label4.grid(row=23, column=1, padx=1, pady=1)

button3 = Button(root, text="Retrieve data", command=sel3)
button3.grid(row=23, column=2, padx=5, pady=5)

var5 = StringVar()
label5 = Label(root, textvariable=var5)
var5.set("Temperature:")
label5.grid(row=24, column=2, padx=1, pady=1, sticky = SW)

label8 = Label(root)
label8.grid(row=24, column=2, padx=1, pady=1)

var6 = StringVar()
label6 = Label(root, textvariable=var6)
var6.set("Humidity:")
label6.grid(row=25, column=2, padx=1, pady=1, sticky = SW)

label9 = Label(root)
label9.grid(row=25, column=2, padx=1, pady=1)

var7 = StringVar()
label7 = Label(root, textvariable=var7)
var7.set("Illuminance:")
label7.grid(row=26, column=2, padx=1, pady=1, sticky = SW)

label10 = Label(root)
label10.grid(row=26, column=2, padx=1, pady=1)

sep4 = Frame(root, height=2, width=700, bd=1, relief=SUNKEN)
sep4.grid(row=35, column=0, columnspan=4, padx=5, pady=5)

#Setting it up
img1 = ImageTk.PhotoImage(Image.open("LTEK_logo.png"))
#Displaying it
imglabel1 = Label(root, image=img1).grid(row=36, column=3, padx=10, pady=1, sticky = W)

sep5 = Frame(root, height=2, width=700, bd=1, relief=SUNKEN)
sep5.grid(row=37, column=0, columnspan=4, padx=1, pady=1)

var8 = StringVar()
label11 = Label(root, textvariable=var8)
var8.set("For more info, visit: ")
label11.grid(row=38, column=2, padx=89, pady=1, sticky = W)
link = Label(root, text="FireFly-IoT.com", fg="blue", cursor="hand1")
link.bind("<Button-1>", callback)
link.grid(row=38, column=2, padx=1, pady=1)

var9 = StringVar()
label12 = Label(root, textvariable=var9)
var9.set("Tutorials can be found: ")
label12.grid(row=39, column=2, padx=90, pady=1, sticky = W)
link1 = Label(root, text="here", fg="blue", cursor="hand2")
link1.bind("<Button-1>", callback1)
link1.grid(row=39, column=2, padx=0, pady=1)

sep6 = Frame(root, height=2, width=700, bd=1, relief=SUNKEN)
sep6.grid(row=40, column=0, columnspan=4, padx=1, pady=1)


root.wm_title("FireFly_control FlyTag")
root.mainloop()
