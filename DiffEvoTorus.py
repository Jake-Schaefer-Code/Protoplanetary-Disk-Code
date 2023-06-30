import numpy as np
import subprocess
count = 0
count2 = 1
baseDir = "/Users/schaeferj/models" # Base Directory
torusDir = "/Users/schaeferj/torus/bin/torus.openmp"
# baseDir = "/home/schaeferj/models"
# torusDir = "/home/schaeferj/torus/bin/torus.openmp"

def differential_evolution(converged, mutation = (0.5,1.0), P = 0.7, popSize = 10):
    bounds = np.array([[1.5, 3.0], [1.0, 2.0], [0.00333, 0.0133]]) # Each entry bounds[i,:] = upper, lower bounds of i
    varNames = ["alphamod1", "betamod1", "grainfrac1"] # Variable names corresponding to bound indices
    global count, baseDir
    
    def replaceValue(line, index, newVal):
        first = line[:index]
        second = line[index+1:]
        return first + [newVal] + second

    def objective_fn(params):
        global count, count2, torusDir, baseDir
        num2 = str(count2)
        runFolder = baseDir + "/gen" + str(count) + "/run" + num2
        # Creates new directory for the run number
        subprocess.call(['cd ' + baseDir, '/'], shell=True)
        subprocess.call(['mkdir ' + runFolder + '; cd ' + runFolder, '/'], shell=True)
        
        # Creates new Parameters file
        originalParams = open(baseDir + '/modParameters.dat', 'r').read()
        lines = originalParams.splitlines()
        lineDict, outputLines = {}, []
        f = open(runFolder + '/modParameters' + num2 + '.dat', 'w') # New param file numbered to run
        for line in lines:
            line = line.split(' ')
            varName = line[0]
            if varName in varNames:
                index = varNames.index(varName)
                newVal = params[index]
                line = replaceValue(line, 1, newVal)
            lineDict[varName] = line
            outputLines += [line]
            
        rPrev, rCur, hPrev = 100, lineDict["rinnermod1"][1], 10
        betamod = lineDict["betamod1"][1]
        for line in outputLines:
            varName = line[0]
            if "alphamod" in varName:
                newVal = float(lineDict["alphamod1"][1])
                line = replaceValue(line, 1, str(newVal))
            if "betamod" in varName:
                newVal = betamod
                line = replaceValue(line, 1, str(newVal))
            if "heightmod" in varName:
                newVal = hPrev * ((rCur/rPrev) ** betamod)
                line = replaceValue(line, 1, str(newVal))
                hPrev = newVal
                modNum = int(varName[-1])
                if modNum < 5:
                    rPrev = float(lineDict["rinnermod" + str(modNum)][1])
                    rCur = float(lineDict["rinnermod" + str(modNum + 1)][1])
            if "settleheight" in varName:
                if varName[-1] == "1":
                    newVal = 0.7*hPrev
                else:
                    newVal = 0.1*hPrev
                line = replaceValue(line, 1, str(newVal))
            
            outputLine = ""
            for item in line:
                outputLine += str(item) + ' '
            print(outputLine)
            f.write(outputLine + '\n' )
        f.close()

        # Runs TORUS and waits
        process = subprocess.Popen([torusDir, runFolder + '/modParameters' + num2 + '.dat'])
        process.communicate()
        process.wait()
        
        # Finds Chi Square and writes it in a file
        sed = baseDir + '/sed_inc042.dat'
        chi = findChi(sed, baseDir + '/mwc275_phot_cleaned_0.dat')
        f = open(runFolder + '/chi' + num2 + '.dat', 'w')
        f.write(str(chi))
        f.close()

        # Moves the SED, Lucy, and Convergence files into run folder to save them
        subprocess.call(["mv "+ baseDir + "/sed_inc042.dat " + runFolder, '/'], shell=True)
        # TODO: write code to move lucy file (which one?)
        subprocess.call(["mv " + baseDir + "/convergence_lucy.dat " + runFolder, '/'], shell=True)

        # Unnecessary, but prints completed message
        completeStr = "Run " + num2 + " Complete"
        decor = "%"*len(completeStr)
        subprocess.call(["cd ..; echo " + decor, '/'], shell=True)
        subprocess.call(["echo  Run " + num2 + " Complete", '/'], shell=True)
        subprocess.call(["cd ..; echo " + decor, '/'], shell=True)

        count2+=1
        return chi
    
    def converged(curPop, fit):
        for chi in fit:
            if chi <= 150000: # TODO: CHANGE TO REASONABLE VALUE
                return True
        return False

    subprocess.call(['cd ' + baseDir, '/'], shell=True)
    subprocess.call(['mkdir gen' + str(count) + '; cd ' + baseDir + '/gen' + str(count), '/'], shell=True)
    N,K = bounds.shape[0]*popSize, bounds.shape[0]
    x = np.random.rand(N, K) # initial (normed) population array with random values
    bmin, brange = bounds[:,0], np.diff(bounds.T, axis = 0)
    fx = np.array([objective_fn(xi) for xi in x*brange+bmin]) # Fit metrics: the chi square value for each population member
    indices = np.arange(N)
    count+=1

    while not converged(x, fx):
        # Creates folder for the new generation
        subprocess.call(['cd ' + baseDir, '/'], shell=True)
        subprocess.call(['mkdir gen' + str(count) + '; cd ' + baseDir + '/gen' + str(count), '/'], shell=True)

        if type(mutation) == tuple:
            m = np.random.uniform(*mutation) # If want m to be random multiple value each generation
        else:
            m = mutation # If want m to be constant value

        xtrial = np.zeros_like(x) # trial vector full of zeros
        j = np.argmin(fx) # index of best member
        # Creates trial population, consisting of mutated and past vectors
        for i in indices:
            k,l = np.random.choice(indices[np.isin(indices, [i,j], invert=True)], 2) # Chooses 2 random vectors that are not xbest or xi
            xmi = np.clip(x[j] + m*(x[k]-x[l]),0,1) # Creates mutated xi vector: xbest + mutant vector
            xtrial[i] = np.where(np.random.rand(K) < P, xmi, x[i]) # Probability that value will be replaced by xmi is 0.7 else = x[i]

        fxtrial = np.array([objective_fn(xi) for xi in xtrial*brange+bmin]) 
        improved = fxtrial < fx # Array of booleans indicating which trial members were improvements
        x[improved], fx[improved] = xtrial[improved], fxtrial[improved] # Replaces values in population with improved ones
        y = x[np.argmin(fx)]*brange+bmin # Gets the vector from x with lowest chi value, mult by range and added to min

        # Code to save the population of x as a csv file
        F = open(baseDir + "/gen" + str(count) + "/result" + str(count) + ".dat", "w")
        F.write(",".join(varNames)+",ChiValue\n")
        for member in x*brange+bmin:
            index2 = np.where(x*brange+bmin == member)[0][0]
            for var in member:
                F.write(str(var)+",")
            F.write(str(fx[index2]))
            F.write("\n")
        F.close()

        count+=1
        # TODO: make a break case for if the program gets stuck 
        if count == 100: #another option if fx < pastfx +1 and fx > pastfx - 1: return -> if fx is not changing
            return varNames, y, np.min(fx)

    return varNames, y, np.min(fx) # Returns variable names, vector with lowest chi value, and lowest chi value

