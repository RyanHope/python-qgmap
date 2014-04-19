#!/usr/bin/python3

from PySide import QtCore, QtGui, QtWebKit, QtNetwork
import os
import decorator

doTrace = False

@decorator.decorator
def trace(function, *args) :
	"""Decorates a function by tracing the begining and
	end of the function execution, if doTrace global is True"""

	if doTrace : print ("> "+function.__name__, args)
	result = function(*args)
	if doTrace : print ("< "+function.__name__, args, "->", result)
	return result

class LoggedPage(QtWebKit.QWebPage):
	@trace
	def javaScriptConsoleMessage(self, msg, line, source):
		print ('JS: %s line %d: %s' % (source, line, msg))


class QGoogleMap(QtWebKit.QWebView) :

	@trace
	def __init__(self, parent, debug=True) :
		super(QGoogleMap, self).__init__(parent)
		if debug :
			QtWebKit.QWebSettings.globalSettings().setAttribute(
				QtWebKit.QWebSettings.DeveloperExtrasEnabled, True)
			self.setPage(LoggedPage())

		self.initialized = False
		self.loadFinished.connect(self.onLoadFinished)

		basePath=os.path.abspath(os.path.dirname(__file__))
		url = 'file://'+basePath+'/qgmap.html'
		self.load(url)

	@trace
	def waitUntilReady(self) :
		while not self.initialized :
			QtGui.QApplication.processEvents()

	@trace
	def onLoadFinished(self, ok) :
		print("onLoadFinished")
		if self.initialized : return
		if not ok :
			print("Error initializing Google Maps")
		self.initialized = True
		self.centerAt(0,0)
		self.setZoom(1)

	@trace
	def runScript(self, script) :
		self.page().mainFrame().evaluateJavaScript(script)


	@trace
	def centerAt(self, latitude, longitude) :
		self.runScript("setGMapCenter({},{})".format(latitude, longitude))

	@trace
	def setZoom(self, zoom) :
		self.runScript("setGMapZoom({})".format(zoom))

	@trace
	def centerAtAddress(self, location) :
		
		url = QtCore.QUrl("http://maps.googleapis.com/maps/api/geocode/xml")
		url.addQueryItem("address", location)
		url.addQueryItem("sensor", "false")
		"""
		url = QtCore.QUrl("http://maps.google.com/maps/geo/")
		url.addQueryItem("q", location)
		url.addQueryItem("output", "csv")
		url.addQueryItem("sensor", "false")
		"""
		request = QtNetwork.QNetworkRequest(url)
		self._accessManager().get(request)

	@trace
	def _accessManager(self) :
		"""Lazy initializer for the network access manager"""
		if not hasattr(self, "_connectionManager") :
			self._connectionManager = QtNetwork.QNetworkAccessManager(self)
			self._connectionManager.finished.connect(self.geocodeReturned)
		return self._connectionManager

	@trace
	def geocodeReturned(self, reply) :
		xml = reply.readAll()
		reader = QtCore.QXmlStreamReader(xml)
		while not reader.atEnd() :
			reader.readNext()
			if reader.name() != "geometry" : continue
			reader.readNextStartElement()
			if reader.name() != "location" : continue
			reader.readNextStartElement()
			if reader.name() != "lat" : continue
			latitude = float(reader.readElementText())
			reader.readNextStartElement()
			if reader.name() != "lng" : continue
			longitude = float(reader.readElementText())
			self.centerAt(latitude, longitude)
			return


if __name__ == '__main__' :

	def go() :
		gmap.centerAtAddress(edit.text())

	app = QtGui.QApplication([])
	w = QtGui.QDialog()
	gmap = QGoogleMap(w)
	gmap.waitUntilReady()
	edit = QtGui.QLineEdit()
	edit.editingFinished.connect(go)
	l = QtGui.QVBoxLayout(w)
	l.addWidget(edit)
	l.addWidget(gmap)
	w.show()
	gmap.centerAt(41.35,2.05)
	gmap.setZoom(13)
	gmap.centerAtAddress("Verdaguer 40, Sant Joan Despí")
	gmap.centerAtAddress("Maragall 1, Santa Coloma de Cervelló")
	gmap.setZoom(17)
	gmap.runScript("getGMapCenter()")

	app.exec_()



