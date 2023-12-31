# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SupercamCompanion
                                 A QGIS plugin
 Helps viewing Supercam science data directly on QGIS
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2023-06-14
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Baptiste Perrier
        email                : baptiste.perrier@ens-lyon.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import pyqtSignal, QObject

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .supercam_companion_dockwidget import SupercamCompanionDockWidget
import os

# Import the code for the map hand tool
from .supercam_companion_tool import selectTool

from . import scam_helper as helper

class SupercamCompanion(QObject):
    """QGIS Plugin Implementation."""

    log = pyqtSignal(str)

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # This line is for PyQt to inherit properly QObject and allow the use of pyqtsignal
        super(SupercamCompanion, self).__init__()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        helper.misc.constants.LOCALFOLDER = self.plugin_dir

        # Instanciating general logger
        self.logger = helper.utils.log.Logger()

        # Binding logger to local log function
        self.log.connect(self.logger.core_log)

        self.log.emit("")
        self.log.emit("Initializing core ...")

        # Save reference to the QGIS interface
        self.iface = iface

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SupercamCompanion_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Supercam Companion')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'SupercamCompanion')
        self.toolbar.setObjectName(u'SupercamCompanion')

        """icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        self.action = QAction(
            QIcon("icon.png"),
            self.menu, self.iface.mainWindow())
        
        self.iface.addPluginToMenu(self.menu, self.action)
        self.iface.addToolBarIcon(self.action)

        self.log.emit(str(self.iface.addToolBarIcon(self.action)))"""

        #print "** INITIALIZING SupercamCompanion"

        self.pluginIsActive = False
        self.dockwidget = None

        best_interp_path = os.path.join(helper.misc.constants.LOCALFOLDER, "rover_position", "best_interp.csv")
        helper.PDS.functions.dl(helper.PDS.constants.PDSROVERPOSITIONDIRECTORY + "/best_interp.csv", best_interp_path)

        best_tactical_path = os.path.join(helper.misc.constants.LOCALFOLDER, "rover_position", "best_tactical.csv")
        helper.PDS.functions.dl(helper.PDS.constants.PDSROVERPOSITIONDIRECTORY + "/best_tactical.csv", best_tactical_path)

        # Instanciating positioner for later points and rover postioning
        self.positioner = helper.science.positioning.Positioner(best_interp_path, best_tactical_path)

        self.log.emit("Core initialized.")

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SupercamCompanion', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/supercam_companion/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Supercam Companion'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD SupercamCompanion"
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Supercam Companion'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = SupercamCompanionDockWidget()

                # Bind the dockwidget with general logger for graphical log display
                self.logger.bindDockWidget(self.dockwidget)

            self.dockwidget.log.connect(self.logger.dockWidget_log)

            # binds local log with graphic methods
            self.log.connect(self.logger.core_graphic_log)
            self.dockwidget.log.connect(self.logger.dockWidget_graphic_log)

            self.dockwidget.init()
            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            self.dockwidget.updateLocalLastMeasureDisplay()
            self.dockwidget.syncPDS_button.setEnabled(True)

            self.tool = selectTool(self.iface)

            self.tool.log.connect(self.logger.mapTool_log)
            self.tool.log.connect(self.logger.mapTool_graphic_log)

            self.tool.init()
            
            # Instanciate EventHandler instance now we have defined every useful object
            self.eventsHandler = helper.events.eventsHandler(self.iface, self.dockwidget, self.tool, self.positioner)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.eventsHandler.onClosePlugin)

            self.eventsHandler.log.connect(self.logger.eventsHandler_log)
            self.eventsHandler.log.connect(self.logger.eventsHandler_graphic_log)

            self.dockwidget.rebuildLocalMasterlist_button.clicked.connect(self.eventsHandler.rebuildLocalMasterlist)
            self.dockwidget.reloadLocalMasterlist_button.clicked.connect(self.eventsHandler.loadLocalMasterlistLayer)

            self.dockwidget.syncPDS_button.clicked.connect(self.eventsHandler.checkPDSAheadOfTime)
            self.dockwidget.mapTool_button.clicked.connect(self.eventsHandler.mapToolSelection)

            self.dockwidget.SCAMLDImport_button.clicked.connect(self.eventsHandler.importSCAMLD)
            self.dockwidget.visIRSpectralParametersImport_button.clicked.connect(self.eventsHandler.importVisIRSpectralParameters)
            self.dockwidget.plannedTargetsImport_button.clicked.connect(self.eventsHandler.importPlannedTargets)

            self.dockwidget.plotSpectralParameters_button.clicked.connect(self.dockwidget.plotSpectralParameters)

            self.tool.mapClicked.connect(self.dockwidget.mapClicked)
            self.tool.featureSelected.connect(self.dockwidget.ftSelected)

            
