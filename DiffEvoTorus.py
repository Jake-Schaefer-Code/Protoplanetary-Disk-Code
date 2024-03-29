import numpy as np
import subprocess
import os
import pyvista as pv
import matplotlib.pyplot as plt
import sys
import time

count, count2 = 0, 1
#baseDir = "/Users/schaeferj/models" # Base Directory
#torusDir = "/Users/schaeferj/torus/bin/torus.openmp"
baseDir = "/home/schaeferj/models"
torusDir = "/home/schaeferj/torus/bin/torus.openmp"

def differential_evolution(converged, restarting, mutation = (0.5,1.0), P = 0.7, popSize = 10, genNum = 0):
    global count, count2, baseDir

    # Each entry bounds[i,:] = upper, lower bounds of i
    bounds = np.array([[1.5, 3.0], [1.0, 2.0], [0.00333, 0.0133], [0.001, 0.05], [5.0, 20.0]])

    # Variable names corresponding to bound indices
    varNames = ["alphamod1", "betamod1", "grainfrac1", "mdisc", "hInit"]
    
    # Code to update value in parameters file
    def replaceValue(line, index, newVal):
        first = line[:index]
        second = line[index+1:]
        return first + [newVal] + second
    
    # Checks if objective function value is low enough to stop
    def converged(fit):
        for chi in fit:
            if chi <= 10:
                return True
        return False

    def check(population):
        # if value less than, reject value
        # if within bounds of what we expect
        for member in population:
            pass
        return

    def objective_fn(params):
        global count, count2, torusDir, baseDir
        num2 = str(count2)
        # Creates new directory that will contain data from the current run
        runFolder = baseDir + "/gen" + str(count) + "/run" + num2
        os.chdir(baseDir)
        subprocess.call(['mkdir ' + runFolder + '; cd ' + runFolder, '/'], shell=True)

        # Opens base parameters file
        baseParams = open(baseDir + '/modParameters.dat', 'r').read()
        lines = baseParams.splitlines()
        lineDict, outputLines = {}, []

        # Creates new parameters file
        newParams = open(runFolder + '/modParameters.dat', 'w')

        # First updates the variables being iterated
        for line in lines:
            line = line.split(' ')
            varName = line[0]
            if varName in varNames:
                index = varNames.index(varName)
                newVal = params[index]
                line = replaceValue(line, 1, newVal)
            outputLines += [line]
            lineDict[varName] = line
            
        rPrev = 100.0
        # hPrev is not an actual paraneter in the file, but it is the height used
        # to initialize heightmod1
        hPrev = float(params[varNames.index("hInit")])
        rCur = float(lineDict["rinnermod1"][1])
        betamod = float(lineDict["betamod1"][1])
        alphamod = float(lineDict["alphamod1"][1])

        # Edits parameters dependent on each other
        for line in outputLines:
            varName = line[0]
            if "heightmod" in varName:
                newVal = hPrev * ((rCur/rPrev) ** betamod)
                line = replaceValue(line, 1, str(newVal))
                hPrev = newVal
                modNum = int(varName[-1])
                #print("heightmod", modNum, newVal)
                if modNum < 5:
                    rPrev = float(lineDict["rinnermod" + str(modNum)][1])
                    rCur = float(lineDict["rinnermod" + str(modNum + 1)][1])
            elif "alphamod" in varName:
                newVal = alphamod
                line = replaceValue(line, 1, str(newVal))
            elif "betamod" in varName:
                newVal = betamod
                line = replaceValue(line, 1, str(newVal))
            elif "settlebeta" in varName:
                newVal = betamod
                line = replaceValue(line, 1, str(newVal))
            elif "settleheight" in varName:
                if varName[-1] == "1":
                    newVal = 0.7*hPrev
                else:
                    newVal = 0.1*hPrev
                line = replaceValue(line, 1, str(newVal))

            outputLine = ""
            for item in line:
                outputLine += str(item) + ' '
            newParams.write(outputLine + '\n' )
        newParams.close()
        print("cur params:", params)

        # Runs Torus and waits
        os.system("echo $'\n'Run " + num2 + " Started$'\n'")
        os.chdir(runFolder)
        os.system("sh /home/schaeferj/Desktop/execute.sh")
        
        # Finds Chi Square and writes it in a file
        # This try-except loop should attempt to rerun torus if torus is killed 9
        """try: 
            sed = runFolder + '/sed_inc042.dat'
            chi = findChi(sed, baseDir + '/mwc275_phot_cleaned_0.dat')
            completeStr = 'Run ' + num2 + ' Complete, Chi Value: ' + str(chi)
        except IOError:
            print("Run failed at " + time.ctime(time.time()) + " Trying again")
            os.system("sh /home/schaeferj/Desktop/execute.sh")

        # If torus is killed again, it will set the chi squared to infinity and not consider
        # thse parameters
        try:
            sed = runFolder + '/sed_inc042.dat'
            chi = findChi(sed, baseDir + '/mwc275_phot_cleaned_0.dat')
            completeStr = 'Run ' + num2 + ' Complete, Chi Value: ' + str(chi)
        except IOError:
            chi = float('inf')
            print("Run failed again at " + time.ctime(time.time()))
            completeStr = 'Run ' + num2 + ' Failed. No chi value.'"""

        sed = runFolder + '/sed_inc042.dat'
        chi = findChi(sed, baseDir + '/mwc275_phot_cleaned_0.dat')
        completeStr = 'Run ' + num2 + ' Complete, Chi Value: ' + str(chi)
        
        f = open(runFolder + '/chi' + num2 + '.dat', 'w')
        f.write(str(chi))
        f.close()


        total_dir_list = os.listdir(runFolder)
        lucy_list = []
        for file in total_dir_list:
            # Torus produces some lucy.dat files and other .vtu files, 
            # so this pulls out the lucy .vtu files
            if str(file)[:4] == 'lucy' and str(file)[-4:] == '.vtu': 
                lucy_list.append(file)
            
            # Removes all lucy*.dat files
            if str(file)[:4] == 'lucy' and str(file)[-4:] == '.dat':
                os.remove(file)
        
        maxLucy, maxFile = 0, None
        for file in lucy_list:
            lucyNum = int(str(file.split('_')[1])[:-4]) # Pulls out number between lucy_ and .vtu
            if lucyNum > maxLucy: # Gets latest lucy iteration
                maxLucy = lucyNum
                maxFile = file

        # Only plot if there is a lucy file
        if maxFile != None: 
            bigPlot(maxFile, runFolder)

        # Moves the SED, Convergence, Lucy, and plotted vtu files into run folder to save them
        subprocess.call(["rm " + runFolder + "lucy*.dat", '/'], shell=True)

        # Unnecessary, but prints completed message
        decor = "%"*len(completeStr)
        os.system("echo " + decor + "$'\n'" + completeStr + "$'\n'" + decor)
        os.chdir(baseDir)

        count2+=1
        return chi

    def diffevo(x, fx):
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
        return

    def restart(population, fx):
        global count, count2, torusDir, baseDir
        #genDir = baseDir + "/gen" + str(count)
        #pastRuns = os.listdir(genDir)
        #numRuns = count * 10 * len(varNames)
        


        numRuns = 0
        # For each previous generation
        for i in range(count + 1):
            genDir = baseDir + "/gen" + str(i)
            pastRuns = os.listdir(genDir)

            # For each run in the previous generation
            for j in range(len(pastRuns)):
                #print("restart" + str(count) + str(i) + str(j))
                runDir = "/run" + str((10 * len(varNames) * i) + j + 1)
                params = population[i]
                os.chdir(genDir + runDir)
                runParams = open(genDir + runDir + "/modParameters.dat", "r").read()
                lines = runParams.splitlines()

                for line in lines:
                    line = line.split(' ')
                    varName = line[0]
                    if varName in varNames: params[varNames.index(varName)] = float(line[1])
                    if varName == "heightmod1": hmod1 = float(line[1]) 
                    elif varName == "rinnermod1": rmod1 = float(line[1])
                    elif varName == "betamod1": bmod1 = float(line[1])
                if "hInit" in varNames:
                    params[varNames.index("hInit")] = ((100 * (hmod1 ** (1 / bmod1))) / rmod1) ** bmod1

                files = os.listdir(genDir + runDir)
                chiVal = float('inf')
                for file in files:
                    # Reading the chi file and getting the chi value for the current run
                    if "chi" in str(file):
                        chiFile = open(genDir + runDir + '/' + str(file), "r").read()
                        chiVal = float(chiFile.splitlines()[0])
                
                print("gen num: ", i, "run num: ", j, population[i], params) 
                fx[j] = chiVal
                os.chdir(genDir)
                numRuns += 1 # TODO: need to fix this so that it doesnt count a run without a chi value as a complete run
            #print(population)


        """for i in range(len(pastRuns)):
            runDir = "/run" + str(numRuns + 1)
            params = population[i]
            os.chdir(genDir + runDir)
            runParams = open(genDir + runDir + "/modParameters.dat", "r").read()
            lines = runParams.splitlines()

            # Setting the params of the current population member to those used in the respective run
            for line in lines:
                line = line.split(' ')
                varName = line[0]
                if varName in varNames: params[varNames.index(varName)] = float(line[1])
                if varName == "heightmod1": hmod1 = float(line[1]) 
                elif varName == "rinnermod1": rmod1 = float(line[1])
                elif varName == "betamod1": bmod1 = float(line[1])
            if "hInit" in varNames:
                params[varNames.index("hInit")] = ((100 * (hmod1 ** (1 / bmod1))) / rmod1) ** bmod1

            files = os.listdir(genDir + runDir)
            chiVal = float('inf')
            for file in files:
                # Reading the chi file and getting the chi value for the current run
                if "chi" in str(file):
                    chiFile = open(genDir + runDir + '/' + str(file), "r").read()
                    chiVal = float(chiFile.splitlines()[0])

            # Adds the chi value for the current population member
            fx[i] = chiVal
            #print(population[i], params)
            #print("run" + str(i) + " chi")
            #print(fx[i])
            os.chdir(genDir)
            numRuns += 1"""
        

        return numRuns
        

    
    os.chdir(baseDir)
    subprocess.call(['mkdir gen' + str(count), '/'], shell=True)
    os.chdir(baseDir + '/gen' + str(count))
    N,K = bounds.shape[0]*popSize, bounds.shape[0]
    x = np.random.rand(N, K) # initial (normed) population array with random values
    bmin, brange = bounds[:,0], np.diff(bounds.T, axis = 0)
    indices = np.arange(N)
    fx = np.full(N, float('inf'))
    fxtrial = np.full(N, float('inf'))
    
    if restarting:
        for i in range(len(x)):
            x[i] = x[i]*brange + bmin
        restarting = True
        count += genNum
        count2 += restart(x, fx)
        #print(count2)
        print("before constrain: ", x)
        for i in range(len(x)):
            x[i] = (x[i] - bmin)/brange
        print(x)


        if count >= 1:
            """x2 = np.random.rand(N, K)
            fx2 = np.full(N, float('inf'))
            prevBest = getPrevBest(x2, fx2)
            print("Best data set: chi: " + str(prevBest[1]) + ", " + varNames[0] + ": " + str(prevBest[0][0])
                  + ", " + varNames[1] + ": " + str(prevBest[0][1]) + ", " + varNames[2] + ": " + str(prevBest[0][2])
                  + ", " + varNames[3] + ": " + str(prevBest[0][3]) + ", " + varNames[4] + ": " + str(prevBest[0][4]))"""
            
            
            if type(mutation) == tuple:
                m = np.random.uniform(*mutation) # If want m to be random multiple value each generation
            else:
                m = mutation # If want m to be constant value

            j = np.argmin(fx) # index of best member
            print("best fx:", fx[j], "best params:", x[j])
            xtrial = np.zeros_like(x)

            for i in indices:
                k,l = np.random.choice(indices[np.isin(indices, [i,j], invert=True)], 2) # Chooses 2 random vectors that are not xbest or xi
                xmi = np.clip(x[j] + m*(x[k]-x[l]),0,1) # Creates mutated xi vector: xbest + mutant vector
                xtrial[i] = np.where(np.random.rand(K) < P, xmi, x[i]) # Probability that value will be replaced by xmi is 0.7 else = x[i]

            os.chdir(baseDir + "/gen" + str(count))
            fxtrial[(count2%50)-1:N+1] = np.array([objective_fn(xi) for xi in (xtrial*brange+bmin)[(count2%50)-1:N+1]])
            improved = fxtrial < fx # Array of booleans indicating which trial members were improvements
            x[improved], fx[improved] = xtrial[improved], fxtrial[improved]

        elif count < 1:
            fx[count2-1:N+1] = np.array([objective_fn(xi) for xi in (x*brange+bmin)[(count2%50)-1:N+1]])
        
        #print(np.shape(fx[count2-1:]))
        # TODO: something weird about this... fix later
        # TODO: got cannot cast shape (0,) to shape (6,) or vice versa error
    elif restarting == False:
        fx = np.array([objective_fn(xi) for xi in x*brange+bmin])
        

    # TODO: add code to remove lucy.dat

    # For using an array of known best values to start:
    # Can use this instead of random if program restarted
    """
    count+=1
    fx = np.full_like(x, float('inf')) # Sets a temp array full of max values for obj fn
    input = np.array([2.3966,1.0823,0.01406]) # Put desired input array
    xtrial = np.zeros_like(x)
    best = (input - bmin)/brange 
    for i in indices:
        k,l = np.random.choice(indices[np.isin(indices, [i], invert=True)], 2)
        xmi = np.clip(best + m*(x[k]-x[l]),0,1)
        xtrial[i] = np.where(np.random.rand(K) < P, xmi, x[i])
    fxtrial = np.array([objective_fn(xi) for xi in xtrial*brange+bmin]) 
    improved = fxtrial < fx # Array of booleans indicating which trial members were improvements
    x[improved], fx[improved] = xtrial[improved], fxtrial[improved]"""
    

    # Fit metrics: the chi square value for each population member
    count+=1

    while not converged(fx):
        # Creates folder for the new generation
        os.chdir(baseDir)
        subprocess.call(['mkdir gen' + str(count), '/'], shell=True)
        os.chdir(baseDir + '/gen' + str(count))

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
    global count2

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

    for i in range(len(names)): # Creating a dictionary of the data points based on author
        names[i] = names[i].split(":")[0]
        if pointDict.get(names[i]) == None:
            pointDict[names[i]] = [list(xyerrTuples[i])]
        else:
            pointDict[names[i]] += [list(xyerrTuples[i])]

    for tuple in modelTuples:
        modelPointDict['x'] += [tuple[0]]
        modelPointDict['y'] += [tuple[1]]

    for tuple in xyerrTuples:
        pointDict['x'] += [tuple[0]]
        pointDict['y'] += [tuple[1]]

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

    #count = 0
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
                if irBin == "nearIr":
                    nearIrChi += d_chi
                elif irBin == "midIr":
                    midIrChi += d_chi
                elif irBin == "farIr":
                    farIrChi += d_chi
                else:
                    microChi += d_chi

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

