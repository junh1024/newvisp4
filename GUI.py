# http://www.qtcentre.org/threads/41621-Resetting-a-QSlider-with-double-click
# http://rowinggolfer.blogspot.co.nz/2009/01/implimenting-custom-widget-using-pyqt4.html
# http://stackoverflow.com/questions/4151637/pyqt4-drag-and-drop-files-into-qlistwidget
# http://www.qsl.net/d/dl4yhf/speclab/specdisp.htm

from sys import argv,exit

from PyQt4 import QtGui, QtCore,Qt

import decoder
import psyco
from struct import pack, unpack
from math import sin,cos,radians,log10,pow

from pyaudio import PyAudio
from cStringIO import StringIO
from time import sleep
from ctypes import *
# from mytest2 import play

from numpy.fft import fft
from numpy import angle#,blackman

from multiprocessing import Value, Lock, Process

global Playing,Running
# Playing=Value(c_bool)
# Playing=c_bool(False)
Running=True
Playing=False
# Running=Value(c_bool)
# Running=c_bool(True)
# print playing.value

psyco.full()

def init1():
	global bufsize, wf, p,  ang,volume,datalen,maxarray,phaarray,prevmaxarray,prevphaarray
	global Running,power,doSFR,phasetext,ballisticsmode
	phasetext="detailed"
	ballisticsmode="1-way variable decay"
	wf=None
	power=1.0
	doSFR=True
	
	volume=1.0
	ang=0
	bufsize = 2048
	datalen=bufsize
	phaarray=[0]*(bufsize/2)#for store phase
	maxarray=[0]*(bufsize/2)#for store ampli
	prevmaxarray=[0]*(bufsize/2)#for store ampli
	prevphaarray=[0]*(bufsize/2)#for store ampli
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
	global ang,data,maxarray,phaarray,datalen,bufsize,prevmaxarray,doSFR,ballisticsmode,Playing
	
	L_temp=0
	R_temp=0

	# ang=(ang+5)%360
	data = wf.readframes(bufsize)
	if(data==''):
		Playing=False
		return
	
	if 	wf.getnchannels() ==1:
		datalen= len(data)/2
	else:
		datalen= len(data)/4
	# print datalen
	
	L=[0]*datalen#for store L ch samples
	Lw=[0]*datalen#windowed version of L
	R=[0]*datalen
	Rw=[0]*datalen
	ffttemp=[0]*datalen
	
	#unpack le data
	if 	wf.getnchannels() ==1: #upscale mono to stereo
		for i in range(0,datalen):
			# print i
			L[i]=unpack('h',data[(i*2):((i*2)+2)])[0]*0.707*volume #0.707 is needed to achieve same volume of 1ch played through 2ch
			R[i]=unpack('h',data[(i*2):((i*2)+2)])[0]*0.707*volume #which is half the sqrt of two
			# R[i*2+1]=unpack('h',data[(i*2):((i*2)+2)])[0]
			
	else:#unpack stereo data into separate arrays of Left & right
		for i in xrange(0,datalen*2):
			if(i%2==0):
				L[i/2]=unpack('h',data[(i*2):((i*2)+2)])[0]*volume #[0] is needed because for some reason unpack returns a tuple
				
			else:
				R[i/2]=unpack('h',data[(i*2):((i*2)+2)])[0]*volume #else use the : operator as with mono, but makes an empty array then adds elements to it, which mite b bad 4 preformance
				# maxarray[i/2]=max(L[i/2],R[i/2])*bmw[i/2]#apply blackmann window
	
	if(doSFR):
		for i in xrange(0,datalen): #perform stereo field rotation, uses 2% cpu
			L_temp=L[i]*cos(radians(ang))-R[i]*sin(radians(ang))
			R_temp=L[i]*sin(radians(ang))+R[i]*cos(radians(ang))
			L[i]=L_temp
			R[i]=R_temp
			
	
	for i in xrange(0,datalen): #apply limiting so that it can be packed into short/16bit. Valid for 16bit only.
		if L[i] >32767:
			L[i]=32767
		if R[i] >32767:
			R[i]=32767
		if L[i] <-32767:
			L[i]=-32767
		if R[i] <-32767:
			R[i]=-32767

	
	for i in xrange(0,datalen):
		Lw[i]=L[i]*(1-((abs((datalen/2)-0.5-i))/((datalen/2)-0.5)))#apply triangle window
		Rw[i]=R[i]*(1-((abs((datalen/2)-0.5-i))/((datalen/2)-0.5)))
	# outfft=fft(maxarray)
	
	Lfft=fft(Lw)#compute FFT of windowed samples
	Rfft=fft(Rw)
	
	if(phasetext!="none"):
		Lpha=angle(Lfft)#extract angle data from FFT
		Rpha=angle(Rfft)
		for i in xrange(0,datalen/2): #compute phase apply phase ballistics
			phatemp=abs(Lpha[i]-Rpha[i])#compute phase difference
			
			if phatemp>(prevphaarray[i]+0.2): #fixed-decay ballistics
				phaarray[i]=prevphaarray[i]+0.2
			else:
				phaarray[i]=phatemp

			prevphaarray[i]=phaarray[i]
	
	for i in xrange(0,datalen/2): #compute fft
		ffttemp[i]=max ( abs(Lfft[i].real), abs(Rfft[i].real) ) #get the maximum of two channels' FFT
		try:
			ffttemp[i]=10*log10(ffttemp[i]/float(datalen)) +40#scale by the number of points so that the magnitude does not depend on the length of FFT, he power in decibels by taking 10*log10, +40 so shouldn't be -ve values at 16bit
		except:
			pass
	#algorithms for applying ballistics
	if ballisticsmode ==  "1-way variable decay":#1wvd-decay increases with frequency
		ballisticscoefficient=[0]*(datalen/2)
		for i in xrange(0,datalen/2):
			ballisticscoefficient[i]=1.2+(i*2/(datalen/2))
			
		for i in xrange(0,datalen/2):
			if ffttemp[i]<(prevmaxarray[i]-ballisticscoefficient[i]):
				maxarray[i]=prevmaxarray[i]-ballisticscoefficient[i]
			else:
				maxarray[i]=ffttemp[i]
			prevmaxarray[i]=maxarray[i]
		
	elif ballisticsmode =="1-way fixed decay":#1wfd-decay is doesn't vary with frequency
		for i in xrange(0,datalen/2):
			if ffttemp[i]<(prevmaxarray[i]-1.2):
				maxarray[i]=prevmaxarray[i]-1.2
			else:
				maxarray[i]=ffttemp[i]
			prevmaxarray[i]=maxarray[i]
			
	elif ballisticsmode =="2-way average":
		for i in xrange(0,datalen/2):
			maxarray[i]=(prevmaxarray[i]+ffttemp[i])/2 #average with 1 previous reference
			prevmaxarray[i]=ffttemp[i]
		
	elif ballisticsmode =="infinite maximum":
		for i in xrange(0,datalen/2):
			if ffttemp[i]>(prevmaxarray[i]): #infinite maximum
				maxarray[i]=ffttemp[i]
			prevmaxarray[i]=maxarray[i]
	else:
		for i in xrange(0,datalen/2): #none
			maxarray[i]=ffttemp[i]
			prevmaxarray[i]=maxarray[i]

		
		# if ffttemp>(prevmaxarray[i]+3): #fixed-decay ballistics
			# maxarray[i]=prevmaxarray[i]+3
		# else:
			# maxarray[i]=ffttemp


	file_str = StringIO()
	
	#repack le data from L&R ch
	for i in xrange(0,datalen*2):
	
		if(i%2==0):
			file_str.write(pack('h',L[i/2]))
		else:
			file_str.write(pack('h',R[i/2]))
			
	data=file_str.getvalue()
	stream.write(data)#plays the data

