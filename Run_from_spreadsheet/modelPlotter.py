import matplotlib.pyplot as plt
import sys

"""
This is a terribly written module that will plot the SED with error bars against
a model given in the command line and calculate the chi squared value.

To do:
-- there's a lot of repetition between the two primary functions. Need to trim the repeats
out and just make them their own function. 

-- I would love to make this runnable from anywhere, and I also would like to somehow automate
the path name, so I don't have to cd every time I want to run this module.

-- document the weird parts of this that I will definitely forget

As of 3/2/2023, this module is running
smoothly.
"""

def findChi(modelPath, dataPath):
    """
    Calculates the chi squared value for two sets of data.
    """
    
    modelFile = open(modelPath, 'r')
    modelText = modelFile.read()
    modelLines = modelText.splitlines()
    
    dataFile = open(dataPath, "r")
    dataText = dataFile.read()
    dataLines = dataText.splitlines()

    dataLines = dataLines[3:]
    modelDataLines = modelLines[1:]
    
    dataLam = []
    dataFlux = []
    error = []
    
    modelLam = []
    modelFlux = [] 

    for i in range(len(modelDataLines)): # intentionally discarding the second and third columns because flux is 0
        valueslist2 = modelDataLines[i].split("     ")
        modelLam.append(float(valueslist2[1]))
        modelFlux.append(float(valueslist2[2]))
    
    for i in range(len(dataLines)):
        valueslist = dataLines[i].split(" ")
        if valueslist[3] != 'nan' and float(valueslist[3]) != 0:
            dataLam.append(float(valueslist[0])*10**6)
            dataFlux.append(float(valueslist[2]))
            error.append(float(valueslist[3]))
    
    listofranges = []

    xyerrTuples = []

    modelTuples = []

    for i in range(len(dataLam)):
        xyerrTuples.append((dataLam[i],dataFlux[i], error[i]))

    for i in range(len(modelLam)):
        modelTuples.append((modelLam[i], modelFlux[i]))

    xyerrTuples.sort()

    # now we have a list of x, y, and error values sorted by x
    # and a list of the x and y values of the model

    for j in range(len(xyerrTuples)):

        if j == 0:
            xmin = 0
        else:
            xmin = (xyerrTuples[j][0] + xyerrTuples[j-1][0])/2

        if j == len(xyerrTuples)-1:
            xmax = xyerrTuples[j][0]
        else:
            xmax = (xyerrTuples[j+1][0] + xyerrTuples[j][0])/2

        listofranges.append((xmin, xmax, j))


    # Everything that happens in this dictOfBins business is something of a relic. I
    # made it early in the process when I was calculating chi2 based on the average value
    # of the model points closest to a data point. That is not the best way to calculate chi2!
    # This system finds the two model points on either side of a data point, averages their 
    # values, and calculates chi2 from that. The system still works fine and I don't want to 
    # break it, and it has the neat upside of binning all the model points according to the data,
    # which could be useful later. It also helpfully filters all the data points that are better
    # matched with other model points.

    dictOfBins = {}

    for entry in modelTuples:
        for i in range(len(listofranges)):
            valuerange = listofranges[i]
            if valuerange[0] < entry[0] and valuerange[1] >= entry[0]: # if x-value is within the bin
                if dictOfBins.get(valuerange) == None:
                    dictOfBins[valuerange] = [(entry, valuerange[2])]
                else:
                    dictOfBins[valuerange].append((entry, valuerange[2]))
    chi2 = 0

    for valuerange in dictOfBins:

        valuesInBin = dictOfBins[valuerange] # nested tuple of ((x, y) for model points, index of data point)

        index = valuesInBin[0][1]

        expectedX = xyerrTuples[index][0]
        expectedY = xyerrTuples[index][1]

        if len(valuesInBin) == 1:
            modelValue = valuesInBin[0][0][1]
            wavelength = valuesInBin[0][0][0]  # useful for figuring out how the model matches up
        else:
            lower = 0
            upper = 10000
            for i in range(len(valuesInBin)):  # this takes a bin, starts at the lowest and highest values, and narrows in on the data point
                xpos = valuesInBin[i][0][0]
                ypos = valuesInBin[i][0][1]
                ymin = 0
                ymax = 0
                if xpos < expectedX and xpos > lower:
                    lower = xpos
                    ymin = ypos
                elif xpos >= expectedX and xpos < upper:
                    upper = xpos
                    ymax = ypos

            if lower == 0:
                modelValue = ymax
                wavelength = upper
            elif upper == 10000:
                modelValue = ymin
                wavelength = lower
            else:
                modelValue = (ymin + ymax)/2
                wavelength = (lower+upper)/2
        
        errorValue = xyerrTuples[index][2]

        d_chi2 = (modelValue - expectedY)**2 / errorValue**2 # standard chi2 calculation with error
#         print('Wavelength: ', wavelength)
#         print('d_chi: ', d_chi2)
#         print()
        chi2 += d_chi2
    
    return chi2

########################

def plotModel(modelPath, dataPath):
    fig = plt.figure(figsize = (16,10))
    #SED = plt.figure(figsize = (15, 10))
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

    for key in datadict:
        x = []
        y = []
        err = []
        keydata = datadict[key]
        
        for k in range(len(keydata)):
            values = keydata[k]
            x.append(values[0])
            y.append(values[1])
            err.append(values[2])
            
        plt.scatter(x, y, s=15, label = str(key))
        plt.errorbar(x, y, yerr = err, fmt = 'None')
        
    ####### Model
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
        lam2.append(float(valueslist2[1]))
        flux2.append(float(valueslist2[2]))
        
    #plt.figure(figsize = (12,8))    
    plt.plot(lam2, flux2)
    plt.grid(False)

    plt.xlabel('lambda (microns)')
    plt.ylabel('flux ${W}/{m^2}$')
    plt.suptitle("SED for " + filename2, fontsize = '18', y = 0.96)
    plt.title("$\chi^2$ value: " + str(findChi(modelPath, dataPath)), fontsize = '15')

    plt.legend()
        
    plt.xscale('log')
    plt.yscale('log')
    filename = filename2 + '.png'
    plt.savefig(filename)


modelPath = str(sys.argv[1]) # unfamiliar with the syntax, but this seems to be working as intended

def main(modelPath):
    plotModel(modelPath, "/home/driscollg/models/mwc275_phot_cleaned_0.dat")

if __name__ == '__main__':
    main(modelPath)
