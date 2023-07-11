import numpy as np
from scipy import integrate, interpolate

def R770(rInterp):
    return rInterp(0.77)

def RBR(rInterp):
    return rInterp(0.77)/rInterp(0.44)

def BD530(rInterp):
    b = (0.530 - 0.648)/(0.440 - 0.648)
    a = 1-b
    return 1-(rInterp(0.530) / (a * rInterp(0.648) + b * rInterp(0.440)))

def SH600(rInterp):
    b = (0.600 - 0.530)/(0.680 - 0.530)
    a = 1-b
    return rInterp(0.600) / (a * rInterp(0.530) + b * rInterp(0.680))

def BD640(rInterp):
    b = (0.648 - 0.600)/(0.680 - 0.600)
    a = 1-b
    return 1-(rInterp(0.648) / (a * rInterp(0.600) + b * rInterp(0.680)))

def RPEAK1(rInterp):
    fit_wavelengths = np.array([0.648, 0.680, 0.710, 0.740, 0.770, 0.800, 0.830])
    fit_reflectances = rInterp(fit_wavelengths)

    fitPolynomial = np.polynomial.polynomial.Polynomial(np.polynomial.polynomial.polyfit(fit_wavelengths, fit_reflectances, deg=5))
    derivedPolynomial = fitPolynomial.deriv()
    roots = np.roots(derivedPolynomial.coef[::-1])
    realRoots = roots[np.isreal(roots)]
    peaks = []
    for root in realRoots:
        if root >= 0.648 and root <= 0.830:
            peaks.append(root)
    
    if len(peaks) == 0:
        return peaks[0]
    else:
        return 0

def IRA(rInterp):
    return rInterp(1.330)

def VAR(rInterp):
    X = np.linspace(1.3114, 2.5896, 256)
    Reflectances = rInterp(X)
    return np.var(Reflectances)

def ISLOPE1(rInterp):
    return (rInterp(1.815) - rInterp(2.530)) / (2.530 - 1.815)

def BD1435(rInterp):
    b = (1.43 - 1.37)/(1.47 - 1.37)
    a = 1-b
    return 1-(rInterp(1.43) / (a * rInterp(1.37) + b * rInterp(1.47)))

def BD1500(rInterp):
    b = (1.51 - 1.33)/(1.695 - 1.33)
    a = 1-b
    return 1-(rInterp(1.51) / (a * rInterp(1.33) + b * rInterp(1.695)))

def ICER1(rInterp):
    return rInterp(1.510) / rInterp(1.430)

def BD1750(rInterp):
    b = (1.75 - 1.660)/(1.815 - 1.660)
    a = 1-b
    return 1-(rInterp(1.75) / (a * rInterp(1.660) + b * rInterp(1.815)))

def BD1900(rInterp):
    b = (1.93 - 1.857)/(2.067 - 1.857)
    a = 1-b
    return 1-((rInterp(1.93) + rInterp(1.985)) * 0.5 / (a * rInterp(1.857) + b * rInterp(2.067)))

def BDI2000(rInterp):
    # Find 1.3-1.87 peak wavelength
    minWavelength = 1.3114
    maxWavelength = 1.87
    spectelsNumber = 300
    findPeak_wavelengths = np.linspace(minWavelength, maxWavelength, spectelsNumber)
    peakIndex = np.argmax(rInterp(findPeak_wavelengths))

    peakWavelength = minWavelength + (maxWavelength-minWavelength)*peakIndex/spectelsNumber

    # Linear fit of continuum between precedently found peak and 2.53 um
    continuumInterpolator = interpolate.interp1d(x=[peakWavelength, 2.53], y=[rInterp(peakWavelength), rInterp(2.53)])

    targetWavelengths = np.array([peakWavelength, 2.214, 2.21, 2.25, 2.29, 2.33, 2.35, 2.39, 2.53])

    continuumCorrectedReflectances = np.divide(rInterp(targetWavelengths), continuumInterpolator(targetWavelengths))

    # Modelling continuum-corrected band as a succession of linear fonctions
    continuumCorrectedReflectancesInterpolator = interpolate.interp1d(targetWavelengths, continuumCorrectedReflectances)
    bandDepth = lambda x: 1 - continuumCorrectedReflectancesInterpolator(x)

    # Integrate band depth between peak and 2.53 um
    return  integrate.quad(bandDepth, peakWavelength, 2.53)[0]

