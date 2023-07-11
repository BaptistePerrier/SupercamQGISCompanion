from qgis.core import Qgis, QgsMessageLog

class Logger:
    def __init__(self):
        print("[SupercamCompanion - Logger] Initializing logger ...")

    def bindDockWidget(self, dockwidget):
        self.dockwidget = dockwidget

    def core_log(self, message, level=Qgis.Info):
        QgsMessageLog.logMessage("[SupercamCompanion - Core] " + message, level=level)
        print("[Core] " + message)

    def eventsHandler_log(self, message, level=Qgis.Info):
        QgsMessageLog.logMessage("[SupercamCompanion - EventsHandler] " + message, level=level)
        print("[EventsHandler] " + message)
        
    def dockWidget_log(self, message, level=Qgis.Info):
        QgsMessageLog.logMessage("[SupercamCompanion - Dockwidget] " + message, level=level)
        print("[Dock Widget] " + message)

    def mapTool_log(self, message, level=Qgis.Info):
        QgsMessageLog.logMessage("[SupercamCompanion - MapTool] " + message, level=level)
        print("[Map tool] " + message)

    def core_graphic_log(self, message, level=Qgis.Info):
        self.dockwidget.logs_TextEdit.append("[Core] " + message)
        self.dockwidget.update()

    def eventsHandler_graphic_log(self, message, level=Qgis.Info):
        self.dockwidget.logs_TextEdit.append("[EventsHandler] " + message)
        self.dockwidget.update()
        
    def dockWidget_graphic_log(self, message, level=Qgis.Info):
        self.dockwidget.logs_TextEdit.append("[Dock Widget] " + message)
        self.dockwidget.update()

    def mapTool_graphic_log(self, message, level=Qgis.Info):
        self.dockwidget.logs_TextEdit.append("[Map tool] " + message)
        self.dockwidget.update()