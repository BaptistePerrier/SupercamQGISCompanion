from .. import misc
from . import constants as PDSConstants
import os
from bs4 import BeautifulSoup
import requests

def retrieveRMI(name):
    pass

def getLinksListOnPage(pageLink):
    linksPage = requests.get(pageLink)
    linkPage_soup = BeautifulSoup(linksPage.content, "html.parser")
    fileLinks = linkPage_soup.find_all("a")[1:] # Exclude "Parent Directory" link

    # create a list for shortened filenames to match with spectra names
    shortenedFileNames = {}
    for link_soup in fileLinks:
        link = link_soup.get('href')
        if link.split(".")[-1] == "fits":
            shortenedFileNames[link.split("/")[-1][:-8]] = link.lower()

    return shortenedFileNames

def dl(url, localPath):
    if not os.path.exists(os.path.split(localPath)[0]):
        os.makedirs(os.path.split(localPath)[0])

    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(localPath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def getLink(sol, fileName):
    linksPage_link = PDSConstants.PDSWEBSITEBASE + "/data_calibrated_spectra" + "/sol_{:05d}".format(sol)

    shortenedFileNames = getLinksListOnPage(linksPage_link)    

    fileName = fileName.lower()
    shortenedfileName = fileName[:-8]

    if shortenedfileName in shortenedFileNames.keys():
        return PDSConstants.PDSWEBSITE + shortenedFileNames[shortenedfileName]
    else:
        raise Exception("File not found on PDS.")

def downloadShotFile(sclk, fileName, forceDownload=False):
    """If file doesn't exist or forceDownload is set to True, downloads a shot file from PDS archive. Returns its absolute path on local computer.

    :param sclk: sclk ssociated with the file
    :type sclk: int
    :param fileName: file name on PDS archive, containing the final "pXX.fits"
    :type fileName: str
    :param forceDownload: Set to True to force a download of an already existing file on local computer
    :type forceDownload: True
    :return: Absolute path of downloaded file
    :rtype: str
    """
    sol = misc.functions.getSolFromsclk(sclk)
    filePath = os.path.join(misc.constants.LOCALFOLDER, PDSConstants.PDSLOCALDATAFOLDER, "data_calibrated_spectra", "sol_{:05d}".format(sol), fileName[:-8].lower() + ".fits")

    if os.path.exists(filePath) and not forceDownload:
        return filePath
    
    DLLink = getLink(sol, fileName)

    # Download the file to the computer
    dl(DLLink, filePath)

    return filePath

def downloadShotFiles(files, forceDownload=False):
    """[Method to prefer to multiple downloadFile if you are downloading several PDS files] If file don't exist or forceDownload is set to True, downloads a list of files from PDS archive. Returns their absolute path on local computer.

    :param files: A list of dicts containing sclk and filename. Eg : [{'sclk' : sclk01, 'fileName' : 'fileNamr01}, {'sclk' : sclk02, 'fileName' : 'fileNamr02}, ...]
    :type files: list of dicts
    :returns: List of absolute path of downloaded files
    :rtype: list of str
    """
    filePaths = []
    linksOnPage = {}
    for file in files:
        sol = misc.functions.getSolFromsclk(file["sclk"])

        fileName = file["fileName"].lower()
        shortenedfileName = fileName[:-8]

        filePath = os.path.join(misc.constants.LOCALFOLDER, PDSConstants.PDSLOCALDATAFOLDER, "data_calibrated_spectra", "sol_{:05d}".format(sol), shortenedfileName + ".fits")

        if not os.path.exists(filePath) or forceDownload:
            if not sol in linksOnPage.keys():
                linksPage_link = PDSConstants.PDSWEBSITEBASE + "/data_calibrated_spectra" + "/sol_{:05d}".format(sol)
                linksOnPage[sol] = getLinksListOnPage(linksPage_link)

            DLLink = PDSConstants.PDSWEBSITE + linksOnPage[sol][shortenedfileName]
        
            dl(DLLink, filePath)

        filePaths.append(filePath)

    return filePaths


    

    