import numpy as np
import subprocess
count = 0
count2 = 1
baseDir = "/Users/schaeferj/models" # Base Directory
torusDir = "/Users/schaeferj/torus/bin/torus.openmp"

def differential_evolution(converged, mutation = (0.5,1.0), P = 0.7, popSize = 10):
    bounds = np.array([[7500, 10000], [0.5, 1.56], [0.001, 0.02], [0.01, 0.05]]) # Each entry bounds[i,:] = upper, lower bounds of i
    varNames = ["teff1", "rinnermod1", "grainfrac1", "grainfrac2"] # Variable names corresponding to bound indices
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
        f = open(runFolder + '/modParameters' + num2 + '.dat', 'w') # New param file numbered to run
        for line in lines:
            line = line.split(' ')
            varName = line[0]
            if varName in varNames:
                index = varNames.index(varName)
                newVal = str(params[index])
                line = replaceValue(line, 1, newVal)
            outputLine = ""
            for item in line:
                outputLine += str(item) + ' '
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

def main():
    result = differential_evolution(False)
    print(result)

if __name__ == '__main__':
    main()