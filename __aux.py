import os
import requests
from bs4 import BeautifulSoup
import shutil
from lxml import etree

from enum import Enum

from qgis.PyQt.QtCore import pyqtSignal, QObject

# Odd syntax to trick python into importing local module 'utils'
from .utils import functions
from .utils import constants

class misc():
    functions = functions
    constants = constants


class FileProvider(QObject):

    log = pyqtSignal(str)

    def __init__(self, localFolder) -> None:
        super(FileProvider, self).__init__()
        self.localFolder = localFolder
        if not os.path.exists(self.localFolder):
            os.mkdir(self.localFolder)
        
        self.pds_local_data_folder = os.path.join(self.localFolder, "pds_local_data")
        if not os.path.exists(self.pds_local_data_folder):
            os.mkdir(self.pds_local_data_folder)

        self.openFiles = {}

    def fetchPDSDataFile(self, sclk, fileName):
        sol = misc.functions.getSolFromsclk(sclk)

        if os.path.exists(os.path.join(self.pds_local_data_folder, "sol_{:05d}".format(sol), fileName[:-8] + ".fits")):
            filePath = self.fetchPDSFile("/", os.path.join("sol_{:05d}".format(sol), fileName[:-8] + ".fits")) # No need to specify an URL because the file exists !
            return filePath
        
        linksPage_link = misc.constants.PDSWEBSITEBASE + misc.constants.PDSSHOTSDATAFOLDER + "/sol_{:05d}".format(sol)
        linksPage = requests.get(linksPage_link)
        linkPage_soup = BeautifulSoup(linksPage.content, "html.parser")
        fileLinks = linkPage_soup.find_all("a")[1:] # Exclude "Parent Directory" link

        # create a list for shortened filenames to match with spectra names
        shortenedFileNames = {}
        for link_soup in fileLinks:
            link = link_soup.get('href')
            if link.split(".")[-1] == "fits":
                shortenedFileNames[link.split("/")[-1][:-8]] = link
        
        i = 0
        fileName = fileName.lower()
        shortenedfileName = fileName[:-8]
        if shortenedfileName in shortenedFileNames.keys():
            filePath = self.fetchPDSFile(misc.constants.PDSWEBSITE + shortenedFileNames[shortenedfileName], os.path.join("sol_{:05d}".format(sol), fileName[:-8] + ".fits"))
            return filePath
        else:
            self.log.emit("{} not found on PDS !")
            return ""

    def fetchPDSFile(self, url, filePath, forceDownload=False):
        """Retrieves the requested file if does not already exist in the local folder

        :param url: Url of the requested file.
        :type url: str

        :param filePath: Path where to register the file.
        :type filePath: str

        :return: Path to the file
        :rtype: str
        """
        absolutePath = os.path.join(self.pds_local_data_folder, filePath)

        if not os.path.exists(absolutePath) or forceDownload:
            self.log.emit("Fetching {} from PDS (this might take a while) ...".format(filePath))

            if not os.path.exists(os.path.split(absolutePath)[0]):
                os.mkdir(os.path.split(absolutePath)[0])

            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(absolutePath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            self.log.emit("{} already present in local folder".format(filePath))

        return absolutePath
    
    def path(self, localPath):
        return os.path.join(self.localFolder, localPath)
    
    def open(self, relativePath, mode, createIfNotExists=True):
        absolutePath = os.path.join(self.localFolder, relativePath)
        if not os.path.exists(os.path.split(absolutePath)[0]):
                os.mkdir(os.path.split(absolutePath)[0])

        if not os.path.exists(relativePath) and createIfNotExists:
            open(os.path.join(self.localFolder, relativePath), 'a').close()

        try:
            f = open(os.path.join(self.localFolder, relativePath), mode)
            self.openFiles[relativePath] = f
            return f
        except:
            self.log.emit("Could not open file {}, with mode {}. Check if the file exists and for your permissions in {}".format(relativePath, mode, self.localFolder))
            return -1
    
    def close(self, relativePath):
        if relativePath in self.openFiles.keys():
            f = self.openFiles.pop(relativePath)
            f.close()
        else:
            self.log.emit("File was not open, thus you can't close it.")

    def closeAll(self):
        """Closes all files. Intended to be used on plugin closure.        
        """
        for file, fileLocalPath in self.openFiles.items():
            self.close(fileLocalPath)  

class PDSFile():
        def __init__(self, fileProvider, shotType, fileName):
            """Constructor.
            :param fileProvider: FileProvider used in the current scope
            :type fileProvider: FileProvider
            :param shotType: Type of measure (IRS, Raman, LIBS ...)
            :type shotType: PDSShot.ShotType
            :param fileName: Name of the .fits file that contains the data of the measure
            :type fileName: str"""
            self.fileProvider = fileProvider
            self.shotType = shotType
            self.fileName = fileName
            self.metadataFileName = self.fileName[:-5] + ".xml" # Removes ".fits" and adds ".xml"

            self.sclk = int(self.fileName[10:20]) # SCLK is at a fixed position in filename

            self.solFolderName = "sol_{:05d}".format(misc.functions.getSolFromsclk(self.sclk))

            self.fileUrl = self._buildUrl(self.fileName)
            self.metadataFileUrl = self._buildUrl(self.metadataFileName)

            try:
                self.filePath = self.fileProvider.fetchFile(self.fileUrl, os.path.join(self.solFolderName, self.fileName))
            except:
                #self.fileProvider.log.emit("Error while fetching the file {} at the url {}".format(self.fileName, self.fileUrl))
                return

            try:
                self.metadataFilePath = self.fileProvider.fetchFile(self.metadataFileUrl, os.path.join(self.solFolderName, self.metadataFileName))
            except:
                #self.fileProvider.log.emit("Error while fetching the metadata file {} at the url {}".format(self.metadataFileName, self.metadataFileUrl))
                return
                

            # Retrieve url from fileName
            # Retrieve metadataFileName

            # retrieve data file
            # retrieve metadata file

        def _readMetadata(self):
            """Reads useful metadata from the .xml companion file
            :return: Dictionary containing metadata
            """
            tree = etree.parse(self.metadataFilePath)
            # Récupérer les infos
        
        def _buildUrl(self, fileName):
            # Assuming the QGISPerseveranceMaster.geojson has been filled with the filenames that are actually on the pds web archive, and not with the filenames in the MasterList (both differ from the 2 last caracters)
            return misc.constants.PDSWEBSITEBASE + misc.constants.PDSSHOTSDATAFOLDER + self.solFolderName + "/" + self.fileName

        @property
        def path(self):
            return self._localPath
        
        @property
        def url(self):
            return self.url

class PDSShot():
    class ShotType(Enum):
        IRSShot = 1
        VisibleShot = 2
        LIBSShot = 3
        RamanShot = 4
        MicShot = 5
        
    def __init__(self, fileProvider, shotType, cdr_fnamesList) -> None:
        """Constructor.
        :param fileProvider: FileProvider used in the current scope
        :type fileProvider: FileProvider
        :param shotType: Type of measure (IRS, Raman, LIBS ...)
        :type shotType: PDSShot.ShotType
        :param cdr_fnamesList: List of the files associated with the shot
        :type cdr_fnamesList: list"""
        self.fileProvider = fileProvider
        self.shotType = shotType
        self.files = [PDSFile(self.fileProvider, self.shotType, fileName) for fileName in cdr_fnamesList]

    def meanInstrumentAttitude(self):
        """Averages the attitude (azimuth and elevation) of the instrument over the different spectra
        :return: The average azimuth and the average elevation
        :rtype: dictionnary {"azimuth" : xxx, "elevation" : xxx}
        """

    def meanSpectrum(self):
        """Processes the mean spectrum for the shot
        :return: A tuple containing the X axis as a numpy array and the Y axis as a numpy array
        :rtype: tuple
        """
        pass

    def spectra(self):
        """Returns the specrea data read from the files
        :return: A tuple containing the X axis and a numpy array containing the values of the different spectra going along the Y axis
        :rtype: tuple (X-axis, np.ndarray([Y1, Y2, ...]))
        """
        pass

