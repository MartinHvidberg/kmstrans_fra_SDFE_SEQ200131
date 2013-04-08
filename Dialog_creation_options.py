# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI\Dialog_creation_options.ui'
#
# Created: Mon Apr 08 09:09:21 2013
#      by: PyQt4 UI code generator 4.9.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(626, 260)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_5 = QtGui.QLabel(Dialog)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.verticalLayout.addWidget(self.label_5)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label)
        self.txt_dco = QtGui.QLineEdit(Dialog)
        self.txt_dco.setObjectName(_fromUtf8("txt_dco"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.txt_dco)
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.label_2)
        self.txt_lco = QtGui.QLineEdit(Dialog)
        self.txt_lco.setObjectName(_fromUtf8("txt_lco"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.FieldRole, self.txt_lco)
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label_3)
        self.lbl_format = QtGui.QLabel(Dialog)
        self.lbl_format.setObjectName(_fromUtf8("lbl_format"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.lbl_format)
        self.label_4 = QtGui.QLabel(Dialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_4)
        self.lbl_format_short = QtGui.QLabel(Dialog)
        self.lbl_format_short.setObjectName(_fromUtf8("lbl_format_short"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.lbl_format_short)
        self.verticalLayout.addLayout(self.formLayout)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Creation options", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("Dialog", "Enter creation options as a , (comma)  separated list of KEY=VALUE pairs (refer to the OGR formats documentation).", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Dialog", "Dataset creation option(s):", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Dialog", "Layer creation options(s):", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Dialog", "OGR format:", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_format.setText(QtGui.QApplication.translate("Dialog", "frmt", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Dialog", "Short OGR code:", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_format_short.setText(QtGui.QApplication.translate("Dialog", "frmt", None, QtGui.QApplication.UnicodeUTF8))

