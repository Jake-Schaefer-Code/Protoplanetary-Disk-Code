import matplotlib.pyplot as plt

def getLine(point1, point2):
    return (point1, (point2[1]-point1[1])/(point2[0]-point1[0]))

def findIntercept(modelPoint, line):
    x = modelPoint[0]
    y = line[1]*(x-line[0][0]) + line[0][1]
    return (x, y)

def findChi(modelPath, dataPath, count2):

    modelFile = open(modelPath, 'r')
    modelText = modelFile.read()
    modelLines = modelText.splitlines()

    dataFile = open(dataPath, "r")
    dataText = dataFile.read()
    dataLines = dataText.splitlines()

    modelDataLines = modelLines[1:]
    dataLines = dataLines[3:]

    modelLam, modelFlux = [], []
    dataLam, dataFlux, error, names = [], [], [], []


    for i in range(len(modelDataLines)): # intentionally discarding the second and third columns because flux is 0
        valueslist2 = modelDataLines[i].split("     ")
        modelLam.append(float(valueslist2[1]))
        modelFlux.append(float(valueslist2[2]))

    for i in range(len(dataLines)):
        valueslist = dataLines[i].split(" ")
        if valueslist[3] != 'nan' and float(valueslist[3]) != 0 and float(valueslist[0])*10**6 != 4.35:
            dataLam.append(float(valueslist[0])*10**6)
            names.append(valueslist[1])
            dataFlux.append(float(valueslist[2]))
            error.append(float(valueslist[3]))
        
    listOfRanges = []
    xyerrTuples = [(dataLam[i],dataFlux[i],error[i]) for i in range(len(dataLam))]
    modelTuples = [(modelLam[i],modelFlux[i]) for i in range(len(modelLam))]
    fitPts = [[dataLam[i],dataFlux[i],error[i]] for i in range(len(dataLam))]
    xyerrTuples.sort()
    fitPts.sort()
    pointDict = {'x':[], 'y':[]}
    modelPointDict = {'x':[], 'y':[]}

    # Creating a dictionary of the data points based on author
    for i in range(len(names)):
        names[i] = names[i].split(":")[0]
        if pointDict.get(names[i]) == None:
            pointDict[names[i]] = [list(xyerrTuples[i])]
        else:
            pointDict[names[i]] += [list(xyerrTuples[i])]

    for tuple in xyerrTuples:
        pointDict['x'] += [tuple[0]]
        pointDict['y'] += [tuple[1]]

    for tuple in modelTuples:
        modelPointDict['x'] += [tuple[0]]
        modelPointDict['y'] += [tuple[1]]

    count = 0
    for j in range(len(xyerrTuples)-1):
        if xyerrTuples[j][0] == xyerrTuples[j+1][0]:
            fitPts[count][1] = (xyerrTuples[j][1] + xyerrTuples[j+1][1])/2
            fitPts[count][2] = (xyerrTuples[j][2] + xyerrTuples[j+1][2])/2
            fitPts.pop(count+1)
        else:
            xmin = xyerrTuples[j][0]
            xmax = xyerrTuples[j+1][0]
            listOfRanges.append((xmin, xmax, count))
            count += 1


    dictOfBins = {"nearIr":{ranges:[] for ranges in listOfRanges[:14]}, "midIr":{ranges:[] for ranges in listOfRanges[14:25]}, 
                    "farIr":{ranges:[] for ranges in listOfRanges[25:31]}, "micro":{ranges:[] for ranges in listOfRanges[31:]}}


    for point in modelTuples:
        for i in range(len(listOfRanges)):
            valuerange = listOfRanges[i]
            if valuerange[0] < point[0] and valuerange[1] >= point[0]:
                # If the point lies in the nearIR spectrum
                if i < 14: dictOfBins["nearIr"][valuerange] += [(point, valuerange[2])] #point and index
                # midIR
                elif 14 <= i and i < 25: dictOfBins["midIr"][valuerange] += [(point, valuerange[2])]
                # farIR
                elif 25 <= i and i < 31: dictOfBins["farIr"][valuerange] += [(point, valuerange[2])]
                # microwave
                else: dictOfBins["micro"][valuerange] += [(point, valuerange[2])]
                    

    plt.figure(facecolor='#808080')
    ax = plt.axes()
    ax.set_facecolor("#404040")
    plt.plot(modelPointDict['x'], modelPointDict['y'], color="white", alpha=0.75)
    
    nearIrChi, midIrChi, farIrChi, microChi = 0, 0, 0, 0
    for irBin in dictOfBins:
        for valuerange in dictOfBins[irBin]:
            valuesInBin = dictOfBins[irBin][valuerange]
            binIndex = valuerange[2]
            binPoint1 = (fitPts[binIndex][0],fitPts[binIndex][1])
            binPoint2 = (fitPts[binIndex + 1][0],fitPts[binIndex + 1][1])
            for value in dictOfBins[irBin][valuerange]:
                modelPoint = value[0]
                binLine = getLine(binPoint1, binPoint2)
                expPoint = findIntercept(modelPoint, binLine)
                errorValue = fitPts[binIndex][2]
                variance = (modelPoint[1]-errorValue)**2
                d_chi = (modelPoint[1]-expPoint[1])**2 / expPoint[1] **2
                
                if irBin == "nearIr": nearIrChi += d_chi   
                elif irBin == "midIr": midIrChi += d_chi
                elif irBin == "farIr": farIrChi += d_chi
                else: microChi += d_chi

    # Weighting the Chi values based on the number of data points
    nearIrChi = (nearIrChi * len(listOfRanges)) / len(listOfRanges[:14])
    midIrChi = (midIrChi * len(listOfRanges)) / len(listOfRanges[14:25])
    farIrChi = (farIrChi * len(listOfRanges)) / len(listOfRanges[25:31])
    microChi = (microChi * len(listOfRanges)) / len(listOfRanges[31:])
    totalChi = nearIrChi + midIrChi + farIrChi + microChi

    # Plotting the graph based on wavelength ranges
    plt.plot([fitPts[i][0] for i in range(len(fitPts[:15]))],[fitPts[i][1] for i in range(len(fitPts[:15]))], color="#FFCC00", alpha=0.75)
    plt.plot([fitPts[i+14][0] for i in range(len(fitPts[14:26]))],[fitPts[i+14][1] for i in range(len(fitPts[14:26]))], color="#FF6600", alpha=0.75)
    plt.plot([fitPts[i+25][0] for i in range(len(fitPts[25:31]))],[fitPts[i+25][1] for i in range(len(fitPts[25:31]))], color="#FF3300", alpha=0.75)
    plt.plot([fitPts[i+30][0] for i in range(len(fitPts[30:]))],[fitPts[i+30][1] for i in range(len(fitPts[30:]))], color="#CC0066", alpha=0.75)

    # Plotting data points and error bars
    for key in pointDict:
        xVals, yVals, errVals = [],[],[]
        for val in pointDict[key]:
            xVals += [val[0]]
            yVals += [val[1]]
            errVals += [val[2]]
        plt.scatter(xVals, yVals, marker="o", linewidths=0.5, label = str(key), alpha = 0.75)
        plt.errorbar(xVals, yVals, yerr = errVals, fmt = 'None', ecolor='white', alpha=0.5)
    
    # Saving the figure
    plt.savefig("sed"+str(count2)+".png")

    return totalChi