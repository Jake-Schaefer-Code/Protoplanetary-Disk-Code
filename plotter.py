import matplotlib.pyplot as plt
import sys
import os
import numpy as np
import curveFitChi
"""
A module to plot SEDs produced by TORUS. Plots the SED due only to scattering, the SED due only to
thermal emission, the combined SED, and a series of observations. Also calculates the chi-squared 
of the combined SED and the observations. Applies a basic reddening correction to the observations; 
the only significant effect is an increase in the visual intensity. 
To run from the command line, the desired SED files must be in a subdirectory of the working directory.
The only command line argument is the directory name, i.e. python3 plotter.py 'directory name'
"""

def correctReddening(pointX, pointY):
    """
    Correct for reddening in the observed data. R_v = 3.1
    A_lam / A_v = a(x) + b(x) / R_v = shiftVal
    where shiftVal is given in CCM 1989
    """
    R_v = 3.1
    A_v = 0.5
    bandMidpoints = {
        # mostly for convenience
        "V": 0.55,
        "R": 0.658,
        "I": 0.806,
        "J": 1.22,
        "H": 1.63,
        "K": 2.19,
        "L": 3.45
    }
    bandMaxes = {
        # the midpoints between the band midpoints. Not a perfect way of defining the
        # ends of the bands, but it works
        0.604: "V",
        0.732: "R",
        1.013: "I",
        1.425: "J",
        1.91: "H",
        2.82: "K",
        np.inf: "L"
    }
    shiftVals = {
        # values of a(x) + b(x) / R_v for different bands
        "V": 1,
        "R": 0.751,
        "I": 0.479,
        "J": 0.282,
        "H": 0.190,
        "K": 0.114,
        "L": 0.056
    }
    maxList = []
    for key in bandMaxes:
        maxList.append(key)
    maxList.sort()

    maxVal = findBandMax(maxList, pointX)
    band = bandMaxes[maxVal]
    shiftVal = shiftVals[band]

    A_lam = A_v * shiftVal

    f_vega = {
        # * 10^-11 erg cm^-2 s^-1 A^-1
        # https://www.astronomy.ohio-state.edu/martini.10/usefuldata.html
        # L band flux calculated from https://www.gemini.edu/observing/resources/magnitudes-and-fluxes
        "V": 363.1,
        "R": 217.7,
        "I": 112.6,
        "J": 31.47,
        "H": 11.38,
        "K": 3.961,
        "L": 0.531
    }
    f_ref = f_vega[band] * 10 # convert from erg cm^-2 s^-2 A^-1 to W m^-2 um^-1
    flux = f_ref * pointX # convert to W m^-2

    mag = -2.5 * np.log10(pointY/flux) # convert to mags
    newMag = mag - A_lam # adjust for extinction
    correctedY = flux * 10 ** (newMag/(-2.5)) # convert back to flux

    return correctedY

def findBandMax(list, value):
    """
    A small recursive function to find the band of a given point.
    """
    if len(list) == 1:
        return list[0]
    elif list[-1] >= value and list[-2] < value:
        return list[-1]
    else:
        return(findBandMax(list[:-1], value))

def plotData(dataPath):
    """
    Plots the observations. Trims out points with no associated error or 0 error.
    As a note, this code tracks the source name of each point, which in most cases
    includes the band. A more precise reddening correction would likely just use the provided 
    bands. However, the result will likely be very similar to the result produced by the current
    reddening function.
    """

    fullfile = open(dataPath, "r")
    textfile = fullfile.read()

    filelines = textfile.splitlines()

    datalines = filelines[3:]

    lam = []
    lamFlam = []
    error = []
    names = []

    for i in range(len(datalines)):
        valueslist = datalines[i].split(" ")
        if valueslist[3] != 'nan' and float(valueslist[3]) != 0 and float(valueslist[0])*10**6 != 4.35:
            # removing points without error, 0 error, or that one point with a ton
            lam.append(float(valueslist[0])*10**6)
            lamFlam.append(float(valueslist[2]))
            error.append(float(valueslist[3]))
            names.append(valueslist[1])
                
    band = []
    for entry in names: # removing specifications and just using main source name
        colonsplit = entry.split(":")
        band.append(colonsplit[0])

    datadict = {}
    for j in range(len(band)):
        if datadict.get(band[j]) == None:
            datadict[band[j]] = [[lam[j], lamFlam[j], error[j]]]
        else:
            datadict[band[j]].append([lam[j], lamFlam[j], error[j]])

    minY = 1
    for key in datadict:
        x = []
        y = []
        err = []
        keydata = datadict[key]
        
        for k in range(len(keydata)):
            values = keydata[k]
            pointX = values[0]
            x.append(pointX)
            pointY = values[1]
            correctedY = correctReddening(pointX, pointY)
            y.append(correctedY)
            err.append(values[2])

            
        plt.scatter(x, y, s=15, label = str(key))
        plt.errorbar(x, y, yerr = err, fmt = 'None')
        
        if min(y) < minY:
            minY = min(y)
    return minY

