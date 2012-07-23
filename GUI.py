# http://doc.qt.nokia.com/4.7-snapshot/coordsys.html
# http://rowinggolfer.blogspot.co.nz/2009/01/implimenting-custom-widget-using-pyqt4.html
# http://stackoverflow.com/questions/4151637/pyqt4-drag-and-drop-files-into-qlistwidget

import sys
from PyQt4 import QtGui,QtCore

class Example(QtGui.QMainWindow):
	
	def __init__(self):
		super(Example, self).__init__()
		print "5"
		self.initUI()
		
		
	def showDialog(self):
		
		fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file')
		print fname
		
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
	
	def initUI(self):
		
		print "6"
		self.statusBar()
		# textEdit = QtGui.QTextEdit()
		# self.setCentralWidget(textEdit)
		awidget=QtGui.QWidget()
		self.setCentralWidget(awidget)
		awidget.setAcceptDrops(True)
		self.setAcceptDrops(True)
		
		nAction = QtGui.QAction(QtGui.QIcon('MSLN.png'),'Nanoha', self)
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
		u"ffwd:\u23E9 \u23ed rewind : \u23ea \u23ee playpause: \u23ef pause: \u2759\u2759"
		
		
		
		volslider = QtGui.QSlider(QtCore.Qt.Horizontal)
		volslider.setTickInterval(10)
		volslider.setTickPosition(volslider.TicksBelow)
		volslider.setStatusTip("volume slider")
		# volslider.sizeHint=QtCore.QSize(600, 150)
		# volslider.minimumSizeHint=QtCore.QSize(100,1)
		# volslider.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
		volslider.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Fixed)

		 
		seekbar = QtGui.QSlider(QtCore.Qt.Horizontal)
		seekbar.setStatusTip("seekbar")
		# seekbar.minimumSizeHint=QtCore.QSize(100,1)
		# seekbar.setMinimumSize(QtCore.QSize(100,1))
		
		exitAction = QtGui.QAction( u"Exit", self)
		exitAction.setShortcut('Ctrl+Q')
		exitAction.setStatusTip('Exit application')
		exitAction.triggered.connect(self.close)
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
	print "7"
		

def nActionMethod(self):
		print "nanoha!"

def main():
	print "1"
	app = QtGui.QApplication(sys.argv)
	print "2"
	ex = Example()
	print "3"
	sys.exit(app.exec_())
	print "4"


if __name__ == '__main__':
	main() 