def findChi(modelPath, dataPath):

    modelFile = open(modelPath, 'r')
    modelText = modelFile.read()
    modelLines = modelText.splitlines()

    dataFile = open(dataPath, "r")
    dataText = dataFile.read()
    dataLines = dataText.splitlines()

    modelDataLines = modelLines[1:]
    dataLines = dataLines[3:]

    modelLam = []
    modelFlux = [] 

    dataLam = []
    dataFlux = []
    error = []


    def getLine(point1, point2):
        return (point1, (point2[1]-point1[1])/(point2[0]-point1[0]))

    def findIntercept(modelPoint, line):
        x = modelPoint[0]
        y = line[1]*(x-line[0][0]) + line[0][1]
        return (x, y)

    for i in range(len(modelDataLines)): # intentionally discarding the second and third columns because flux is 0
        valueslist2 = modelDataLines[i].split("     ")
        modelLam.append(float(valueslist2[1]))
        modelFlux.append(float(valueslist2[2]))

    for i in range(len(dataLines)):
        valueslist = dataLines[i].split(" ")
        if valueslist[3] != 'nan' and float(valueslist[3]) != 0 and float(valueslist[0])*10**6 != 4.35:
            dataLam.append(float(valueslist[0])*10**6)
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


    count = 0
    for point in modelTuples:
        for i in range(len(listOfRanges)):
            valuerange = listOfRanges[i]
            if valuerange[0] < point[0] and valuerange[1] >= point[0]:
                if i < 14: # If the point lies in the nearIR spectrum
                    dictOfBins["nearIr"][valuerange] += [(point, valuerange[2])] #point and index
                elif 14 <= i and i < 25: 
                    dictOfBins["midIr"][valuerange] += [(point, valuerange[2])]
                elif 25 <= i and i < 31:
                    dictOfBins["farIr"][valuerange] += [(point, valuerange[2])]
                else:
                    dictOfBins["micro"][valuerange] += [(point, valuerange[2])]

    nearIrChi = 0
    midIrChi = 0
    farIrChi = 0
    microChi = 0

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
                if irBin == "nearIr":
                    nearIrChi += d_chi
                elif irBin == "midIr":
                    midIrChi += d_chi
                elif irBin == "farIr":
                    farIrChi += d_chi
                else:
                    microChi += d_chi

    nearIrChi = (nearIrChi * len(listOfRanges)) / len(listOfRanges[:14])
    midIrChi = (midIrChi * len(listOfRanges)) / len(listOfRanges[14:25])
    farIrChi = (farIrChi * len(listOfRanges)) / len(listOfRanges[25:31])
    microChi = (microChi * len(listOfRanges)) / len(listOfRanges[31:])
    totalChi = nearIrChi + midIrChi + farIrChi + microChi

    return totalChi


def main():
    result = differential_evolution(False)
    print(result)

if __name__ == '__main__':
    main()