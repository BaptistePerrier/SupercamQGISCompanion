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
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QFileDialog
from qgis.PyQt.QtCore import pyqtSignal, QObject

from qgis.core import (
    QgsPoint,
    QgsVectorLayer,
    QgsProject,
    QgsProcessingContext,
    QgsTaskManager,
    QgsTask,
    QgsProcessingAlgRunnerTask,
    Qgis,
    QgsProcessingFeedback,
    QgsApplication,
    QgsMessageLog,
)

MESSAGE_CATEGORY = 'TaskFromFunction'

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .supercam_companion_dockwidget import SupercamCompanionDockWidget
import os
import os.path
import json
import pandas as pd
import time
import numpy as np

# Import the code for the map hand tool
from .supercam_companion_tool import selectTool

from .aux import misc, FileProvider

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
        super(SupercamCompanion, self).__init__()
        self.log.connect(self.core_log)

        self.log.emit("")
        self.log.emit("Initializing core ...")
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

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

        self.fileProvider = FileProvider(self.plugin_dir)

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

    def core_log(self, message):
        QgsMessageLog.logMessage("[SupercamCompanion - Core] " + message, level=Qgis.Info)
        print("[Core] " + message)

    def fileProvider_log(self, message):
        QgsMessageLog.logMessage("[SupercamCompanion - FileProvider] " + message, level=Qgis.Info)
        print("[FileProvider] " + message)
        
    def dockWidget_log(self, message):
        QgsMessageLog.logMessage("[SupercamCompanion - Dockwidget] " + message, level=Qgis.Info)
        print("[Dock Widget] " + message)

    def mapTool_log(self, message):
        QgsMessageLog.logMessage("[SupercamCompanion - MapTool] " + message, level=Qgis.Info)
        print("[Map tool] " + message)

    def core_graphic_log(self, message):
        self.dockwidget.logs_TextEdit.append("[Core] " + message)
        self.dockwidget.update()

    def fileProvider_graphic_log(self, message):
        self.dockwidget.logs_TextEdit.append("[FileProvider] " + message)
        self.dockwidget.update()
        
    def dockWidget_graphic_log(self, message):
        self.dockwidget.logs_TextEdit.append("[Dock Widget] " + message)
        self.dockwidget.update()

    def mapTool_graphic_log(self, message):
        self.dockwidget.logs_TextEdit.append("[Map tool] " + message)
        self.dockwidget.update()

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        self.log.emit("Closing plugin.")
        self.fileProvider.closeAll()

        QgsProject.instance().removeMapLayers([self.pointsLayer.id()])

        # disconnects
        #self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD SupercamCompanion"
        self.fileProvider.closeAll()
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Supercam Companion'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def retrieveRMI(self): # Move these functions into misc.functions
        pass

    def retrieveRoverPosition(self, sclk, best_interp, best_tactical):
        # Get the last registered localization for the rover in both best_interp and best_tactical
        last_interp = best_interp[best_interp["sclk"]<sclk].sort_values(by="sclk").tail(1)
        last_tactical = best_tactical[best_tactical["sclk"]<sclk].sort_values(by="sclk").tail(1)

        # Get the last timestamps where the positions have been registered in both tactical and interp
        last_interp_sclk = last_interp.sclk.values[0]
        last_tactical_sclk = last_tactical.sclk.values[0]

        interp_coordinates = [float(last_interp.planetocentric_latitude.values[0]), float(last_interp.longitude.values[0])]
        tactical_coordinates = [float(last_tactical.planetocentric_latitude.values[0]), float(last_tactical.longitude.values[0])]

        if last_interp_sclk > last_tactical_sclk: # If interp and auto are old egal, chosse tactical, otherwise tactical has not been updated for the current rover position and thus we chosse interp
            return {"source" : "best_interp", "coordinates" : interp_coordinates}
        else:
            return {"source" : "best_tactical", "coordinates" : tactical_coordinates}

    def updateLocalLastMeasureDisplay(self):
        self.dockwidget.localLastMeasure_Label.setText("Sol {}, {} Mars. time".format(misc.functions.getSolFromsclk(self.config_localJSON.PDS_syncing.local_last_sclk), misc.functions.getMartianTimeFromsclk(self.config_localJSON.PDS_syncing.local_last_sclk)))

    def saveLocalConfig(self):
        local_JSONconfig = self.fileProvider.open(os.path.join("config", "local.json"), 'w')
        local_JSONconfig.write(self.config_localJSON.to_json())
        self.fileProvider.close(os.path.join("config", "local.json"))

    def readLocalData(self):
        self.log.emit("Reading local data")
        self.config_localJSON = pd.read_json(self.fileProvider.path(os.path.join("config", "local.json")))

        self.updateLocalLastMeasureDisplay()

        self.dockwidget.syncPDS_button.setEnabled(True)

    def importPlannedTargets(self):
        #### La c'est flingué, à reprednre, c'est l'importation dans un format correct des .geojson qui merde (le reste peut etre aussi mais on en est pas là)
        self.log.emit("Local GEOJSON Import")
        plannedTargetsPath = QFileDialog.getOpenFileName()[0]

        if not plannedTargetsPath:
            return
        
        self.log.emit("Importing PlannedTargets at {}.".format(plannedTargetsPath))

        with open(self.fileProvider.path(os.path.join("local_data", "local_masterlist.geojson")), 'r') as f:
            localMasterlistRaw = json.load(f)
        localMasterlist = localMasterlistRaw["features"]

        with open(plannedTargetsPath, 'r') as f:
            plannedTargetsRaw = json.load(f)["features"]
        # Building correspondance dictionnary to faciliytate search
        plannedTargets = {}
        for entry in plannedTargetsRaw:
            plannedTargets[entry["properties"]["Name"]] = entry   

        for entry in localMasterlist:
            try:
                plannedTargetsCoordinates = plannedTargets[entry["properties"]["name"]]["geometry"]["coordinates"]
                entry["geometry"]["coordinates"] = plannedTargetsCoordinates
            except:
                pass # If the masterlist name is not found in Planned Targets, don't worry and go on

        self.log.emit("Finished parsing PlannedTargets, now writing to local_data/local_masterlist.geojson")

        localMasterList_file = self.fileProvider.open(os.path.join("local_data", "local_masterlist.geojson"), 'w')
        json.dump(localMasterlistRaw, localMasterList_file)
        self.fileProvider.close(os.path.join("local_data", "local_masterlist.geojson"))

        self.updateLocalLastMeasureDisplay()

    def importSCAMLD(self):
        self.log.emit("Importing SCAMLD")
        SCAMLDPath = QFileDialog.getOpenFileName()[0]

        if not SCAMLDPath:
            return
        
        self.log.emit("Importing SCAMLD at {}.".format(SCAMLDPath))

        with open(self.fileProvider.path(os.path.join("local_data", "local_masterlist.geojson")), 'r') as f:
            localMasterlistRaw = json.load(f)
        localMasterlist = localMasterlistRaw["features"]

        with open(SCAMLDPath, 'r') as f:
            SCAMLDRaw = json.load(f)["features"]
        # Building correspondance dictionnary to faciliytate search
        SCAMLD = {}
        for entry in SCAMLDRaw:
            SCAMLD[entry["properties"]["description"]] = entry

        for entry in localMasterlist:
            try:
                SCAMLDCoordinates = SCAMLD[entry["properties"]["name"]]["geometry"]["coordinates"]
                entry["geometry"]["coordinates"] = SCAMLDCoordinates
            except:
                pass # If the masterlist name is not found in SCAMLD, don't worry and go on

        self.log.emit("Finished parsing SCAMLD, now writing to local_data/local_masterlist.geojson")

        localMasterList_file = self.fileProvider.open(os.path.join("local_data", "local_masterlist.geojson"), 'w')
        json.dump(localMasterlistRaw, localMasterList_file)
        self.fileProvider.close(os.path.join("local_data", "local_masterlist.geojson"))

        self.updateLocalLastMeasureDisplay()

    def importVisIRSpectralParameters(self):
        self.log.emit("Importing local VISIR spectral parameters")
        VisIRSPPath = QFileDialog.getOpenFileName()[0]

        if not VisIRSPPath:
            return
        
        self.log.emit("Importing spectral parameters at {}.".format(VisIRSPPath))

        with open(self.fileProvider.path(os.path.join("local_data", "local_masterlist.geojson")), 'r') as f:
            localMasterlistRaw = json.load(f)
        localMasterlist = localMasterlistRaw["features"]

        SPRaw = pd.read_csv(VisIRSPPath)

        for entry in localMasterlist:
            try:
                spectralParameters = {
                    "BD1420" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1420.replace(np.nan, None)),
                    "BD1900_2" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1900_2.replace(np.nan, None)),
                    "BD1920" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1920.replace(np.nan, None)),
                    "BD1930" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1930.replace(np.nan, None)),
                    "BD1940" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD1940.replace(np.nan, None)),
                    "BD2210" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD2210.replace(np.nan, None)),
                    "BD2280" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD2280.replace(np.nan, None)),
                    "BD2320" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD2320.replace(np.nan, None)),
                    "LCPINDEX2" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].LCPINDEX2.replace(np.nan, None)),
                    "HCPINDEX2" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].HCPINDEX2.replace(np.nan, None)),
                    "BD2530" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD2530.replace(np.nan, None)),
                    "SINDEX2" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].SINDEX2.replace(np.nan, None)),
                    "S2100_2500" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S2100_2500.replace(np.nan, None)),
                    "S1350_1800" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S1350_1800.replace(np.nan, None)),
                    "BD433" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD433.replace(np.nan, None)),
                    "BD545" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD545.replace(np.nan, None)),
                    "BD650" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].BD650.replace(np.nan, None)),
                    "R6744" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].R6744.replace(np.nan, None)),
                    "R7584" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].R7584.replace(np.nan, None)),
                    "S6744" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S6744.replace(np.nan, None)),
                    "S7584" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S7584.replace(np.nan, None)),
                    "S6075" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S6075.replace(np.nan, None)),
                    "R6084" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].R6084.replace(np.nan, None)),
                    "S6084" : list(SPRaw[SPRaw["targetname"] == entry["properties"]["name"]].S6084)
                }
                entry["properties"]["VisIRspectralParameters"] = spectralParameters
            except Exception as e:
                self.log.emit(str(e))
                pass # If the masterlist name is not found in SCAMLD, don't worry and go on

        self.log.emit("Finished parsing spectral parameters, now writing to local_data/local_masterlist.geojson")

        localMasterList_file = self.fileProvider.open(os.path.join("local_data", "local_masterlist.geojson"), 'w')
        json.dump(localMasterlistRaw, localMasterList_file)
        self.fileProvider.close(os.path.join("local_data", "local_masterlist.geojson"))

        self.loadLocalMasterlistLayer()
        

    def checkPDSAheadOfTime(self):
        self._masterlistPath = self.fileProvider.fetchPDSFile(misc.constants.SCAM_MASTERLISTURL, os.path.join("master", "PDS_masterlist.csv"), forceDownload=True) # MUST SET forceDownload To True otherwise Supercam Companion won't update !!!
        masterlist = pd.read_csv(self._masterlistPath, usecols=[
            "sol",
            "seqid",
            "sclk",
            "targetname",
            "tdb_name",
            "type",
            "primary_mirror_temp",
            "focus_position_mm",
            "focus_position_steps",
            "binfile",
            "edr_fname",
            "cdr_fname",
            "rsm_az",
            "rsm_el",
            "inst_az",
            "inst_el",
            "solar_az",
            "solar_el"
        ], dtype={
            "sol" : int,
            "seqid" : str,
            "sclk" : int,
            "targetname" : str,
            "tdb_name" : str,
            "type" : str,
            "primary_mirror_temp" : float,
            "focus_position_mm" : int,
            "focus_position_steps" : int,
            "binfile" : str,
            "edr_fname" : str,
            "cdr_fname" : str,
            "rsm_az" : float,
            "rsm_el" : float,
            "inst_az" : float,
            "inst_el" : float,
            "solar_az" : float,
            "solar_el" : float
        })
        PDSLastShot = masterlist.sort_values(by="sclk").tail(1)
        
        if PDSLastShot.sclk.values[0] > self.config_localJSON.PDS_syncing.local_last_sclk:
            self.log.emit("PDS ahead of time on local files, building new local Masterlist...")
            self.buildLocalMasterlist()            
            self.dockwidget.rebuildLocalMasterlist_button.setEnabled(True)
            self.dockwidget.reloadLocalMasterlist_button.setEnabled(True)
            return True
        else:
            self.log.emit("Local files are up to date with PDS.")
            self.dockwidget.rebuildLocalMasterlist_button.setEnabled(True)
            self.dockwidget.reloadLocalMasterlist_button.setEnabled(True)
            return False

    def buildLocalMasterlist(self):
        self.log.emit("Building local masterlist ...")
        masterlist = pd.read_csv(self._masterlistPath, usecols=[
            "sol",
            "seqid",
            "sclk",
            "targetname",
            "tdb_name",
            "type",
            "primary_mirror_temp",
            "focus_position_mm",
            "focus_position_steps",
            "binfile",
            "edr_fname",
            "cdr_fname",
            "rsm_az",
            "rsm_el",
            "inst_az",
            "inst_el",
            "solar_az",
            "solar_el"
        ], dtype={
            "sol" : int,
            "seqid" : str,
            "sclk" : int,
            "targetname" : str,
            "tdb_name" : str,
            "type" : str,
            "primary_mirror_temp" : float,
            "focus_position_mm" : int,
            "focus_position_steps" : int,
            "binfile" : str,
            "edr_fname" : str,
            "cdr_fname" : str,
            "rsm_az" : float,
            "rsm_el" : float,
            "inst_az" : float,
            "inst_el" : float,
            "solar_az" : float,
            "solar_el" : float
        })

        # Read rover_positions in interp (auto positionning) and tactical (reviewed by team)
        best_interp = pd.read_csv(self.fileProvider.fetchPDSFile(misc.constants.PDSROVERPOSITIONDIRECTORY + "/best_interp.csv", os.path.join("rover_position", "best_interp.csv")))
        best_tactical = pd.read_csv(self.fileProvider.fetchPDSFile(misc.constants.PDSROVERPOSITIONDIRECTORY + "/best_tactical.csv", os.path.join("rover_position", "best_tactical.csv")))

        geojson_points = {"type" : "FeatureCollection", "features" : []}

        names = masterlist.tdb_name.unique()
        for name in names:
            if not name == "SCCT":
                shots = masterlist[masterlist["tdb_name"]==name]
                RMIs = shots[shots["type"]=="RMI"].sort_values(by="sclk")
                self.retrieveRMI()
                if len(RMIs.sclk.values) > 0:
                    point = {
                        "type" : "Feature", 
                        "geometry" : {
                            "type" : "Point",
                            "coordinates" : []
                        },
                        "properties" : {}
                    }

                    point["properties"]["name"] = name
                    point["properties"]["sclk"] = int(RMIs.sclk.values[0])
                    point["properties"]["seqid"] = RMIs.seqid.values[0]

                    roverCoordinates = self.retrieveRoverPosition(point["properties"]["sclk"], best_interp, best_tactical)

                    point["properties"]["roverCoordinates_source"] = roverCoordinates["source"]
                    point["properties"]["roverCoordinates"] = roverCoordinates["coordinates"]
                    Qgs_roverCoordinates = QgsPoint(point["properties"]["roverCoordinates"][1], point["properties"]["roverCoordinates"][0])

                    _shotsWithInstAz = shots.inst_az.dropna()
                    if not _shotsWithInstAz.empty:
                        point["properties"]["meanAzimuth"] = _shotsWithInstAz.mean()
                    else:
                        point["properties"]["meanAzimuth"] = 0 # Assuming the instrument is pointing north if not specified

                    _shotsWithInstEl = shots.inst_el.dropna()
                    if not _shotsWithInstEl.empty:
                        point["properties"]["meanElevation"] = _shotsWithInstEl.mean()
                    else:
                        point["properties"]["meanElevation"] = 0

                    _shotsFocusPositionMm = shots.focus_position_mm.dropna()
                    if not _shotsFocusPositionMm.empty:
                        point["properties"]["meanFocusPosition_mm"] = _shotsFocusPositionMm.mean()
                    else:
                        point["properties"]["meanFocusPosition_mm"] = 2 # Assuming the measure is made at 2 meters if not specified

                    try:
                        groundDistance = np.sqrt((point["properties"]["meanFocusPosition_mm"]/1000)**2 - 2.2**2) # Assuming supercam is 2.2 meters high
                    except:
                        groundDistance = 3 # if can't compute ground distance, assute the measure was made 3 meters away from the rover
                    
                    groundDistance = 0.00002 * groundDistance # Don't know why but need to correct groundDistance for QgsPoint.project to project at a reasonable distance

                    Qgs_pointCoordinates = Qgs_roverCoordinates.project(groundDistance, point["properties"]["meanAzimuth"]) # Check whether inst_az is given relative to RoverNAV frame or LocalLevel frame; doesn't work welle for long distances
                    point["geometry"]["coordinates"] = [Qgs_pointCoordinates.x(), Qgs_pointCoordinates.y()]
                    if np.isnan(point["geometry"]["coordinates"][0]) or np.isnan(point["geometry"]["coordinates"][1]):
                        continue

                    point["properties"]["shots"] = {}
                    _LIBSShots = shots[shots["type"] == "LIBS"]
                    if not _LIBSShots.empty:
                        point["properties"]["shots"]["LIBS"] = {
                            "sclk" : list(_LIBSShots.sclk),
                            "focus_position_mm" : list(_LIBSShots.focus_position_mm),
                            "primary_mirror_temp" : list(_LIBSShots.primary_mirror_temp),
                            "rsm_az" : list(_LIBSShots.rsm_az),
                            "rsm_el" : list(_LIBSShots.rsm_el),
                            "inst_az" : list(_LIBSShots.inst_az),
                            "inst_el" : list(_LIBSShots.inst_el),
                            "solar_az" : list(_LIBSShots.solar_az),
                            "solar_el" : list(_LIBSShots.solar_el),
                            "edr_fname" : list(_LIBSShots.edr_fname),
                            "cdr_fname" : list(_LIBSShots.cdr_fname),
                            "binfile" : list(_LIBSShots.binfile)
                        }

                    _IRSShot = shots[shots["type"] == "IRS"]
                    if not _IRSShot.empty:
                        point["properties"]["shots"]["IRS"] = {
                            "sclk" : list(_IRSShot.sclk),
                            "focus_position_mm" : list(_IRSShot.focus_position_mm),
                            "primary_mirror_temp" : list(_IRSShot.primary_mirror_temp),
                            "rsm_az" : list(_IRSShot.rsm_az),
                            "rsm_el" : list(_IRSShot.rsm_el),
                            "inst_az" : list(_IRSShot.inst_az),
                            "inst_el" : list(_IRSShot.inst_el),
                            "solar_az" : list(_IRSShot.solar_az),
                            "solar_el" : list(_IRSShot.solar_el),
                            "edr_fname" : list(_IRSShot.edr_fname),
                            "cdr_fname" : list(_IRSShot.cdr_fname),
                            "binfile" : list(_IRSShot.binfile)
                        }

                    _VISShot = shots[shots["type"] == "VIS"]
                    if not _VISShot.empty:
                        point["properties"]["shots"]["VIS"] = {
                            "sclk" : list(_VISShot.sclk),
                            "focus_position_mm" : list(_VISShot.focus_position_mm),
                            "primary_mirror_temp" : list(_VISShot.primary_mirror_temp),
                            "rsm_az" : list(_VISShot.rsm_az),
                            "rsm_el" : list(_VISShot.rsm_el),
                            "inst_az" : list(_VISShot.inst_az),
                            "inst_el" : list(_VISShot.inst_el),
                            "solar_az" : list(_VISShot.solar_az),
                            "solar_el" : list(_VISShot.solar_el),
                            "edr_fname" : list(_VISShot.edr_fname),
                            "cdr_fname" : list(_VISShot.cdr_fname),
                            "binfile" : list(_VISShot.binfile)
                        }

                    _RAMANShot = shots[shots["type"] == "RAMAN"]
                    if not _RAMANShot.empty:
                        point["properties"]["shots"]["RAMAN"] = {
                            "sclk" : list(_RAMANShot.sclk),
                            "focus_position_mm" : list(_RAMANShot.focus_position_mm),
                            "primary_mirror_temp" : list(_RAMANShot.primary_mirror_temp),
                            "rsm_az" : list(_RAMANShot.rsm_az),
                            "rsm_el" : list(_RAMANShot.rsm_el),
                            "inst_az" : list(_RAMANShot.inst_az),
                            "inst_el" : list(_RAMANShot.inst_el),
                            "solar_az" : list(_RAMANShot.solar_az),
                            "solar_el" : list(_RAMANShot.solar_el),
                            "edr_fname" : list(_RAMANShot.edr_fname),
                            "cdr_fname" : list(_RAMANShot.cdr_fname),
                            "binfile" : list(_RAMANShot.binfile)
                        }

                    geojson_points["features"].append(point)

        localMasterList_file = self.fileProvider.open(os.path.join("local_data", "local_masterlist.geojson"), 'w')
        json.dump(geojson_points, localMasterList_file)
        self.fileProvider.close(os.path.join("local_data", "local_masterlist.geojson"))

        self.config_localJSON.PDS_syncing.local_last_sclk = masterlist.sort_values(by="sclk").tail(1).sclk.values[0]

        self.saveLocalConfig()
        self.updateLocalLastMeasureDisplay()

        self.loadLocalMasterlistLayer()
                
    def loadLocalMasterlistLayer(self):
        self.log.emit("Binding local masterlist with QGIS layer")

        # Didn't succeed at reloading the .geojson data, so we delete and recall the file. Could try to at least save the style parameters of the layer
        if QgsProject.instance().mapLayersByName("shots"):
            QgsProject.instance().removeMapLayers([self.pointsLayer.id()])

        self.pointsLayer = QgsVectorLayer(self.fileProvider.path(os.path.join("local_data", "local_masterlist.geojson")),"shots","ogr")

        self.tool.pointsLayer = QgsProject.instance().addMapLayer(self.pointsLayer)

        self.dockwidget.plannedTargetsImport_button.setEnabled(True)
        self.dockwidget.SCAMLDImport_button.setEnabled(True)
        self.dockwidget.visIRSpectralParametersImport_button.setEnabled(True)

    def mapToolSelection(self):
        self.iface.mapCanvas().setMapTool(self.tool)


    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        self.fileProvider.log.connect(self.fileProvider_log)

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING SupercamCompanion"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = SupercamCompanionDockWidget(self.fileProvider)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            self.dockwidget.log.connect(self.dockWidget_log)
            self.log.connect(self.core_graphic_log)
            self.dockwidget.log.connect(self.dockWidget_graphic_log)

            self.dockwidget.init()
            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
            #readLocalData_task = QgsTask.fromFunction("Read local data", self.readLocalData, on_finish=self.localDataRead)
            #QgsApplication.taskManager().addTask(readLocalData_task)
            #readLocalData_task.run()
            #self.log.emit(str(QgsApplication.taskManager().tasks()[0]))

            self.readLocalData()

            self.tool = selectTool(self.iface)            
            self.tool.log.connect(self.mapTool_log)
            self.tool.log.connect(self.mapTool_graphic_log)
            self.tool.mapClicked.connect(self.dockwidget.mapClicked)
            self.tool.featureSelected.connect(self.dockwidget.ftSelected)
            self.tool.init()

            self.dockwidget.rebuildLocalMasterlist_button.clicked.connect(self.buildLocalMasterlist)
            self.dockwidget.reloadLocalMasterlist_button.clicked.connect(self.loadLocalMasterlistLayer)

            self.dockwidget.syncPDS_button.clicked.connect(self.checkPDSAheadOfTime)
            self.dockwidget.mapTool_button.clicked.connect(self.mapToolSelection)

            self.dockwidget.SCAMLDImport_button.clicked.connect(self.importSCAMLD)
            self.dockwidget.visIRSpectralParametersImport_button.clicked.connect(self.importVisIRSpectralParameters)
            self.dockwidget.plannedTargetsImport_button.clicked.connect(self.importPlannedTargets)

            self.dockwidget.plotSpectralParameters_button.clicked.connect(self.dockwidget.plotSpectralParameters)

            