def plot(filename, variable, directory = '', plotsize = 'full'):
    if directory != '':
        filename = str(directory) + '/' + str(filename)

    variable = str(variable)
    grid = pv.read(filename) # Read lucy file in as a pyvista mesh
    valArray = grid[variable] # The lucy file is basically a bunch of vtk files stacked on top
                              # of each other, which is why just plotting the lucy file either
                              # doesn't work or returns a blank square. This lets us work with 
                              # only one of the variables (VisIt has all the variable names, 
                              # working on getting them to display here)
    minIndexes = []
    for i in range(len(valArray)): # convert to log values
        value = valArray[i] # EAR
        if value > 0: # if value won't throw a log error
            valArray[i] = np.log10(value) # EAR
        else: # if the value is too small to log, store the index 
            minIndexes.append(i)

    minVal = min(valArray) # get the minimum of the logged values
    for i in minIndexes: # go through the stored indicies and set all those values to the minimum
        valArray[i] = minVal # EAR

    centers = grid.cell_centers() # plot the center points for the contour
    centerPoints = np.asarray(centers.GetPoints().GetData())
    scale = 6.685 * (10 ** -4)
    centerX = centerPoints[:,0] * scale
    centerY = centerPoints[:,1] * scale

    centerX = centerX.transpose() # they come out as column vectors
    centerY = centerY.transpose()
    
    u = np.array([np.asarray(valArray)])
    u = u.transpose()
    centerU = u[:,0]

    if plotsize != 'full': # zoom in on the star
        xMin = 0
        xMax = plotsize
        yMin = -1 * int(plotsize/2) # need to center the y axis
        yMax = int(plotsize/2)
        size = ([xMin, xMax, yMin, yMax])
    else:
        size = ([0, max(centerX), min(centerY), max(centerY)]) # otherwise show all the data
    return((centerX, centerY, centerU, size))