class ResettingSlider(QtGui.QSlider):#if it's double clicked, it resets to a reset value defined here
	def setRSV(self,rsv):
		self.resetvalue=rsv
	
	def mouseDoubleClickEvent(self, event):
		self.setValue(self.resetvalue)

		
		
class SpectrumWidget(QtGui.QWidget):
	def paintEvent(self, e):
		qp = QtGui.QPainter()
		qp.begin(self)
		# qp.setRenderHint(QtGui.QPainter.Antialiasing) #slow as balls
		self.drawBackground(qp)
		if(wf):#if a file is loaded, scale lines are drawn
			self.drawScale(qp)
		self.drawLines(qp)
		qp.end()

	def drawBackground(self, qp):
		size = self.size()
		w = size.width()
		h = size.height()
		
		backgroundrect=QtCore.QRect(0,0,w,h)
		qp.setBrush(QtCore.Qt.SolidPattern)
		qp.drawRect(backgroundrect)
			
	def drawScale(self, qp):
		global wf
		size = self.size()
		w = float(size.width())
		h = float(size.height())
		
		apen=QtGui.QPen()
		apen.setColor(QtGui.QColor(111,111,111))
		qp.setPen(apen) #set colour for drawing scale info
		
		SR= wf.getframerate() #get the sampling rate of file
		
		alist=[] #make array of 2^x where x is 7 to 14, for hertz to plot scale lines
		for i in xrange(7,(14+1)):
			alist.append(2**(i))
		
		for hz in alist: #draw the lines, while compensating for scale slider
			ti = (pow(hz,1/power)/pow(SR/2,1/power))*w
			p1=QtCore.QPointF(ti,0)
			p1a=QtCore.QPointF(ti,20)
			p2=QtCore.QPointF(ti,h)
			qp.drawLine(p1,p2)
			qp.drawText(p1a,str(hz) + " hz")

			
		xpos=(QtGui.QWidget.mapFromGlobal (self, QtGui.QCursor.pos()).x()) #get cursor position relative to current widget
		if(self.underMouse() ):
			
			freq= int((pow(xpos,power)/pow(w,power))*(SR/2))
			qp.drawText( QtCore.QPointF(w-64, 40) , str(freq)+" hz"  ) #draw what frequency is under the mouse

			
	def drawLines(self, qp):
		global maxarray,datalen,power,phasetext
		size = self.size()
		w = float(size.width())
		h = float(size.height())
		
		apen=QtGui.QPen()
		apen.setWidthF(((w)/(datalen/2)  ) + 200*(1/w))
		apen.setColor(QtGui.QColor(150,200,100))
		qp.setPen(apen)

		
		if phasetext == "none":
			for i in xrange(0,datalen/2):
				x=float(i)
				transformedindex=int((pow(x,power)/pow(datalen/2,power))*datalen/2 ) #index for FFT array, compensated for scale slider
				p1=QtCore.QPointF((x/(datalen/2))*w,h)
				p2=QtCore.QPointF((x/(datalen/2))*w,h-(maxarray[transformedindex]/80)*h)
				qp.drawLine(p1,p2)
			
		elif phasetext == "magnified average":
		
			total=0 #average all the phases of all frequencies and make the average larger
			for i in xrange(0,datalen/2):
				total+=phaarray[i]
			total=(total)*4/datalen
			
			apen.setColor(QtGui.QColor(150-(total*1),200-(total*8),100-(total*8)))
			qp.setPen(apen)
		
			for i in xrange(0,datalen/2):
				x=float(i)
				transformedindex=int((pow(x,power)/pow(datalen/2,power))*datalen/2 )
				
				p1=QtCore.QPointF((x/(datalen/2))*w,h)
				p2=QtCore.QPointF((x/(datalen/2))*w,h-(maxarray[transformedindex]/80)*h)
				qp.drawLine(p1,p2)
		else:
			for i in xrange(0,datalen/2):
				x=float(i)
				transformedindex=int((pow(x,power)/pow(datalen/2,power))*datalen/2 )
				apen.setColor(QtGui.QColor(150-(phaarray[transformedindex]*1),200-(phaarray[transformedindex]*8),100-(phaarray[transformedindex]*8))) #phase colours
				qp.setPen(apen)
				p1=QtCore.QPointF((x/(datalen/2))*w,h)
				p2=QtCore.QPointF((x/(datalen/2))*w,h-(maxarray[transformedindex]/80)*h)
				qp.drawLine(p1,p2)


