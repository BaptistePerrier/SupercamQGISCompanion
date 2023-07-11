import pandas as pd
import numpy as np

from qgis.core import QgsPoint

class Positioner():
    def __init__(self, best_interp_path, best_tactical_path):
        self.best_interp_path = best_interp_path
        self.best_tactical_path = best_tactical_path

        self.roverPositioningFilesOpen = False

    def openRoverPositioningFiles(self):
        self.best_interp = pd.read_csv(self.best_interp_path)
        self.best_tactical = pd.read_csv(self.best_tactical_path)

        self.roverPositioningFilesOpen = True

    def closeRoverPositioningFiles(self):
        del self.best_tactical
        del self.best_interp

        self.roverPositioningFilesOpen = False

    def retrieveRoverPosition(self, sclk):
        """Returns the rover coordinates at a givent time (sclk). Based on best_tactical if available (positions reviewed by team), and best_interp otherwise (autonomous interpolation of rover position)

        :param sclk: The time at which to compute rover position
        :type sclk: int
        :param best_interp: pd.DataFrame from pd.read_csv(best_interp_file)
        :type best_interp: pd.DataFrame
        :param best_tactical: pd.DataFrame from pd.read_csv(best_interp_tactical)
        :type best_tactical: pd.DataFrame

        :return: Dictionnary containing : {"source" : "best_interp/best_tactical", "coordinates" : [lat, lon]}
        :rtype: dict
        """

        if not self.roverPositioningFilesOpen:
            raise Exception("Tried to retrieve rover position (via Positioner.retrieveRoverPosition) before opening data files (via Positioner.openRoverPositioningFiles). Don't forget to close data files after use.")
        
        # Get the last registered localization for the rover in both best_interp and best_tactical
        last_interp = self.best_interp[self.best_interp["sclk"]<sclk].sort_values(by="sclk").tail(1)
        last_tactical = self.best_tactical[self.best_tactical["sclk"]<sclk].sort_values(by="sclk").tail(1)

        # Get the last timestamps where the positions have been registered in both tactical and interp
        last_interp_sclk = last_interp.sclk.values[0]
        last_tactical_sclk = last_tactical.sclk.values[0]

        interp_coordinates = [float(last_interp.planetocentric_latitude.values[0]), float(last_interp.longitude.values[0])]
        tactical_coordinates = [float(last_tactical.planetocentric_latitude.values[0]), float(last_tactical.longitude.values[0])]

        if last_interp_sclk > last_tactical_sclk: # If interp and auto are old egal, choose tactical, otherwise tactical has not been updated for the current rover position and thus we choose interp
            return {"source" : "best_interp", "coordinates" : interp_coordinates}
        else:
            return {"source" : "best_tactical", "coordinates" : tactical_coordinates}
        
    def retrieveShotPosition(self, azimuth, focusPosition_mm, roverCoordinates):
        """ Returns the position of a measure made by the rover, given the position of the rover, the azimuth and focus of the measure

        :param azimuth: Azimuth (ie angle to the north) of the measure, given in degree ?
        :type azimuth: float
        :param focusPosition_mm: Distance of focus, given in mm
        :type focusPosition_mm: int
        :param roverCoordinates: Coordinates of the rover [lat, lon]
        :type roverCoordinates: list

        :return: Coordinates of the shot [lat, lon]
        :rtype: list
        """
        try:
            groundDistance = np.sqrt((focusPosition_mm/1000)**2 - 2.2**2) # Assuming supercam is 2.2 meters high
        except:
            groundDistance = 3 # if can't compute ground distance, assume the measure was made 3 meters away from the rover
        
        groundDistance = 0.00002 * groundDistance # Don't know why but need to correct groundDistance for QgsPoint.project to project at a reasonable distance

        Qgs_roverCoordinates = QgsPoint(roverCoordinates[1], roverCoordinates[0])
        Qgs_pointCoordinates = Qgs_roverCoordinates.project(groundDistance, azimuth) # Check whether inst_az is given relative to RoverNAV frame or LocalLevel frame; doesn't work well for long distances

        return [Qgs_pointCoordinates.x(), Qgs_pointCoordinates.y()]
                    