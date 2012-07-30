# http://www.qtcentre.org/threads/41621-Resetting-a-QSlider-with-double-click
# http://rowinggolfer.blogspot.co.nz/2009/01/implimenting-custom-widget-using-pyqt4.html
# http://stackoverflow.com/questions/4151637/pyqt4-drag-and-drop-files-into-qlistwidget
# http://www.qsl.net/d/dl4yhf/speclab/specdisp.htm

from PyQt4 import QtGui, QtCore,Qt

import decoder
import psyco
from struct import pack, unpack
from math import sin,cos,radians,log10,pow
from sys import argv,exit
from pyaudio import PyAudio
from cStringIO import StringIO
from time import sleep
from ctypes import c_bool
# from mytest2 import play

from numpy.fft import fft
from numpy import angle#,blackman

from multiprocessing import Value, Lock, Process

playing=Value(c_bool)
playing.value=False
# print playing.value

psyco.full()

def init1():
	global bufsize, wf, p,  ang,volume,datalen,maxarray,phaarray,prevmaxarray
	global Playing,Running,power
	
	power=1.0
	Playing=useLogScale=False
	Running=True
	volume=1.0
	ang=0
	bufsize = 2048
	datalen=bufsize
	phaarray=[0]*(bufsize/2)#for store phase
	maxarray=[0]*(bufsize/2)#for store ampli
	prevmaxarray=[0]*(bufsize/2)#for store ampli
	# bmw=blackman(bufsize)
	p = PyAudio() #make a pyaudio

def loadfile(file):
	global wf, stream
	try:
		stream.close() #close le stream
		wf.close() #close le wave-like object
	except:
		pass
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
	global ang,data,maxarray,phaarray,datalen,bufsize,prevmaxarray
	
	
	L_temp=0
	R_temp=0

	ang=(ang+0)%360
	# print ang
	data = wf.readframes(bufsize)
	
	if 	wf.getnchannels() ==1:
		datalen= len(data)/2
	else:
		datalen= len(data)/4
	# print datalen
	
	
	L=[0]*datalen#for store L ch samples
	Lw=[0]*datalen#windowed version of L
	R=[0]*datalen
	Rw=[0]*datalen
	
	#unpack le data
	if 	wf.getnchannels() ==1: #upscale mono to stereo
		for i in range(0,datalen/2):
			# print i
			L[i*2]=unpack('h',data[(i*2):((i*2)+2)])[0]
			R[i*2+1]=unpack('h',data[(i*2):((i*2)+2)])[0]
			L[i*2]=L[i*2]*0.707*volume #0.707 is needed to achieve same volume of 1ch played through 2ch
			R[i*2+1]=R[i*2+1]*0.707*volume #which is half the sqrt of two
			
	else:#unpack stereo data into separate arrays of Left & right
		for i in xrange(0,datalen*2):
			if(i%2==0):
				L[i/2]=unpack('h',data[(i*2):((i*2)+2)])[0]*volume #[0] is needed because for some reason unpack returns a tuple
				
			else:
				R[i/2]=unpack('h',data[(i*2):((i*2)+2)])[0]*volume #else use the : operator as with mono, but makes an empty array then adds elements to it, which mite b bad 4 preformance
				# maxarray[i/2]=max(L[i/2],R[i/2])*bmw[i/2]#apply blackmann window
				
			
	for i in xrange(0,datalen): #perform stereo field rotation, uses 2% cpu
		L_temp=L[i]*cos(radians(ang))-R[i]*sin(radians(ang))
		R_temp=L[i]*sin(radians(ang))+R[i]*cos(radians(ang))
		L[i]=L_temp
		R[i]=R_temp
	
	
	for i in xrange(0,datalen):
		Lw[i]=L[i]*(1-((abs((datalen/2)-0.5-i))/((datalen/2)-0.5)))#apply triangle window
		Rw[i]=R[i]*(1-((abs((datalen/2)-0.5-i))/((datalen/2)-0.5)))
	# outfft=fft(maxarray)
	
	Lfft=fft(Lw)#compute FFT of windowed samples
	Lpha=angle(Lfft)#extract angle data from FFT
	Rfft=fft(Rw)
	Rpha=angle(Rfft)
	
	for i in xrange(0,datalen/2):
		phaarray[i]=abs(Lpha[i]-Rpha[i])#compute phase difference
		temp=max ( abs(Lfft[i].real), abs(Rfft[i].real) ) #get the maximum of two channels' FFT
		temp=10*log10(temp/float(datalen)) +40#scale by the number of pointss so that the magnitude does not depend on the length of FFT, he power in decibels by taking 10*log10, +40 so shouldn't be -ve values at 16bit
		
		if temp<(prevmaxarray[i]-1.2): #fixed-decay ballistics
			maxarray[i]=prevmaxarray[i]-1.2
		else:
			maxarray[i]=temp
		
		# if temp<(prevmaxarray[i]): #infinite maximum ballistics
			# maxarray[i]=prevmaxarray[i]
		# else:
			# maxarray[i]=temp
		
		prevmaxarray[i]=maxarray[i] #both ballistics above need this line
		
		# maxarray[i]=(prevmaxarray[i]+temp)/2 #average with 1ref ballistics
		# prevmaxarray[i]=temp
		

	file_str = StringIO()
	
	#repack le data from L&R ch
	for i in xrange(0,datalen*2):
		if(i%2==0):
			file_str.write(pack('h',L[i/2]))
		else:
			file_str.write(pack('h',R[i/2]))
			
	data=file_str.getvalue()
	stream.write(data)#plays the data

