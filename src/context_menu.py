import os
from os import path
import json
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QToolTip, QPushButton, QMessageBox, QMainWindow, QHBoxLayout
from PyQt5.QtWidgets import qApp, QAction, QMenu, QGridLayout, QLabel, QLineEdit, QSizePolicy, QFileDialog
from PyQt5.QtWidgets import QInputDialog, QColorDialog, QSpinBox, QGraphicsWidget, QComboBox, QDialog, QAbstractSpinBox
from PyQt5.QtGui import QIcon, QFont, QCursor, QRegion, QPolygon, QWindow, QColor
from PyQt5 import QtCore, Qt, QtGui

class ContextMenu():
    """"""
    def __init__(self, menu, viewbox_menu, tpg):
        self.tpg = tpg
        self.menu = menu
        self.viewbox_menu = viewbox_menu
        self.viewbox_menu.leftMenu.actions()[0].setText('Click and Drag')
        self.viewbox_menu.leftMenu.actions()[1].setText('Select Rectangle')
        self.y_autopan_check = self.viewbox_menu.actions()[2].menu().actions()[0].defaultWidget().layout().itemAt(10).widget()
        self.y_autopan_check.stateChanged.connect(self.tpg.y_autopan_warning)

        self.autoVisibleOnly_x = self.viewbox_menu.actions()[1].menu().actions()[0].defaultWidget().layout().itemAt(9).widget()
        self.autoVisibleOnly_y = self.viewbox_menu.actions()[2].menu().actions()[0].defaultWidget().layout().itemAt(9).widget()
        self.autoVisibleOnly_x.setChecked(self.tpg.settings['autoVisibleOnly_x'])
        self.autoVisibleOnly_y.setChecked(self.tpg.settings['autoVisibleOnly_y'])

        # ===============================
        # Create submenus (in order)
        # ===============================
        self.line_settings_menu = self.menu.addMenu("Line Settings")
        self.visualization_settings = self.menu.addMenu("Visualization Settings")
        self.data_options = self.menu.addMenu("Data Options")
        self.change_labels_menu = self.menu.addMenu("Change Labels")

        # ===============================
        # Submenu Formation: line_settings
        # ===============================
        self._add_line_settings_menu()

        # ===============================
        # Submenu Formation: visualization_settings
        # ===============================
        self._add_visualization_settings_menu()

        # ===============================
        # Submenu Formation: Data Options
        # ===============================
        self._add_data_option_menu()

        # ===============================
        # Submenu Formation: Change Labels
        # ===============================
        self._add_change_label_menu()

        # ===============================
        # Function Formation: Load Past Data
        # ===============================
        self._add_load_past_data()
        
        # ===============================
        # Submenu revision: local fourier transform
        # ===============================
        self._add_local_fft()

        # ===============================
        # Remove unnecesary default context menu operations
        # ===============================
        self.remove_options_from_default_contextmenu()


    def _add_line_settings_menu(self):
        """add line setting submenu to Plot Options menu
        
        Line settings menu consists of multiple blocks such that every data
        line present in the plot has a corresponding block. One block consists 
        consists of QWidgets to change line color, alpha value, and width.
        
        """
        # ===============================
        # remove existing items from the menu
        # ===============================
        self.line_settings_menu.clear()
        # ===============================
        # Submenu Formation: line_settings
        # ===============================
        for key in self.tpg.data_table:
            # ===============================
            # width and alpha
            # ===============================
            mainlabel = QLabel('Line '+str(key))
            mainlabel.setAlignment(QtCore.Qt.AlignCenter)
            widthintermediate = QtGui.QWidgetAction(self.line_settings_menu)
            width_widget = QtGui.QWidget()
            widthlabel = QLabel("Line Width:")
            spinbox = QSpinBox()
            spinbox.setValue(self.tpg.settings['line_settings'][str(key)]['line_width'])
            spinbox.setRange(1, 15)
            spinbox.setSingleStep(1)

            alphalabel = QLabel("Alpha")
            alphaSlider = QtGui.QSlider(self.line_settings_menu)
            alphaSlider.setOrientation(QtCore.Qt.Horizontal)
            alphaSlider.setMaximum(255)
            alphaSlider.setValue(self.tpg.settings['line_settings'][str(key)]['line_alpha']*255)

            width_layout = QGridLayout()
            width_layout.addWidget(mainlabel, 0, 0, 1, 2)
            width_layout.addWidget(alphalabel, 1, 0, 1, 1)
            width_layout.addWidget(alphaSlider, 1, 1, 1, 1)
            width_layout.addWidget(widthlabel, 2, 0, 1, 1)
            width_layout.addWidget(spinbox, 2, 1, 1, 1)
            width_widget.setLayout(width_layout)

            spinbox.valueChanged.connect(self.tpg.data_table[key].setWidth)
            alphaSlider.valueChanged.connect(self.tpg.data_table[key].setAlpha)
            widthintermediate.setDefaultWidget(width_widget)
            self.line_settings_menu.addAction(widthintermediate)
            self.line_settings_menu.widthintermediate = widthintermediate
            # ===============================
            # color
            # ===============================
            change_line_color = QtGui.QWidgetAction(self.line_settings_menu)
            color_button = QPushButton("Change line color")
            color_button.clicked.connect(self.tpg.data_table[key].open_color_dialog)
            change_line_color.setDefaultWidget(color_button)
            self.line_settings_menu.addAction(change_line_color)
            self.line_settings_menu.change_line_color = change_line_color

    def _add_visualization_settings_menu(self):
        """add visualization submenu to Plot Options menu
        
        Visualization menu contains actions to load, save, clear, and restore 
        plot settings.
        
        """
        restore_default = QtGui.QAction(
            "Restore Default Plot Settings", 
            self.visualization_settings
        )
        restore_default.triggered.connect(self.tpg.restore_default_settings)
        self.visualization_settings.addAction(restore_default)
        self.visualization_settings.restore_default = restore_default

        restore_saved = QtGui.QAction(
            "Restore Saved Plot Settings", 
            self.visualization_settings
        )
        restore_saved.triggered.connect(self.tpg.set_custom_settings)
        self.visualization_settings.addAction(restore_saved)
        self.visualization_settings.restore_saved = restore_saved

        save_settings = QtGui.QAction(
            "Save Current Plot Settings", 
            self.visualization_settings
        )
        save_settings.triggered.connect(self.tpg.save_current_settings)
        self.visualization_settings.addAction(save_settings)
        self.visualization_settings.save_settings = save_settings

        clear_line_settings = QtGui.QAction(
            "Clear Line Settings", 
            self.visualization_settings
        )
        clear_line_settings.triggered.connect(self.tpg.clear_line_settings)
        self.visualization_settings.addAction(clear_line_settings)
        self.visualization_settings.clear_line_settings = clear_line_settings
        
    def _add_data_option_menu(self):
        """add data option submenu to Plot Options menu
        
        Data option menu contains actions to to clear present data; set the
        clear-on-startup option; and enable data autosave option
        
        """
        clear_data = QtGui.QAction(
            "Clear Data", 
            self.data_options
        )
        clear_data.triggered.connect(self.tpg.clear_all_data)
        self.data_options.addAction(clear_data)
        self.data_options.clear_data = clear_data

        automatic_clear = QtGui.QWidgetAction(self.data_options)
        automatic_clear_checkbox = QtGui.QCheckBox("Clear Old Data on Start")
        automatic_clear.setDefaultWidget(automatic_clear_checkbox)
        automatic_clear_checkbox.stateChanged.connect(self.tpg.save_data_settings)
        self.data_options.addAction(automatic_clear)
        self.data_options.automatic_clear = automatic_clear
        self.data_options.automatic_clear_checkbox = automatic_clear_checkbox

        autosave = QtGui.QWidgetAction(self.data_options)
        autosave_widget = QWidget()
        autosave_layout = QHBoxLayout()
        autosave_layout.setContentsMargins(0,0,0,0)
        autosave_checkbox = QtGui.QCheckBox("Automatically Save Data")
        autosave_checkbox.stateChanged.connect(self.tpg.set_all_autosave)
        autosave_checkbox.setChecked(self.tpg.settings['do_autosave'])
        autosave_nr = QSpinBox()
        autosave_nr.setButtonSymbols(QAbstractSpinBox().NoButtons)
        autosave_nr.setRange(10, 1000)
        autosave_nr.setValue(self.tpg.settings['autosave_nr'])
        # autosave_nr.setSingleStep(10)
        autosave_nr.valueChanged.connect(self.tpg.set_all_autosave_nr)
        autosave_layout.addWidget(autosave_checkbox)
        autosave_layout.addWidget(autosave_nr)
        autosave_widget.setLayout(autosave_layout)
        autosave.setDefaultWidget(autosave_widget)
        self.data_options.addAction(autosave)
        self.data_options.autosave = autosave        

    def _add_change_label_menu(self):
        """add change label submenu to Plot Option menu
        
        Chane label menu contians functions to change title, and axes labels. 
        Furthermore it allows to change time scale from relative time values to
        absolute timve values
        
        """
        change_title = QtGui.QAction(
            "Change Plot Title", 
            self.change_labels_menu
        )
        change_title.triggered.connect(self.tpg.change_title)
        self.change_labels_menu.addAction(change_title)
        self.change_labels_menu.change_title = change_title

        change_x_axis_label = QtGui.QAction(
            "Change X Axis Label", 
            self.change_labels_menu
        )
        change_x_axis_label.triggered.connect(self.tpg.change_x_axis_label)
        self.change_labels_menu.addAction(change_x_axis_label)
        self.change_labels_menu.change_x_axis_label = change_x_axis_label

        change_y_axis_label = QtGui.QAction(
            "Change Y Axis Label", 
            self.change_labels_menu
        )
        change_y_axis_label.triggered.connect(self.tpg.change_y_axis_label)
        self.change_labels_menu.addAction(change_y_axis_label)
        self.change_labels_menu.change_y_axis_label = change_y_axis_label

        relative_time = QtGui.QWidgetAction(self.change_labels_menu)
        relative_time_checkbox = QtGui.QCheckBox("Relative Time Markers")
        relative_time.setDefaultWidget(relative_time_checkbox)
        relative_time_checkbox.setChecked(self.tpg.settings['relative_timestamp'])
        relative_time_checkbox.stateChanged.connect(self.tpg.change_time_markers)
        self.change_labels_menu.addAction(relative_time)
        self.change_labels_menu.relative_time = relative_time
        self.change_labels_menu.relative_time_checkbox = relative_time_checkbox

    def _add_load_past_data(self):
        """add load-past-data function to Plot Option menu
        
        This function opens a seperate finder window from where plot settings 
        and data files can be selected to be loaded into the plot
        
        """
        open_data = QtGui.QAction("Load Stored Data")
        open_data.triggered.connect(self.tpg.open_finder)
        self.menu.addAction(open_data)
        self.menu.open_data = open_data
        
    def _add_local_fft(self):
        """add local_fft option to the Transform submenu in the Plot Option menu
        
        This function ammends functionality to the Transform submenu. Since the 
        Transform submenu is defined in the pyqtgraph ContextMenu class this
        function has to retrieve the relevant QAction to successfully ammend 
        the functionality.
        
        """
        self.transform_menu = self.menu.actions()[0].menu()
        self.transform_menu.actions()[0].defaultWidget().layout().setContentsMargins(10,10,10,0)

        self.x_log_check = self.transform_menu.actions()[0].defaultWidget().layout().itemAt(1).widget()
        self.y_log_check = self.transform_menu.actions()[0].defaultWidget().layout().itemAt(2).widget()

        local_fourier = QtGui.QWidgetAction(self.transform_menu)
        local_fourier_widget = QWidget()
        lf_label = QLabel("Local Fourier Mode")
        local_fourier_checkbox = QtGui.QCheckBox()
        local_fourier_checkbox.stateChanged.connect(self.tpg.set_local_ft_mode)
        lf_layout = QHBoxLayout()
        lf_layout.setContentsMargins(10,0,0,0)
        lf_layout.addWidget(lf_label)
        lf_layout.addWidget(local_fourier_checkbox)
        local_fourier_widget.setLayout(lf_layout)
        local_fourier.setDefaultWidget(local_fourier_widget)
        self.transform_menu.addAction(local_fourier)
        self.transform_menu.local_fourier = local_fourier

    def remove_options_from_default_contextmenu(self):
        """
        remove some default options from the contextmenu
        
        Since this context menu is build upon the pyqtgraph context menu, some 
        of the submenues are not relevant here. This function removes them.
        
        """
        remove_menu_lst = ['Downsample','Average','Alpha', 'Points']
        
        actions = self.tpg.graphItem.ctrlMenu.actions()
        for action in actions:
            menu_name = action.iconText() 
            if menu_name in remove_menu_lst:
                self.tpg.graphItem.ctrlMenu.removeAction(action)
        

    def ammend_context_menu(self):
        line_controls = self.line_settings_menu.actions()[0::2]
        key = 0
        for line in line_controls:
            line.defaultWidget().layout().itemAt(2).widget().setValue(
                255*self.tpg.settings['line_settings'][str(key)]['line_alpha']
            )
            line.defaultWidget().layout().itemAt(4).widget().setValue(
                self.tpg.settings['line_settings'][str(key)]['line_width']
            )
            key += 1
