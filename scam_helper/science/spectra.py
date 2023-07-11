from astropy.io import fits
from scipy import signal

from .. import PDS

def getSpectralData(sclk, cdr_fnames):
    reflectances = []

    f = [{"sclk" : sclk, "fileName" : fname} for fname in cdr_fnames]

    localFilePaths = PDS.functions.downloadShotFiles(f)

    for filePath in localFilePaths:
        Headerfitslist = fits.open(filePath)
        reflectances.append(Headerfitslist['SPECTRA'].data['I_F_atm'])
        wavelengths = (Headerfitslist['WAVELENGTH'].data['Wavelength (um)'])
        Headerfitslist.close()
    
    return (wavelengths, reflectances)

def getSmoothedSpectrum(reflectance):
    return(signal.savgol_filter(reflectance, window_length=11, polyorder=3, mode="nearest"))