def BD2100(rInterp):
    b = (2.12 - 1.93)/(2.25 - 1.93)
    a = 1-b
    return 1-((rInterp(2.12) + rInterp(2.140)) * 0.5/ (a * rInterp(1.93) + b * rInterp(2.25)))
              
def BD2210(rInterp):
    b = (2.21 - 2.14)/(2.25 - 2.14)
    a = 1-b
    return 1-(rInterp(2.21) / (a * rInterp(2.14) + b * rInterp(2.25)))

def BD2290(rInterp):
    b = (2.29 - 2.25)/(2.35 - 2.25)
    a = 1-b
    return 1-(rInterp(2.29) / (a * rInterp(2.25) + b * rInterp(2.35)))

def D2300(rInterp):
    # Linear fit of continuum between 1.8 and 2.53 um
    continuumInterpolator = interpolate.interp1d(x=[1.8, 2.53], y=[rInterp(1.8), rInterp(2.53)])

    targetWavelengths = np.array([2.14, 2.17, 2.21, 2.29, 2.32, 2.33])

    continuumCorrectedReflectances = np.divide(rInterp(targetWavelengths), continuumInterpolator(targetWavelengths))

    # Aliasing continuumCorrectedReflectances as cr because it is too long and boring to write and read otherwise
    cr = continuumCorrectedReflectances

    return 1 - (cr[3] + cr[4] + cr[5])/(cr[0] + cr[1] + cr[2])

def D2400(rInterp):
    # Linear fit of continuum between 1.8 and 2.53 um
    continuumInterpolator = interpolate.interp1d(x=[1.8, 2.53], y=[rInterp(1.8), rInterp(2.53)])

    targetWavelengths = np.array([2.29, 2.32, 2.39, 2.43])

    continuumCorrectedReflectances = np.divide(rInterp(targetWavelengths), continuumInterpolator(targetWavelengths))

    # Aliasing continuumCorrectedReflectances as cr because it is too long and boring to write and read otherwise
    cr = continuumCorrectedReflectances

    return 1 - (cr[2] + cr[3])/(cr[0] + cr[1])

def R410(rInterp):
    return rInterp(0.410)

def BD1270O2(rInterp):
    shortWavelengthBandShoulder = 1.25
    longWavelengthBandShoulder = 1.28

    inBandWavelengths = np.array([1.261, 1.268])

    # Sum of BandDepths for each wavelength
    sum = 0
    for inBandWavelength in inBandWavelengths:
        b = (inBandWavelength - shortWavelengthBandShoulder)/(longWavelengthBandShoulder - shortWavelengthBandShoulder)
        a = 1-b
        sum += 1 - (rInterp(inBandWavelength) / (a*rInterp(shortWavelengthBandShoulder) + b*rInterp(longWavelengthBandShoulder)))

    # Normlize by the number of point taken inside of the band
    return sum / len(inBandWavelengths)


def BD1400H2O(rInterp):
    shortWavelengthBandShoulder = 1.33
    longWavelengthBandShoulder = 1.51

    inBandWavelengths = np.array([1.37, 1.4])

    # Sum of BandDepths for each wavelength
    sum = 0
    for inBandWavelength in inBandWavelengths:
        b = (inBandWavelength - shortWavelengthBandShoulder)/(longWavelengthBandShoulder - shortWavelengthBandShoulder)
        a = 1-b
        sum += 1 - (rInterp(inBandWavelength) / (a*rInterp(shortWavelengthBandShoulder) + b*rInterp(longWavelengthBandShoulder)))

    # Normlize by the number of point taken inside of the band
    return sum / len(inBandWavelengths)

def BD2000CO(rInterp):
    b = (2.010 - 1.815)/(2.17 - 1.815)
    a = 1-b
    return 1-(rInterp(2.010) / (a * rInterp(1.815) + b * rInterp(2.17)))

