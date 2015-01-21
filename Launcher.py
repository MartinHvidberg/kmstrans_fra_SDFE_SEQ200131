# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI\Launcher.ui'
#
# Created: Wed Jan 21 10:08:44 2015
#      by: PyQt4 UI code generator 4.10
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_LauncherWindow(object):
    def setupUi(self, LauncherWindow):
        LauncherWindow.setObjectName(_fromUtf8("LauncherWindow"))
        LauncherWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(LauncherWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.txt_log = QtGui.QTextEdit(self.centralwidget)
        self.txt_log.setObjectName(_fromUtf8("txt_log"))
        self.verticalLayout.addWidget(self.txt_log)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.bt_geoids = QtGui.QPushButton(self.centralwidget)
        self.bt_geoids.setObjectName(_fromUtf8("bt_geoids"))
        self.horizontalLayout.addWidget(self.bt_geoids)
        self.bt_launch = QtGui.QPushButton(self.centralwidget)
        self.bt_launch.setObjectName(_fromUtf8("bt_launch"))
        self.horizontalLayout.addWidget(self.bt_launch)
        self.bt_close = QtGui.QPushButton(self.centralwidget)
        self.bt_close.setObjectName(_fromUtf8("bt_close"))
        self.horizontalLayout.addWidget(self.bt_close)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        LauncherWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(LauncherWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        LauncherWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(LauncherWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        LauncherWindow.setStatusBar(self.statusbar)

        self.retranslateUi(LauncherWindow)
        QtCore.QMetaObject.connectSlotsByName(LauncherWindow)

    def retranslateUi(self, LauncherWindow):
        LauncherWindow.setWindowTitle(_translate("LauncherWindow", "KMSTrans2 Launcher", None))
        self.bt_geoids.setText(_translate("LauncherWindow", "Select geoid dir", None))
        self.bt_launch.setText(_translate("LauncherWindow", "Launch KMSTrans2", None))
        self.bt_close.setText(_translate("LauncherWindow", "Close", None))

