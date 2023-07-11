import os
import pandas as pd

from qgis.PyQt.QtCore import pyqtSignal, QObject
from qgis.PyQt.QtWidgets import QAction, QInputDialog, QFileDialog

from .. import scam_helper as helper

from qgis.core import QgsProject, QgsVectorLayer

class eventsHandler(QObject):
    log = pyqtSignal(str)

    def __init__(self, iface, dockwidget, tool, positioner) -> None:
        # This line is for PyQt to inherit properly QObject and allow the use of pyqtsignal
        super(eventsHandler, self).__init__()

        self.iface = iface
        self.dockwidget = dockwidget
        self.tool = tool
        self.positioner = positioner

    def loadLocalMasterlistLayer(self):
        self.log.emit("Binding local masterlist with QGIS layer")

        # Didn't succeed at reloading the .geojson data, so we delete and recall the file. Could try to at least save the style parameters of the layer
        if QgsProject.instance().mapLayersByName("shots"):
            QgsProject.instance().removeMapLayers([self.pointsLayer.id()])

        self.pointsLayer = QgsVectorLayer(os.path.join(helper.misc.constants.LOCALFOLDER, "local_data", "local_masterlist.geojson"),"shots","ogr")

        self.tool.updatePointsLayer(QgsProject.instance().addMapLayer(self.pointsLayer))

        self.dockwidget.mapTool_button.setEnabled(True)
        self.dockwidget.plannedTargetsImport_button.setEnabled(True)
        self.dockwidget.SCAMLDImport_button.setEnabled(True)
        self.dockwidget.visIRSpectralParametersImport_button.setEnabled(True)

    def rebuildLocalMasterlist(self):
        geojson_points, lastSclk = helper.files.local.buildLocalMasterlist(self._masterlistPath, self.positioner)

        helper.files.local.writeLocalMasterlist(geojson_points)

        config = helper.files.local.readLocalConfig()
        config["PDSSyncing"]["local_last_sclk"] = lastSclk
        helper.files.local.writeLocalConfig(config)

        self.dockwidget.updateLocalLastMeasureDisplay()
        self.loadLocalMasterlistLayer()
    
    def checkPDSAheadOfTime(self):
        self._masterlistPath = os.path.join(helper.misc.constants.LOCALFOLDER, "master", "PDS_masterlist.csv")
        helper.PDS.functions.dl(helper.PDS.constants.SCAM_MASTERLISTURL, self._masterlistPath)
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
        self.dockwidget.rebuildLocalMasterlist_button.setEnabled(True)
        self.dockwidget.reloadLocalMasterlist_button.setEnabled(True)
        
        config = helper.files.local.readLocalConfig()

        if PDSLastShot.sclk.values[0] > config["PDSSyncing"]["local_last_sclk"]:
            self.log.emit("PDS ahead of time on local files, building new local Masterlist...")
            self.rebuildLocalMasterlist()            
            return True
        else:
            self.log.emit("Local files are up to date with PDS.")
            return False
    
    def importPlannedTargets(self):
        self.log.emit("Local GEOJSON Import")
        plannedTargetsPath = QFileDialog.getOpenFileName()[0]

        if not plannedTargetsPath:
            return
        
        self.log.emit("Importing PlannedTargets at {}.".format(plannedTargetsPath))

        helper.files.local.importPlannedTargets(plannedTargetsPath)

        self.dockwidget.updateLocalLastMeasureDisplay()

    def importSCAMLD(self):
        self.log.emit("Importing SCAMLD")
        SCAMLDPath = QFileDialog.getOpenFileName()[0]

        if not SCAMLDPath:
            return
        
        self.log.emit("Importing SCAMLD at {}.".format(SCAMLDPath))

        helper.files.local.importSCAMLD(SCAMLDPath)

        self.dockwidget.updateLocalLastMeasureDisplay()

    def importVisIRSpectralParameters(self):
        self.log.emit("Importing local VISIR spectral parameters")
        VisIRSPPath = QFileDialog.getOpenFileName()[0]

        if not VisIRSPPath:
            return
        
        self.log.emit("Importing spectral parameters at {}.".format(VisIRSPPath))

        helper.files.local.importVisIRSpectralParameters(VisIRSPPath)

        self.loadLocalMasterlistLayer()
    
    def mapToolSelection(self):
        self.iface.mapCanvas().setMapTool(self.tool)

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        self.log.emit("Closing plugin.")

        QgsProject.instance().removeMapLayers([self.pointsLayer.id()])