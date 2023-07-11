import matplotlib.pyplot as plt
import os
import numpy as np

from qgis.gui import QgsMapToolIdentifyFeature, QgsMapToolIdentify
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsPointXY, QgsPoint
from PyQt5.QtCore import QVariant, Qt

from qgis.PyQt.QtCore import pyqtSignal

class selectTool(QgsMapToolIdentifyFeature):
    log = pyqtSignal(str)
    mapClicked = pyqtSignal()
    featureSelected = pyqtSignal(QgsFeature)
    
    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        #self.pointsLayer = QgsProject().instance().mapLayersByName("usableTargets")[0]
        #QgsMapToolIdentifyFeature.__init__(self, self.canvas, self.pointsLayer)
        #self.iface.currentLayerChanged.connect(self.active_changed)

        QgsMapToolIdentifyFeature.__init__(self, self.canvas)
        
        self._ctrlPressed = False
        self.pltCount = 0
        self.xpos = 0
        self.ypos = 0
        
        self.roverLayer = QgsProject().instance().mapLayersByName("RoverLayer")
        if self.roverLayer:
            self.roverLayer = self.roverLayer[0]
            self.roverFeatures = self.roverLayer.dataProvider()
        else:
            self.roverLayer = QgsVectorLayer("Point", "RoverLayer", "memory")
            self.roverFeatures = self.roverLayer.dataProvider()
            self.roverFeatures.addAttributes([
                QgsField("az", QVariant.Double),
                QgsField("el", QVariant.Double)
                ])
            self.roverLayer.updateFields()
            
        self.linesLayer = QgsProject().instance().mapLayersByName("LinesLayer")
        if self.linesLayer:
            self.linesLayer = self.linesLayer[0]
        else:
            self.linesLayer = QgsVectorLayer("Linestring", "LinesLayer", "memory")
        self.linesFeatures = self.linesLayer.dataProvider()

    def init(self):
        self.log.emit("Map tool initialized.")

    def updatePointsLayer(self, pointsLayer):
        self.pointsLayer = pointsLayer

        # Herited method
        self.setLayer(pointsLayer)

        self.iface.setActiveLayer(self.pointsLayer)

    def active_changed(self, layer):
        self.pointsLayer.removeSelection()
        if isinstance(layer, QgsVectorLayer) and layer.isSpatial():
            self.layer = layer
            self.setLayer(self.pointsLayer)        
    
    def canvasPressEvent(self, event):
        self.mapClicked.emit()
        try:
            self.pointsLayer.removeSelection() 
        except Exception as e:
            self.log.emit(str(e))       
        
        if QgsProject().instance().mapLayersByName("RoverLayer"):
            self.roverLayer.startEditing()
            for roverFt in self.roverLayer.getFeatures():
                self.roverLayer.deleteFeature(roverFt.id())
            self.roverLayer.commitChanges()
        
        if QgsProject().instance().mapLayersByName("LinesLayer"):
            self.linesLayer.startEditing()
            for line in self.linesLayer.getFeatures():
                self.linesLayer.deleteFeature(line.id())
            self.linesLayer.commitChanges()
                
        self.pltCount = 0
        self.xpos = 0
        self.ypos = 0
            
        found_features = self.identify(event.x(), event.y(), [self.pointsLayer], QgsMapToolIdentify.TopDownAll)
        self.pointsLayer.selectByIds([f.mFeature.id() for f in found_features], QgsVectorLayer.AddToSelection)
        
        self.selectedFeatures = self.pointsLayer.selectedFeatures()
        if self.selectedFeatures:
            for ft in self.selectedFeatures:
                self.featureSelected.emit(ft)
                
                self.roverLayer.startEditing()
                self.linesLayer.startEditing()
                
                f = QgsFeature()
                f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(ft.attribute("roverCoordinates")[1],ft.attribute("roverCoordinates")[0])))
                self.roverFeatures.addFeature(f)
                self.roverLayer.updateExtents()
                
                seg = QgsFeature()
                seg.setGeometry(QgsGeometry.fromPolyline([QgsPoint(ft.geometry().asPoint()), QgsPoint(f.geometry().asPoint())]))
                self.linesFeatures.addFeature(seg)
                self.linesFeatures.updateExtents()
                
                QgsProject.instance().addMapLayer(self.roverLayer)
                QgsProject.instance().addMapLayer(self.linesLayer)
                self.roverLayer.commitChanges()
                self.linesLayer.commitChanges()
                
                """fig = plt.figure()
                wavelengths, reflectances = self.getSpectralData(ft.attribute("sclk"), ft.attribute("cdr_fname"))
                for reflectance in reflectances:
                    plt.plot(wavelengths, reflectance, color='b', linewidth=0.5)
                    
                reflectances = np.array(reflectances)
                reflectancesMean = np.mean(reflectances, axis=0)
                
                if self.pltCount > 0:
                    mngr = plt.get_current_fig_manager()
                    geom = mngr.window.geometry()
                    x,y,dx,dy = geom.getRect()
                    self.ypos += dy
                
                plt.plot(wavelengths, reflectancesMean, color='r', linewidth=2)
                fig.canvas.manager.window.move(self.xpos,self.ypos)
                self.pltCount += 1
                
                plt.show()"""
                
                self.iface.setActiveLayer(self.pointsLayer)