def plotModel(modelPath, minY):
    """
    A function to plot the model SEDs produced by TORUS.
    """

    filename2 = modelPath.split('/')[-2]

    fullfile2 = open(modelPath, "r")
    textfile2 = fullfile2.read()

    filelines2 = textfile2.splitlines()

    datalines2 = filelines2[1:]

    lam2 = []
    flux2 = []
    names2 = []

    for i in range(len(datalines2)): # intentionally discarding the second and third columns because flux is 0
        valueslist2 = datalines2[i].split("     ")
        if float(valueslist2[2]) > minY:
            lam2.append(float(valueslist2[1]))
            flux2.append(float(valueslist2[2]))
        
    return (lam2,flux2)

    # below code is usable if only one SED is desirable. Returning the points instead of a plot is
    # better if plotting multiple SEDs.

    #plt.figure(figsize = (12,8))    
    # plt.plot(lam2, flux2)
    # plt.grid(False)

    # plt.xlabel('lambda (microns)')
    # plt.ylabel('flux ${W}/{m^2}$')
    # plt.suptitle("SED for " + filename2, fontsize = '18', y = 0.96)
    # plt.title("$\chi^2$ value: " + str(findChi(modelPath, dataPath)), fontsize = '15')

    # plt.legend()
        
    # plt.xscale('log')
    # plt.yscale('log')
    # filename = filename2 + '.png'
    # plt.savefig(filename)


def getSEDlist(directory):
    """
    A function to find all SED files within a directory.
    """
    fullList = os.listdir(directory)
    sedList = []
    for item in fullList:
        if 'sed_inc' in str(item):
            if str(item).count('_') == 1 or 'direct' in str(item):
                sedList.append(item)
    return sedList


def main(directory):

    fig = plt.figure(figsize = (16,10))
    plt.grid(False)
    plt.suptitle(directory + " SED (olin210pa65537)", fontsize = '18', y = 0.96)
    plt.xlabel('lambda ($\mu$m)')
    plt.ylabel('flux (W/${m^2}$)')

    minY = plotData('mwc275_phot_cleaned_0.dat')
    
    sedList = getSEDlist(directory)
    for SED in sedList:
        if str(SED).count('_') == 1:
            # only interested in plotting the main 3 SEDs right now
            mainSED = str(SED)
        modelPath = directory + '/' + SED
        coords = plotModel(modelPath, minY)
        x = coords[0]
        y = coords[1]
        plt.plot(x,y, label = str(SED).split('.')[0])

    modelPath = directory + '/' + mainSED
    chiTuple = curveFitChi.findChi(modelPath, 'mwc275_phot_cleaned_0.dat')
    # finding the chi-squared value using Jake's code

    nearIR = "Near IR $\chi^2$: " + str(float(f'{chiTuple[0]:.2f}')) + "    "
    midIR = "Mid IR $\chi^2$: " + str(float(f'{chiTuple[1]:.2f}')) + "    "
    farIR = "Far IR $\chi^2$: " + str(float(f'{chiTuple[1]:.2f}')) + "    "
    micro = "Microwave $\chi^2$: " + str(float(f'{chiTuple[3]:.2f}')) + "    "
    allChi = nearIR + midIR + farIR + micro

    plt.title(allChi)

    plt.legend(fontsize = '9')
    plt.xscale('log')
    plt.yscale('log')
    filename = directory + '.png'
    plt.savefig(filename)

if __name__ == '__main__':
    directory = str(sys.argv[1])
    main(directory)
