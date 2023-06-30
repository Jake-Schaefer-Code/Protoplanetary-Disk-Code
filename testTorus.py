import subprocess


def runTorus():
    def replaceValue(line, index, newVal):
        first = line[:index]
        second = line[index+1:]
        return first + [newVal] + second
    
    count = 0
    count2 = 0
    varNames = ["teff1", "rinnermod1", "grainfrac1", "grainfrac2"]
    tmpBest = [8600, 0.9, 0.012, 0.04]
    runFolder = "/home/schaeferj/models/gen" + str(count) + "/run" + str(count2)

    subprocess.call(['cd /home/schaeferj/models', '/'], shell=True)
    subprocess.call(['mkdir gen' + str(count) + '; cd /home/schaeferj/models/gen' + str(count), '/'], shell=True)

    subprocess.call(['mkdir run' + str(count2) + '; cd ' + runFolder, '/'], shell=True)
    
    
    originalParams = open("/home/schaeferj/models/modParameters.dat", "r").read()
    lines = originalParams.splitlines()
    f = open(runFolder + "/modParameters" + str(count2) + ".dat", "w")
    for line in lines:
        line = line.split(" ")
        varName = line[0]
        if varName in varNames:
            index = varNames.index(varName)
            newVal = str(tmpBest[index])
            line = replaceValue(line, 1, newVal)
        outputLine = ""
        for item in line:
            outputLine += str(item) + " "
        f.write(outputLine + '\n' )
    f.close()


    #output = subprocess.call(["/home/schaeferj/torus/bin/torus.openmp /home/schaeferj/models/modParameters.dat > output.txt &", '/'], shell=True)
    #subprocess.call(['cd ' + runFolder + '; ls', '/'], shell = True)
    process = subprocess.Popen(['/home/schaeferj/torus/bin/torus.openmp', runFolder + "/modParameters" + str(count2) + ".dat"])
    process.communicate()
    
    sed = '/home/schaeferj/models/sed_inc042.dat'
    chi = findChi(sed, "/home/schaeferj/models/mwc275_phot_cleaned_0.dat")
    f = open(runFolder + "/chi" + str(count2) + ".dat", "w")
    f.write(str(chi))
    f.close()
    subprocess.call(["mv /home/schaeferj/models/sed_inc042.dat " + runFolder, '/'], shell=True)

    # Unnecessary, but prints completed message
    completeStr = "Run " + str(count2) + " Complete"
    decor = "%"*len(completeStr)
    subprocess.call(["cd ..; echo " + decor, '/'], shell=True)
    subprocess.call(["echo  Run " + str(count2) + " Complete", '/'], shell=True)
    subprocess.call(["cd ..; echo " + decor, '/'], shell=True)



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

runTorus()
    