def bigPlot(filename, directory = '', min = 10, mid = 100, 
            variableNames = ('temperature', 'dust1', 'dust2'), levels = 100):
    fig = plt.figure(figsize=(18, 4 * len(variableNames)))
    subfigs = fig.subfigures(len(variableNames),1) # one subfig for each variable
    if len(variableNames) == 1: # if only one variable, makes a single subfig instead of a list
        subfigs = [subfigs]

    for i in range(len(subfigs)):

        variable = variableNames[i]
        (ax1, ax2, ax3) = subfigs[i].subplots(1, 3) #len(variableNames)
        plt.set_cmap('viridis')
        if variable == 'temperature': # some colormaps I like. Not necessary and other variables will just be in the default colormap.
            plt.set_cmap('inferno')
        if variable == 'dust1':
            plt.set_cmap('Blues')
        if variable == 'dust2':
            plt.set_cmap('Greens')

        data1 = plot(filename, variable, directory,  plotsize=min)  # these three blocks select the data for each plot
        x1, y1, u1 = data1[0], data1[1], data1[2]
        size1 = data1[3]
        ax1.tricontourf(x1, y1, u1, levels = levels)
        ax1.axis(size1)

        data2 = plot(filename, variable, directory,  plotsize=mid)
        x2, y2, u2 = data2[0], data2[1], data2[2]
        size2 = data2[3]
        ax2.tricontourf(x2, y2, u2, levels = levels)
        ax2.axis(size2)

        data3 = plot(filename, variable, directory)
        x3, y3, u3 = data3[0], data3[1], data3[2]
        size3 = data3[3]
        im = ax3.tricontourf(x3, y3, u3, levels = levels)
        ax3.axis(size3)

        cbar = fig.colorbar(im, ax = [ax1, ax2, ax3]) # add colorbar to each figure
        cbar.set_label(variable, fontsize = 'x-large')

        tickLocs = cbar.get_ticks()
        newLabels = []
        for tick in tickLocs:
            actual = 10 ** tick
            rounded = '%s' % float('%.3g' % actual) # rounding the tick labels to 3 sig figs
            newLabels.append(str(rounded))
        cbar.set_ticks(tickLocs, labels = newLabels)
        #subfigs[i].suptitle(variable)
        
        subfigs[i].supxlabel('Radial distance (AU)',  fontsize = 'x-large', y=0)
        subfigs[i].supylabel('Polar distance (AU)',  fontsize = 'x-large', x = 0.09)
    plt.subplots_adjust(bottom=0.15, right = 0.77)
    plt.savefig('lucyvtu.png')

    """if directory == '':
        plt.savefig(filename.split('.')[0] + '.png')
    else:
        plt.savefig('lucyvtu.png') # adjust for personal preference"""

    plt.close() # EAR

def main():
    restarting = bool(sys.argv[1])
    genNum = int(sys.argv[2])
    result = differential_evolution(False, restarting, (0.5,1.0), 0.7, 10, genNum)
    print(result)

if __name__ == '__main__':
    main()
