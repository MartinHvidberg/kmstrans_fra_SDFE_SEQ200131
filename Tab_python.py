# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI\Tab_python.ui'
#
# Created: Tue May 28 11:30:20 2013
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

class Ui_tab_python(object):
    def setupUi(self, tab_python):
        tab_python.setObjectName(_fromUtf8("tab_python"))
        tab_python.resize(652, 391)
        self.verticalLayout = QtGui.QVBoxLayout(tab_python)
        self.verticalLayout.setContentsMargins(15, 15, 15, 10)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.txt_python_out = QtGui.QTextEdit(tab_python)
        self.txt_python_out.setReadOnly(True)
        self.txt_python_out.setObjectName(_fromUtf8("txt_python_out"))
        self.verticalLayout.addWidget(self.txt_python_out)
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.bt_python_run = QtGui.QPushButton(tab_python)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bt_python_run.sizePolicy().hasHeightForWidth())
        self.bt_python_run.setSizePolicy(sizePolicy)
        self.bt_python_run.setObjectName(_fromUtf8("bt_python_run"))
        self.horizontalLayout_7.addWidget(self.bt_python_run)
        self.bt_python_load = QtGui.QPushButton(tab_python)
        self.bt_python_load.setObjectName(_fromUtf8("bt_python_load"))
        self.horizontalLayout_7.addWidget(self.bt_python_load)
        self.chb_python_process_enter = QtGui.QCheckBox(tab_python)
        self.chb_python_process_enter.setChecked(True)
        self.chb_python_process_enter.setObjectName(_fromUtf8("chb_python_process_enter"))
        self.horizontalLayout_7.addWidget(self.chb_python_process_enter)
        self.chb_python_clear = QtGui.QCheckBox(tab_python)
        self.chb_python_clear.setChecked(True)
        self.chb_python_clear.setObjectName(_fromUtf8("chb_python_clear"))
        self.horizontalLayout_7.addWidget(self.chb_python_clear)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_7)

        self.retranslateUi(tab_python)
        QtCore.QObject.connect(self.chb_python_process_enter, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.chb_python_clear.setChecked)
        QtCore.QMetaObject.connectSlotsByName(tab_python)

    def retranslateUi(self, tab_python):
        tab_python.setWindowTitle(_translate("tab_python", "Form", None))
        self.txt_python_out.setWhatsThis(_translate("tab_python", "Python output from interactive sessions will be displayed in this field.", None))
        self.bt_python_run.setToolTip(_translate("tab_python", "Compile/run input code", None))
        self.bt_python_run.setWhatsThis(_translate("tab_python", "Compile input code. Used to enter definitions/code which span several lines (uncheck the REPL mode checkbox). ", None))
        self.bt_python_run.setText(_translate("tab_python", "compile", None))
        self.bt_python_load.setWhatsThis(_translate("tab_python", "Load a script for editing.", None))
        self.bt_python_load.setText(_translate("tab_python", "load script", None))
        self.chb_python_process_enter.setToolTip(_translate("tab_python", "REPL mode on/off", None))
        self.chb_python_process_enter.setWhatsThis(_translate("tab_python", "Check this box if you want to run in an interactive mode with instant response to each command. ", None))
        self.chb_python_process_enter.setText(_translate("tab_python", "Run command on enter (REPL mode)", None))
        self.chb_python_clear.setWhatsThis(_translate("tab_python", "Clear input code if it did not result in a error. Useful in interactive (REPL) mode. A command history is maintained and available by using up/down arrows.", None))
        self.chb_python_clear.setText(_translate("tab_python", "Clear input code on succes", None))

