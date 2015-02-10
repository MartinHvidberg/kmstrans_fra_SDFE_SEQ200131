# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI\Dialog_affine.ui'
#
# Created: Tue Feb 10 12:46:25 2015
#      by: PyQt4 UI code generator 4.11.3
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
        Dialog.resize(568, 362)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.textBrowser = QtGui.QTextBrowser(Dialog)
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.verticalLayout.addWidget(self.textBrowser)
        self.layout_horizontal = QtGui.QHBoxLayout()
        self.layout_horizontal.setObjectName(_fromUtf8("layout_horizontal"))
        self.verticalLayout.addLayout(self.layout_horizontal)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.chb_apply_interactive = QtGui.QCheckBox(Dialog)
        self.chb_apply_interactive.setObjectName(_fromUtf8("chb_apply_interactive"))
        self.horizontalLayout.addWidget(self.chb_apply_interactive)
        self.chb_apply_f2f = QtGui.QCheckBox(Dialog)
        self.chb_apply_f2f.setObjectName(_fromUtf8("chb_apply_f2f"))
        self.horizontalLayout.addWidget(self.chb_apply_f2f)
        self.bt_apply = QtGui.QPushButton(Dialog)
        self.bt_apply.setObjectName(_fromUtf8("bt_apply"))
        self.horizontalLayout.addWidget(self.bt_apply)
        self.bt_cancel = QtGui.QPushButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.bt_cancel.sizePolicy().hasHeightForWidth())
        self.bt_cancel.setSizePolicy(sizePolicy)
        self.bt_cancel.setObjectName(_fromUtf8("bt_cancel"))
        self.horizontalLayout.addWidget(self.bt_cancel)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Affine transformations", None))
        self.textBrowser.setHtml(_translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Setup affine transformations, e.g. for System34 layers which have inverted x-axis.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">The affine transformations will be applied before and after the coordinate reference system transformations as:</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\"> (x,y,z)=R*(x,y,z)+T, where R is a matrix (e.g. a rotation matrix) and T is a translation.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">To invert x-axis only, e.g. for System34, set first element of the R-matrix to -1, and all other diagonal elements to 1 (a button does this).</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">To only apply a 2D affine transformation, modify only the upper left (x-y) part of the matrix and translation vector.</span></p></body></html>", None))
        self.chb_apply_interactive.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Check this to apply modifications in the interactive tab - for experimentation etc.</p></body></html>", None))
        self.chb_apply_interactive.setText(_translate("Dialog", "Apply modifications in interactive tab", None))
        self.chb_apply_f2f.setWhatsThis(_translate("Dialog", "<html><head/><body><p>Check this to apply affine modifications in batch mode, when transforming datasources.</p></body></html>", None))
        self.chb_apply_f2f.setText(_translate("Dialog", "Apply modifications in batch tab", None))
        self.bt_apply.setToolTip(_translate("Dialog", "<html><head/><body><p>Click to apply changes.</p></body></html>", None))
        self.bt_apply.setText(_translate("Dialog", "Apply", None))
        self.bt_cancel.setText(_translate("Dialog", "Cancel", None))