def BD2350(rInterp):
    shortWavelengthBandShoulder = 2.29
    longWavelengthBandShoulder = 2.43

    inBandWavelengths = np.array([2.32, 2.33, 2.35])

    # Sum of BandDepths for each wavelength
    sum = 0
    for inBandWavelength in inBandWavelengths:
        b = (inBandWavelength - shortWavelengthBandShoulder)/(longWavelengthBandShoulder - shortWavelengthBandShoulder)
        a = 1-b
        sum += 1 - (rInterp(inBandWavelength) / (a*rInterp(shortWavelengthBandShoulder) + b*rInterp(longWavelengthBandShoulder)))

    # Normlize by the number of point taken inside of the band
    return sum / len(inBandWavelengths)

def IRR2(rInterp):
    return rInterp(2.530) / rInterp(2.210)

def LCPINDEX(rInterp):
    shortWavelengthBandShoulder = 1.45
    longWavelengthBandShoulder = 2.3

    b = (1.82 - shortWavelengthBandShoulder)/(longWavelengthBandShoulder - shortWavelengthBandShoulder)
    a = 1-b
    return  1 - (rInterp(1.82) / (a*rInterp(shortWavelengthBandShoulder) + b*rInterp(longWavelengthBandShoulder)))

def SINDEX(rInterp):
    return (rInterp(2.12) + rInterp(2.4)) / rInterp(2.29)


GeologicParameters = {
    "R770" : {"type" : "VIS", "function" : R770, "description" : "Rock/dust"},
    "RBR" : {"type" : "VIS", "function" : RBR, "description" : "Rock/dust"},
    "BD530" : {"type" : "VIS", "function" : BD530, "description" : "Crystalline ferric minerals"},
    "SH600" : {"type" : "VIS", "function" : SH600, "description" : "Select ferric minerals"},
    "BD640" : {"type" : "VIS", "function" : BD640, "description" : "Select ferric mineral"},
    "RPEAK1" : {"type" : "VIS", "function" : RPEAK1, "description" : "Fe mineralogy"},
    "IRA" : {"type" : "IR", "function" : IRA, "description" : "IR albedo"},
    "VAR" : {"type" : "IR", "function" : VAR, "description" : "Olivine and pyroxene will have high values"},
    "ISLOPE1" : {"type" : "IR", "function" : ISLOPE1, "description" : "Ferric coating on dark rock"},
    "BD1435" : {"type" : "IR", "function" : BD1435, "description" : "CO2 ice"},
    "BD1500" : {"type" : "IR", "function" : BD1500, "description" : "H2O ice"},
    "ICER1" : {"type" : "IR", "function" : ICER1, "description" : "CO2, H2O ice mixtures"},
    "BD1750" : {"type" : "IR", "function" : BD1750, "description" : "Gypsum"},
    "BD1900" : {"type" : "IR", "function" : BD1900, "description" : "H2O"},
    "BDI2000" : {"type" : "IR", "function" : BDI2000, "description" : "Fe mineralogy"},
    "BD2100" : {"type" : "IR", "function" : BD2100, "description" : "Monohydrated minerals"},
    "BD2210" : {"type" : "IR", "function" : BD2210, "description" : "Al-OH minerals"},
    "BD2290" : {"type" : "IR", "function" : BD2290, "description" : "Mg,Fe-OH minerals; CO2 ice"},
    "D2300" : {"type" : "IR", "function" : D2300, "description" : "Hydrated min; phyllosilicates"},
    "D2400" : {"type" : "IR", "function" : D2400, "description" : "Hydrated min; sulfate"},
    "LCPINDEX" : {"type" : "IR", "function" : LCPINDEX, "description" : "Low-Ca Pyroxenes (1.82 um Band Depth)"},
    "SINDEX" : {"type" : "IR", "function" : SINDEX, "description" : "Hydrated Sulfates (2.12 + 2.4)/2.29"},
}

AtmosphericParameters = {
    "R410" : {"type" : "VIS", "function" : R410, "description" : "Unmodeled clouds/hazes"},
    "BD1270O2" : {"type" : "IR", "function" : BD1270O2, "description" : "O2 emission; inversely correlated with high altitude water; signature of ozone"},
    "BD1400H2O" : {"type" : "IR", "function" : BD1400H2O, "description" : "H2O vapor"},
    "BD2000CO" : {"type" : "IR", "function" : BD2000CO, "description" : "Atmospheric CO2"},
    "BD2350" : {"type" : "IR", "function" : BD2350, "description" : "CO"},
    "IRR2" : {"type" : "IR", "function" : IRR2, "description" : "Aphelion ice clouds vs. seasonal or dust"},
}