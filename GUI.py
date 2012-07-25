﻿# http://doc.qt.nokia.com/4.7-snapshot/coordsys.html
# http://rowinggolfer.blogspot.co.nz/2009/01/implimenting-custom-widget-using-pyqt4.html
# http://stackoverflow.com/questions/4151637/pyqt4-drag-and-drop-files-into-qlistwidget

import sys
from PyQt4 import QtGui, QtCore

import decoder
from struct import pack, unpack
from math import sin,cos,radians,log,fabs
from sys import argv,exit
from pyaudio import PyAudio
from cStringIO import StringIO
from time import sleep
from ctypes import c_bool

# import msvcrt 

from numpy.fft import fft
from numpy import angle#,blackman

from multiprocessing import Value, Lock, Process

playing=Value(c_bool)
playing.value=False
# print playing.value

def init1():
	global bufsize, wf, p, data, stream,ang,volume,Playing,Running
	Playing=False
	Running=True
	volume=1.0
	ang=0
	bufsize = 4096
	# bmw=blackman(bufsize)
	p = PyAudio() #make a pyaudio

def loadfile(file):
	global wf, stream
	try:
		stream.close() #close le stream
		wf.close() #close le wave-like object
		print "cleaned up"
	except:
		print "did not clean up"
	wf = decoder.open(file, "r") #create a read-onry wave-like obj
	
	if wf.getnchannels() >2:
		print "multichannel files not supported"
		exit(-1)

	# open stream
	stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
		channels = 2,
		rate = wf.getframerate(),
		output = True)

def play():
	global ang,data,maxarray,phaarray,wf
	L=[0]*bufsize#for store L ch samples
	Lw=[0]*bufsize#windowed version of L
	R=[0]*bufsize
	Rw=[0]*bufsize
	phaarray=[0]*(bufsize/2)#for store phase
	maxarray=[0]*(bufsize/2)#for store ampli
	L_temp=0
	R_temp=0

	ang=(ang+0)%360
	# print ang
	data = wf.readframes(bufsize)
	
	if data =='':
		
		wf.setpos(50)
		print str(wf)
	
	#unpack le data
	if 	wf.getnchannels() ==1: #upscale mono to stereo
		try: 
			for i in range(0,bufsize):
				dataarray[i*2:]=unpack('h',data[(i*2):((i*2)+2)])
				dataarray[i*2+1:]=unpack('h',data[(i*2):((i*2)+2)])
				dataarray[i*2]=dataarray[i*2]*0.707*volume #0.707 is needed to achieve same volume of 1ch played through 2ch
				dataarray[i*2+1]=dataarray[i*2+1]*0.707*volume #which is half the sqrt of two
		except:
			pass
	else:#unpack stereo data into separate arrays of Left & right
		try:
			for i in xrange(0,bufsize*2):
				if(i%2==0):
					L[i/2]=unpack('h',data[(i*2):((i*2)+2)])[0]*volume #[0] is needed because for some reason unpack returns a tuple
					
				else:
					R[i/2]=unpack('h',data[(i*2):((i*2)+2)])[0]*volume #else use the : operator as with mono, but makes an empty array then adds elements to it, which mite b bad 4 preformance
					# maxarray[i/2]=max(L[i/2],R[i/2])*(1-((fabs(4095.5-i))/4095.5))#apply triangle window
					# maxarray[i/2]=max(L[i/2],R[i/2])*bmw[i/2]#apply blackmann window
		except:
			pass
			
	for i in xrange(0,bufsize): #perform stereo field rotation, uses 2% cpu
		L_temp=L[i]*cos(radians(ang))-R[i]*sin(radians(ang))
		R_temp=L[i]*sin(radians(ang))+R[i]*cos(radians(ang))
		L[i]=L_temp
		R[i]=R_temp
	
	
	for i in xrange(0,bufsize):
		Lw[i]=L[i]*(1-((fabs((bufsize/2)-0.5-i))/((bufsize/2)-0.5)))#apply triangle window
		Rw[i]=R[i]*(1-((fabs((bufsize/2)-0.5-i))/((bufsize/2)-0.5)))
	# outfft=fft(maxarray)
	
	Lfft=fft(Lw)#compute FFT of windowed samples
	Lpha=angle(Lfft)#extract angle data from FFT
	Rfft=fft(Rw)
	Rpha=angle(Rfft)
	
	for i in xrange(0,bufsize/2):
		phaarray[i]=fabs(Lpha[i]-Rpha[i])#compute phase difference
		maxarray[i]=max ( (Lfft[i].real), (Rfft[i].real) )#get the maximum of two channels' FFT

	file_str = StringIO()
	
	#repack le data from L&R ch
	for i in xrange(0,bufsize*2):
		if(i%2==0):
			file_str.write(pack('h',L[i/2]))
		else:
			file_str.write(pack('h',R[i/2]))
			
	data=file_str.getvalue()
	stream.write(data)#plays the data

