# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI\Dialog_settings_gdal.ui'
#
# Created: Tue May 28 10:56:38 2013
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
        Dialog.resize(859, 224)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_4 = QtGui.QLabel(Dialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout.addWidget(self.label_4)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.rdb_gdal_system = QtGui.QRadioButton(Dialog)
        self.rdb_gdal_system.setObjectName(_fromUtf8("rdb_gdal_system"))
        self.horizontalLayout.addWidget(self.rdb_gdal_system)
        self.rdb_gdal_included = QtGui.QRadioButton(Dialog)
        self.rdb_gdal_included.setChecked(True)
        self.rdb_gdal_included.setObjectName(_fromUtf8("rdb_gdal_included"))
        self.horizontalLayout.addWidget(self.rdb_gdal_included)
        self.rdb_gdal_custom = QtGui.QRadioButton(Dialog)
        self.rdb_gdal_custom.setObjectName(_fromUtf8("rdb_gdal_custom"))
        self.horizontalLayout.addWidget(self.rdb_gdal_custom)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.txt_data_folder = QtGui.QLineEdit(Dialog)
        self.txt_data_folder.setObjectName(_fromUtf8("txt_data_folder"))
        self.gridLayout.addWidget(self.txt_data_folder, 1, 1, 1, 1)
        self.txt_plugin_folder = QtGui.QLineEdit(Dialog)
        self.txt_plugin_folder.setObjectName(_fromUtf8("txt_plugin_folder"))
        self.gridLayout.addWidget(self.txt_plugin_folder, 2, 1, 1, 1)
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.txt_bin_folder = QtGui.QLineEdit(Dialog)
        self.txt_bin_folder.setObjectName(_fromUtf8("txt_bin_folder"))
        self.gridLayout.addWidget(self.txt_bin_folder, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.bt_browse_bin = QtGui.QPushButton(Dialog)
        self.bt_browse_bin.setObjectName(_fromUtf8("bt_browse_bin"))
        self.gridLayout.addWidget(self.bt_browse_bin, 0, 2, 1, 1)
        self.bt_browse_data = QtGui.QPushButton(Dialog)
        self.bt_browse_data.setObjectName(_fromUtf8("bt_browse_data"))
        self.gridLayout.addWidget(self.bt_browse_data, 1, 2, 1, 1)
        self.bt_browse_plugin = QtGui.QPushButton(Dialog)
        self.bt_browse_plugin.setObjectName(_fromUtf8("bt_browse_plugin"))
        self.gridLayout.addWidget(self.bt_browse_plugin, 2, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.bt_apply = QtGui.QPushButton(Dialog)
        self.bt_apply.setObjectName(_fromUtf8("bt_apply"))
        self.horizontalLayout_2.addWidget(self.bt_apply)
        self.bt_cancel = QtGui.QPushButton(Dialog)
        self.bt_cancel.setObjectName(_fromUtf8("bt_cancel"))
        self.horizontalLayout_2.addWidget(self.bt_cancel)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "GDAL settings", None))
        self.label_4.setText(_translate("Dialog", "GDAL installation currently only customizable on windows. ", None))
        self.rdb_gdal_system.setToolTip(_translate("Dialog", "Use a system wide gdal installation", None))
        self.rdb_gdal_system.setText(_translate("Dialog", "Use system gdal", None))
        self.rdb_gdal_included.setToolTip(_translate("Dialog", "Use the included minimal gdal installation", None))
        self.rdb_gdal_included.setText(_translate("Dialog", "Use included gdal", None))
        self.rdb_gdal_custom.setToolTip(_translate("Dialog", "A a customized gdal installation (by selecting folders below).", None))
        self.rdb_gdal_custom.setText(_translate("Dialog", "Use customized gdal", None))
        self.label.setText(_translate("Dialog", "GDAL BIN Folder", None))
        self.txt_data_folder.setToolTip(_translate("Dialog", "Folder containing gdal data files", None))
        self.txt_plugin_folder.setToolTip(_translate("Dialog", "Folder containing plugin libraries", None))
        self.label_2.setText(_translate("Dialog", "GDAL_DATA", None))
        self.txt_bin_folder.setToolTip(_translate("Dialog", "Folder comtaining gdal binary (and binary dependencies)", None))
        self.label_3.setText(_translate("Dialog", "GDAL_DRIVER_PATH", None))
        self.bt_browse_bin.setText(_translate("Dialog", "Browse", None))
        self.bt_browse_data.setText(_translate("Dialog", "Browse", None))
        self.bt_browse_plugin.setText(_translate("Dialog", "Browse", None))
        self.bt_apply.setText(_translate("Dialog", "Apply and restart", None))
        self.bt_cancel.setText(_translate("Dialog", "Cancel", None))