class ResettingSlider(QtGui.QSlider):
	def setRSV(self,rsv):
		self.resetvalue=rsv
	
	def mouseDoubleClickEvent(self, event):
		self.setValue(self.resetvalue)

class SpectrumWidget(QtGui.QWidget):
	def paintEvent(self, e):
		qp = QtGui.QPainter()
		qp.begin(self)
		# qp.setRenderHint(QtGui.QPainter.Antialiasing)
		self.drawBackground(qp)
		self.drawLines(qp)
		qp.end()

	def drawBackground(self, qp):
		size = self.size()
		w = size.width()
		h = size.height()
		
		backgroundrect=QtCore.QRect(0,0,w,h)
		qp.setBrush(QtCore.Qt.SolidPattern)
		qp.drawRect(backgroundrect)
		
		
	def drawLines(self, qp):
		global maxarray,datalen,power
		somegreen=QtGui.QColor(150,200,100)
		apen=QtGui.QPen()
		apen.setColor(somegreen)
		apen.setWidth(2)
		qp.setPen(apen)
		size = self.size()
		w = float(size.width())
		h = float(size.height())

		for i in xrange(0,datalen/2):
			x=float(i)
			p1=QtCore.QPointF((x/(datalen/2))*w,h)
			# p2=QtCore.QPointF((x/(datalen/2))*w,h-(maxarray[i]/80)*h)
			p2=QtCore.QPointF((x/(datalen/2))*w,h-(maxarray[int((pow(x,power)/pow(datalen/2,power))*datalen/2 )]/80)*h)
			# print int((pow(x,2)/pow(datalen/2,2))*datalen/2 )
			qp.drawLine(p1,p2)




class Example(QtGui.QMainWindow):
	
	def __init__(self):
		super(Example, self).__init__()
		print "5"
		self.initUI()
		
	def end(self):
		global Running
		Running=False
		self.close()
	
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

		# vbox= QtGui.QVBoxLayout()
		# vbox.addWidget(graph)
		# self.setLayout(vbox)
		awidget=SpectrumWidget()
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
		
		volslider = ResettingSlider(QtCore.Qt.Horizontal)
		volslider.setRSV(100)
		volslider.setTickInterval(10)
		volslider.setTickPosition(volslider.TicksBelow)
		volslider.setStatusTip("volume slider")
		volslider.setRange(0,100)
		volslider.setValue(100)
		volslider.valueChanged.connect(self.setVolume)
		volslider.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
		
		powslider = ResettingSlider(QtCore.Qt.Horizontal)
		powslider.setRSV(100)
		powslider.setStatusTip("scale slider")
		powslider.setRange(100,500)
		powslider.setValue(100)
		powslider.valueChanged.connect(self.setPower)
		
		
		sfrslider = ResettingSlider(QtCore.Qt.Horizontal)
		sfrslider.setRSV(0)
		sfrslider.setStatusTip("rotation")
		sfrslider.setRange(-180,180)
		sfrslider.setValue(0)
		sfrslider.valueChanged.connect(self.setAngle)
		sfrslider.setTickInterval(45)
		sfrslider.setTickPosition(sfrslider.TicksBelow)
		

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
		
		
		
		toolbar2=QtGui.QToolBar('fish',self)
		self.addToolBar(QtCore.Qt.BottomToolBarArea,toolbar2)
		toolbar2.setMovable(False)
		toolbar2.addWidget(powslider)
		toolbar2.addWidget(sfrslider)
		# powslider
		
		# toolbar2.setAllowedAreas(QtCore.Qt.BottomToolBarArea)
		# toolbar2.addSeparator ()
		
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
		
		self.setGeometry(300, 300, 800, 500)
		self.setWindowTitle('Main window')	
		self.show()
	
	def setPower(self):
		global power
		sender = self.sender()
		power= (float(sender.value()) / 100.0)
		# self.centralWidget.repaint()
		print power
	
	def setVolume(self):
		global volume
		sender = self.sender()
		volume= (float(sender.value()) / 100.0)
		print volume
	
	def setAngle(self):
		global ang
		sender = self.sender()
		ang= sender.value()
		print ang
	print "7"



def nActionMethod():
	print "nanoha!"

def playActionMethod():
	global Playing
	Playing=not Playing

def main():
	init1()
	print "1"
	app = QtGui.QApplication(argv)
	print "2"
	ex = Example()
	qcw=ex.centralWidget()
	while(Running):
		app.processEvents()
		if(Playing):
			qcw.repaint()
			# play()
			try:
				play()
			except:
				print "exception happened"
		else:
			sleep(0.01)
			continue
	print "4"
	# exit(app.exec_())
	exit(0)

if __name__ == '__main__':
	main()