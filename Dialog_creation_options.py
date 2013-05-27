# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI\Dialog_creation_options.ui'
#
# Created: Mon May 27 14:42:20 2013
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
        Dialog.setWindowTitle(_translate("Dialog", "Creation options", None))
        self.label_5.setText(_translate("Dialog", "Enter creation options as a , (comma)  separated list of KEY=VALUE pairs (refer to the OGR formats documentation).", None))
        self.label.setText(_translate("Dialog", "Dataset creation option(s):", None))
        self.label_2.setText(_translate("Dialog", "Layer creation options(s):", None))
        self.label_3.setText(_translate("Dialog", "OGR format:", None))
        self.lbl_format.setText(_translate("Dialog", "frmt", None))
        self.label_4.setText(_translate("Dialog", "Short OGR code:", None))
        self.lbl_format_short.setText(_translate("Dialog", "frmt", None))

