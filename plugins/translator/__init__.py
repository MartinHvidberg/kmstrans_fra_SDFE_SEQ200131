__version__="1.0"
__author__="Simlk"
__about__="A srs metadata translation plugin"
def getWidget(mainWindow):
	from widget_plugin import TranslatorWidget
	return TranslatorWidget(mainWindow)
def getName():
	return "Translator"
def startPlugin(mainWindow):
	pass 