class Example(QtGui.QMainWindow):
	def __init__(self):
		super(Example, self).__init__()
		print "5"
		self.initUI()
		
	def closeEvent(self,whocares):
		global Playing, Running
		Playing=False
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
		
		SFRcb = QtGui.QCheckBox('SFR', self)
		SFRcb.toggle()
		SFRcb.stateChanged.connect(self.setSFR)
		
		PColCombo = QtGui.QComboBox(self)
		PColCombo.addItem("detailed")
		PColCombo.addItem("magnified average")
		PColCombo.addItem("none")
		PColCombo.activated[str].connect(self.setPhaseColours)
		
		BalCombo = QtGui.QComboBox(self)
		BalCombo.addItem("1-way variable decay")
		BalCombo.addItem("1-way fixed decay")
		BalCombo.addItem("2-way average")
		BalCombo.addItem("infinite maximum")
		BalCombo.addItem("none")
		BalCombo.activated[str].connect(self.setBallistics)
		
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
		exitAction.triggered.connect(self.closeEvent)
		
		toolbar = self.addToolBar('ponies')
		toolbar.setMovable(False)
		
		
		
		toolbar2=QtGui.QToolBar('fish',self)
		self.addToolBar(QtCore.Qt.BottomToolBarArea,toolbar2)
		toolbar2.setMovable(False)
		
		LinearLabel = QtGui.QLabel(" Linear ")
		toolbar2.addWidget(BalCombo)
		toolbar2.addWidget(LinearLabel)
		toolbar2.addWidget(powslider)
		LogLabel = QtGui.QLabel(" Semi-Log ")
		toolbar2.addWidget(LogLabel)
		toolbar2.addSeparator ()
		
		PColLabel = QtGui.QLabel(" Phase colours ")
		toolbar2.addWidget(PColLabel)
		toolbar2.addWidget(PColCombo)
		toolbar2.addSeparator ()
		toolbar2.addWidget(SFRcb)
		toolbar2.addWidget(sfrslider)
		
		
		toolbar.addAction(nAction)
		toolbar.addAction(openAction)
		toolbar.addAction(playAction)
		toolbar.addSeparator ()
		toolbar.addWidget(volslider)
		toolbar.addSeparator ()
		
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
		
	def setSFR(self):
		global doSFR
		doSFR= not doSFR
		
	def setPhaseColours(self, text):
		global phasetext
		phasetext=text
		
	def setBallistics(self, text):
		global ballisticsmode
		ballisticsmode=text
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
		qcw.repaint()
		if(Playing and wf):
			
			play()
		else:
			sleep(0.1)
			continue
	print "4"
	# exit(app.exec_())
	exit(0)

if __name__ == '__main__':
	main()