class Example(QtGui.QMainWindow):
	
	def __init__(self):
		super(Example, self).__init__()
		print "5"
		self.initUI()
		
	def end(self):
		# super(Example, self).__init__()
		global Running
		Running=False
		self.close()
		
		# nActionMethod()
	# def __init__(self):
	
	
	def showDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file')
		
		print fname
		loadfile(str(fname))
		
	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
		else:
			event.ignore()
	
	
	def dropEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
			l = []
			for url in event.mimeData().urls():
				l.append(str(url.toLocalFile()))
			# self.emit(SIGNAL("dropped"), l)
		else:
			event.ignore()
		print l
		loadfile(str(l[0]))
	

	
	def initUI(self):
		print "6"
		self.statusBar()
		# textEdit = QtGui.QTextEdit()
		# self.setCentralWidget(textEdit)
		awidget=QtGui.QWidget()
		self.setCentralWidget(awidget)
		awidget.setAcceptDrops(True)
		self.setAcceptDrops(True)
		
		nAction = QtGui.QAction('Nanoha', self)
		nAction.setShortcut('N')
		nAction.triggered.connect(nActionMethod)
		nAction.setStatusTip(u'`\(°.o)/´ ┐(￣ー￣)┌ ')
		
		openAction=QtGui.QAction( u"Open File...", self)
		openAction.setStatusTip("actionhelptext")
		openAction.setShortcut("Ctrl+O")
		openAction.triggered.connect(self.showDialog)
		

		
		playAction=QtGui.QAction( u"Play/Pause:\u25b8/||", self)
		playAction.setStatusTip("actionhelptext")
		playAction.setShortcut('c')
		playAction.triggered.connect(playActionMethod)
		u"ffwd:\u23E9 \u23ed rewind : \u23ea \u23ee playpause: \u23ef pause: \u2759\u2759"
		
		
		
		volslider = QtGui.QSlider(QtCore.Qt.Horizontal)
		volslider.setTickInterval(10)
		volslider.setTickPosition(volslider.TicksBelow)
		volslider.setStatusTip("volume slider")
		volslider.setRange(0,100)
		volslider.setValue(100)
		volslider.valueChanged.connect(self.setVolume)
		volslider.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)

		seekbar = QtGui.QSlider(QtCore.Qt.Horizontal)
		seekbar.setStatusTip("seekbar")
		# volslider.sizeHint=QtCore.QSize(600, 150)
		# seekbar.minimumSizeHint=QtCore.QSize(100,1)
		# seekbar.setMinimumSize(QtCore.QSize(100,1))
		
		exitAction = QtGui.QAction( u"Exit", self)
		exitAction.setShortcut('Ctrl+Q')
		exitAction.setStatusTip('Exit application')
		exitAction.triggered.connect(self.end)
		toolbar = self.addToolBar('ponies')
		toolbar.setMovable(False)
		
		toolbar.addAction(nAction)
		toolbar.addAction(openAction)
		toolbar.addAction(playAction)
		toolbar.addSeparator ()
		toolbar.addWidget(volslider)
		toolbar.addSeparator ()
		
		# spacer = QtGui.QLabel("          ")
		# toolbar.addWidget(spacer)

		toolbar.addWidget(seekbar)
		toolbar.addSeparator ()
		toolbar.addAction(exitAction)

		menubar = self.menuBar()
		fileMenu = menubar.addMenu('&File')
		fileMenu.addAction(nAction)
		fileMenu.addAction(openAction)
		fileMenu.addAction(exitAction)
		
		self.setGeometry(300, 300, 600, 250)
		self.setWindowTitle('Main window')	
		self.show()
	
	def setVolume(self):
		global volume
		sender = self.sender()
		volume= (float(sender.value()) / 100.0)
		print volume
	print "7"
		

def nActionMethod():
	print "nanoha!"

def playActionMethod():
	global Playing
	Playing=not Playing
	print Playing

def main():
	init1()
	print "1"
	app = QtGui.QApplication(sys.argv)
	print "2"
	ex = Example()
	while(Running):
		app.processEvents()
		if(Playing):
			play()
		else:
			sleep(0.01)
			continue
	print "4"
	# sys.exit(app.exec_())
	exit(0)
	


if __name__ == '__main__':
	main() 