# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'translator.ui'
#
# Created: Thu Mar 14 14:19:19 2013
#      by: PyQt4 UI code generator 4.9.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_TranslatorWidget(object):
    def setupUi(self, TranslatorWidget):
        TranslatorWidget.setObjectName(_fromUtf8("TranslatorWidget"))
        TranslatorWidget.resize(789, 481)
        self.verticalLayout = QtGui.QVBoxLayout(TranslatorWidget)
        self.verticalLayout.setContentsMargins(15, 15, 25, 15)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_4 = QtGui.QLabel(TranslatorWidget)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout.addWidget(self.label_4)
        spacerItem = QtGui.QSpacerItem(20, 18, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lbl_system_info = QtGui.QLabel(TranslatorWidget)
        self.lbl_system_info.setObjectName(_fromUtf8("lbl_system_info"))
        self.gridLayout.addWidget(self.lbl_system_info, 1, 0, 1, 1)
        self.txt_wkt = QtGui.QTextEdit(TranslatorWidget)
        self.txt_wkt.setObjectName(_fromUtf8("txt_wkt"))
        self.gridLayout.addWidget(self.txt_wkt, 8, 2, 1, 1)
        self.txt_proj4 = QtGui.QLineEdit(TranslatorWidget)
        self.txt_proj4.setObjectName(_fromUtf8("txt_proj4"))
        self.gridLayout.addWidget(self.txt_proj4, 5, 0, 1, 1)
        self.label_5 = QtGui.QLabel(TranslatorWidget)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 4, 0, 1, 1)
        self.txt_mlb = QtGui.QLineEdit(TranslatorWidget)
        self.txt_mlb.setObjectName(_fromUtf8("txt_mlb"))
        self.gridLayout.addWidget(self.txt_mlb, 5, 2, 1, 1)
        self.label_10 = QtGui.QLabel(TranslatorWidget)
        self.label_10.setText(_fromUtf8(""))
        self.label_10.setPixmap(QtGui.QPixmap(_fromUtf8(":/newPrefix/varrow.png")))
        self.label_10.setAlignment(QtCore.Qt.AlignCenter)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.gridLayout.addWidget(self.label_10, 6, 2, 1, 1)
        self.label = QtGui.QLabel(TranslatorWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(TranslatorWidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 4, 2, 1, 1)
        self.label_2 = QtGui.QLabel(TranslatorWidget)
        self.label_2.setText(_fromUtf8(""))
        self.label_2.setPixmap(QtGui.QPixmap(_fromUtf8(":/newPrefix/harrow.png")))
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 5, 1, 1, 1)
        self.label_11 = QtGui.QLabel(TranslatorWidget)
        self.label_11.setText(_fromUtf8(""))
        self.label_11.setPixmap(QtGui.QPixmap(_fromUtf8(":/newPrefix/varrow.png")))
        self.label_11.setAlignment(QtCore.Qt.AlignCenter)
        self.label_11.setObjectName(_fromUtf8("label_11"))
        self.gridLayout.addWidget(self.label_11, 1, 2, 1, 1)
        self.txt_epsg = QtGui.QLineEdit(TranslatorWidget)
        self.txt_epsg.setObjectName(_fromUtf8("txt_epsg"))
        self.gridLayout.addWidget(self.txt_epsg, 0, 2, 1, 1)
        self.label_6 = QtGui.QLabel(TranslatorWidget)
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.gridLayout.addWidget(self.label_6, 8, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(70, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 3, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.label_7 = QtGui.QLabel(TranslatorWidget)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.verticalLayout.addWidget(self.label_7)
        self.txt_log = QtGui.QTextEdit(TranslatorWidget)
        self.txt_log.setReadOnly(True)
        self.txt_log.setObjectName(_fromUtf8("txt_log"))
        self.verticalLayout.addWidget(self.txt_log)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        spacerItem3 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)

        self.retranslateUi(TranslatorWidget)
        QtCore.QMetaObject.connectSlotsByName(TranslatorWidget)

    def retranslateUi(self, TranslatorWidget):
        TranslatorWidget.setWindowTitle(QtGui.QApplication.translate("TranslatorWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("TranslatorWidget", "Type a definition and hit enter in the text field to translate. The wkt to mini label translation is still \'shaky\'....", None, QtGui.QApplication.UnicodeUTF8))
        self.lbl_system_info.setText(QtGui.QApplication.translate("TranslatorWidget", "System description:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("TranslatorWidget", "Proj4 definition", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("TranslatorWidget", "EPSG definition", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("TranslatorWidget", "Mini label", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("TranslatorWidget", "WKT definition   ", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("TranslatorWidget", "Messages (implement handleCallBack in your widget to handle messages from TrLib)", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
