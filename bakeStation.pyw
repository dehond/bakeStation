import tkinter
from tkinter import messagebox
import time
import datetime

import serial
from IPython.display import HTML, clear_output
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import csv
import os, glob
import numpy as np

from math import log

def getPressure(physAddress):
	# Connect to the ion gauge hooked up to physAddress and query for pressure
	try:
		ser = serial.Serial(physAddress, 9600, timeout =  10)
		#ser.open()
		ser.write(b'#0002I1\r')
		ser.flush()
		message = ser.read(11)
		ser.close()
		pressure = float(message[1:-1].decode("utf-8"))
		return pressure
	except:
		#messagebox.showerror("Error", "Couldn't read out over serial connection")
		return 'NaN'
		
def thermistorFun(resistance, R25):
    # Assuming a specific 100 kOhm thermistor, this returns the temperature
    B = 4092.0
    T0 = 298.0
    temperature = B * T0 / (B - T0 * log(R25 / resistance)) - 273
    return temperature

def getTemperature(physAddress):
    # Connect to the Itsy Bitsy reading in the voltage across the thermistor
    R25 = 100.0E3 # Thermistor value
    Rpullup = 100.0E3
    ser = serial.Serial(physAddress, timeout = 5)
    ser.write(b'boguscommand\r\n')
    ser.readline()	# Do a dummy because that's how the Itsy Bitsy be
    message = ser.readline()[:-2]
    ser.close()
    value = float(message)/2**16
    resistance = Rpullup * value / (1 - value)
    temperature = thermistorFun(resistance, R25)
    return temperature

def readCSVFile(filename):
	# Read in data from file named filename
	dum = []
	with open(filename, 'r') as infile:
		reader = csv.reader(infile, delimiter = ',')
		for row in reader:
			dum.append(row)
		# Strip off header
		dum = dum[1:]
	return dum

def appendToCSVFile(filename, data):
	try:
		with open(filename, 'a', newline = '') as outfile:
			writer = csv.writer(outfile)
			writer.writerow(data)
	except:
		messagebox.showerror("Error", "Couldn't write to csv file for some reason")

def updatePlot(fig, ax1, ax2, xdat, ydat1, ydat2):
	ax1.clear()
	ax1.semilogy(xdat, ydat1, 'k')
	ax1.set_ylabel("Pressure (torr)", fontsize=20)
	ax1.set_xlabel("Time and date", fontsize=20)
	if not len(ydat1) == 0:
		ax1.set_ylim((0.5*min(ydat1),2*max(ydat1)))

	ax2.clear()
	ax2.plot(xdat, ydat2, 'r')
	ax2.set_ylabel("Temperature (°C)", fontsize=20, color='r')
	ax2.tick_params('y', colors='r')
	if not len(ydat2) == 0:
		ax2.set_ylim((0.5*min(ydat2),2*max(ydat2)))
	
	ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%d/%m'))
	#fig.tight_layout()
	canvas.draw()

def addPoint(datetimestrs, timestamps, pressure_array, temp_array, physAddressIonGauge, physAddressThermo, fig, ax1, ax2, samplePeriod, filename):
	# Does everything to add a new point and update everything
	pressure = getPressure(physAddressIonGauge)
	temperature = getTemperature(physAddressThermo)
	while pressure == 'NaN':
		pressure = getPressure(physAddressIonGauge)
	reltime = int(time.time())
	nowtime = datetime.datetime.now()
	curtime = time.strftime('%H:%M %d %h %Y')
	
	# Append new data points to existing arrays
	datetimestrs.append(curtime)
	timestamps = np.append(timestamps, nowtime)
	pressure_array = np.append(pressure_array, pressure)
	temp_array = np.append(temp_array, temperature)
	
	# Update plot
	updatePlot(fig, ax1, ax2, timestamps, pressure_array, temp_array)
	
	# Add to file
	appendToCSVFile(filename, [curtime, reltime, pressure, temperature])
	
	# Repeat
	root.after(samplePeriod*1000, addPoint, datetimestrs, timestamps, pressure_array, temp_array, physAddressIonGauge, physAddressThermo, fig, ax1, ax2, samplePeriod, filename)

def _quit():
	# Handles what happens when the 'quit' button is clicked
	figname = 'logfigs/' + filename[8:-4] + '.png'
	plt.savefig(figname)
	root.quit()
	root.destroy()

if __name__ == "__main__":
	# Some configuration parameters, may be set via GUI later
	physAddressIonGauge = 'COM3'
	physAddressThermo = 'COM13'
	samplePeriod = 10	# In seconds
	
	# Open tkinter figure
	root = tkinter.Tk()
	
	# Create directories for data and figures if they don't exist yet
	if not os.path.exists('logdata'):
		os.makedirs('logdata')
	if not os.path.exists('logfigs'):
		os.makedirs('logfigs')
	
	# Should we continue using the old .csv file, or start afresh?
	usePreviousFile = messagebox.askyesno("Continue?", "Continue using previous savefile?")
	if usePreviousFile:
		try:
			# Get most recent file
			filename = glob.glob("logdata/*.csv")[-1]
			# Read in old data
			rawdat = readCSVFile(filename)
			datetimestrs = [x[0] for x in rawdat]
			time_array = np.array( [int(x[1]) for x in rawdat] )
			pressure_array = np.array( [float(x[2]) for x in rawdat] )
			temp_array = np.array( [float(x[3]) for x in rawdat] )
		except:
			messagebox.showerror("Error", "Couldn't open previous file. Starting afresh.")
			# Create new file based on time specification
			filename = 'logdata/' + time.strftime('%Y%m%d_%H%M') + '.csv'
			# Preallocate some variables
			time_array = np.array([])
			pressure_array = np.array([])
			temp_array = np.array([])
			datetimestrs = []
			appendToCSVFile(filename, ['Date and time', 'Epoch time (s)', 'Pressure (torr)', 'Temperature (°C)'])
	else:
		# Create new file based on time specification
		filename = 'logdata/' + time.strftime('%Y%m%d_%H%M') + '.csv'
		# Preallocate some variables
		time_array = np.array([])
		pressure_array = np.array([])
		temp_array = np.array([])
		datetimestrs = []
		appendToCSVFile(filename, ['Date and time', 'Epoch time (s)', 'Pressure (torr)', 'Temperature (°C)'])
	
	timestamps = [datetime.datetime.fromtimestamp(x) for x in time_array]
	
	fig = plt.figure(figsize=(10,7))
	ax1 = fig.add_subplot(1,1,1)
	ax2 = ax1.twinx()
	
	canvas = FigureCanvasTkAgg(fig, master = root)
	canvas.draw()
	canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
	canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
	
	toolbar = NavigationToolbar2Tk(canvas, root)
	toolbar.update()
	canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
	
	button = tkinter.Button(master=root, text="Quit", command=_quit)
	button.pack(side=tkinter.BOTTOM)	
	
	# Add new data points to plot, update everything
	addPoint(datetimestrs, timestamps, pressure_array, temp_array, physAddressIonGauge, physAddressThermo, fig, ax1, ax2, samplePeriod, filename)
	
	# Hand over to tkinter
	root.mainloop()