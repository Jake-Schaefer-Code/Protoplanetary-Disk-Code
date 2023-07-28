import numpy as np
import subprocess
import os
import ChiSq
import vtuPlotter as vp
import time
import sys

count, count2 = 0, 1

# baseDir = "/Users/schaeferj/models" # Base Directory
# torusDir = "/Users/schaeferj/torus/bin/torus.openmp"
baseDir = "/home/schaeferj/models"
torusDir = "/home/schaeferj/torus/bin/torus.openmp"

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


# Objective function used to measure convergence to best vector
def objective_fn(params):
    global count, count2, torusDir, baseDir, bounds, varNames
    num2 = str(count2)
    
    # Creates new directory that will contain data from the current run
    runFolder = baseDir + "/gen" + str(count) + "/run" + num2
    os.chdir(runFolder)
    subprocess.call(['mkdir ' + runFolder, '/'], shell=True)

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
        if varName in varNames: line = replaceValue(line, 1, params[varNames.index(varName)])
        outputLines += [line]
        lineDict[varName] = line

    # Values that other Parameters depend on
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
            if modNum < 5:
                rPrev = float(lineDict["rinnermod" + str(modNum)][1])
                rCur = float(lineDict["rinnermod" + str(modNum + 1)][1])
                
        elif "settleheight" in varName:
            newVal = 0.7*hPrev if varName[-1] == "1" else 0.1*hPrev
            line = replaceValue(line, 1, str(newVal))

        # All alphas and betas should be the same
        elif "alphamod" in varName: line = replaceValue(line, 1, str(alphamod))
        elif "betamod" in varName: line = replaceValue(line, 1, str(betamod))
        elif "settlebeta" in varName: line = replaceValue(line, 1, str(betamod))
        
        # Rewrites the line
        outputLine = ""
        for item in line: outputLine += str(item) + ' '
        newParams.write(outputLine + '\n' )
    newParams.close()

    # Runs Torus and waits
    os.system("echo $'\n'Run " + num2 + " Started$'\n'")
    os.chdir(runFolder)
    os.system("sh " + baseDir + "/execute.sh")
    
    # Finds Chi Square and writes it in a file
    # This try-except loop should attempt to re-run torus if torus is killed 9
    try: 
        chi = ChiSq.findChi(runFolder + '/sed_inc042.dat', baseDir + '/mwc275_phot_cleaned_0.dat', count2)
        completeStr = 'Run ' + num2 + ' Complete, Chi Value: ' + str(chi)
    except:
        print("Run failed at " + time.ctime(time.time()) + " Trying again")
        os.system("sh /home/schaeferj/Desktop/execute.sh")
    
    # If torus is killed again, it will set the chi squared to infinity and not consider
    # these parameters
    try:
        chi = ChiSq.findChi(runFolder + '/sed_inc042.dat', baseDir + '/mwc275_phot_cleaned_0.dat', count2)
        completeStr = 'Run ' + num2 + ' Complete, Chi Value: ' + str(chi)
    except:
        chi = float('inf')
        print("Run failed again at " + time.ctime(time.time()))
        completeStr = 'Run ' + num2 + ' Failed. No chi value.'

    f = open(runFolder + '/chi' + num2 + '.dat', 'w')
    f.write(str(chi))
    f.close()

    total_dir_list = os.listdir(runFolder)
    lucy_list = []
    for file in total_dir_list:
        # Torus produces some lucy.dat files and other .vtu files, 
        # so this pulls out the lucy .vtu files
        if str(file)[:4] == 'lucy' and str(file)[-4:] == '.vtu': lucy_list.append(file)

        # Removes all lucy*.dat files
        if str(file)[:4] == 'lucy' and str(file)[-4:] == '.dat': os.remove(file)
    
    maxLucy, maxFile = 0, None
    for file in lucy_list:
        lucyNum = int(str(file.split('_')[1])[:-4]) # Pulls out number between lucy_ and .vtu
        # Gets latest lucy iteration
        if lucyNum > maxLucy: maxLucy, maxFile = lucyNum, file

    # Only plot vtu if there is a lucy file
    if maxFile != None: vp.bigPlot(maxFile, runFolder)

    # Moves the SED, Convergence, Lucy, and plotted vtu files into run folder to save them
    subprocess.call(["rm " + runFolder + "lucy*.dat", '/'], shell=True)
    os.chdir(baseDir)

    # Unnecessary, but prints completed message
    decor = "%"*len(completeStr)
    os.system("echo " + decor + "$'\n'" + completeStr + "$'\n'" + decor)
    os.chdir(baseDir)

    count2+=1
    return chi

# Code to continue running the program from the most recent generation and run if it was killed
# Takes the most recent parameter population and fit metric array as arguments
def restart(population, fx):
    global count, count2, torusDir, baseDir, varNames
    genDir = baseDir + "/gen" + str(count)
    pastRuns = os.listdir(genDir)
    numRuns = 0

    # Goes through each run in the current generation
    for i in range(len(pastRuns)):
        runDir = "/run" + str(i + 1)
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

        files = os.listdir(genDir + "/run" + str(i + 1))
        chiVal = float('inf')
        for file in files:
            # Reading the chi file and getting the chi value for the current run
            if "chi" in str(file):
                chiFile = open(genDir + "/run" + str(i + 1) + '/' + str(file), "r").read()
                chiVal = float(chiFile.splitlines()[0])

        # Adds the chi value for the current population member
        fx[i] = chiVal
        print(runDir)
        print(population[i], fx[i])
        os.chdir(genDir)
        numRuns += 1

    return numRuns


# Code for running the actual DE
# Returns variable names, vector with lowest chi value, and lowest chi value
def differential_evolution(converged, restarting, mutation = (0.5,1.0), P = 0.7, popSize = 10, genNum = 0):
    global count, count2, baseDir, bounds, varNames

    os.chdir(baseDir)
    subprocess.call(['mkdir gen' + str(count), '/'], shell=True)
    os.chdir(baseDir + '/gen' + str(count))
    N,K = bounds.shape[0]*popSize, bounds.shape[0]
    x = np.random.rand(N, K) # initial (normed) population array with random values
    bmin, brange = bounds[:,0], np.diff(bounds.T, axis = 0)
    indices = np.arange(N)
    fx = np.full(N, float('inf'))


    if restarting:
        x = x*brange + bmin
        restarting = True
        count += genNum
        count2 += restart(x, fx)
        x = (x - bmin)/brange
        print(np.shape(fx[count2-1:]))
        fx[count2-1:N+1] = np.array([objective_fn(xi) for xi in (x*brange+bmin)[count2-1:N+1]]) # TODO: something weird about this... fix later
        # TODO: got cannot cast shape (0,) to shape (6,) or vice versa error
    elif restarting == False:
        fx = np.array([objective_fn(xi) for xi in x*brange+bmin])
    

    # For using an array of known best values to start:
    # Can use this instead of random if program restarted
    """
    count+=1
    fx = np.full_like(x, float('inf')) # Sets a temp array full of max values for obj fn
    input = np.array([2.3966,1.0823,0.01406]) # Put desired input array
    xtrial = np.zeros_like(x)
    best = (input - bmin)/brange 
    print(input, best)
    for i in indices:
        k,l = np.random.choice(indices[np.isin(indices, [i], invert=True)], 2)
        xmi = np.clip(best + m*(x[k]-x[l]),0,1)
        print(xmi)
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

        # If want m to be random multiple value each generation or if want m to be constant value
        m = np.random.uniform(*mutation) if type(mutation) == tuple else mutation

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
        best = x[np.argmin(fx)]*brange+bmin # Gets the vector from x with lowest chi value, mult by range and added to min
		
        # Code to save the population of x as a csv file
        csv = open(baseDir + "/result" + str(count) + ".dat", "w")
        csv.write(",".join(varNames)+",ChiValue\n")
        for member in x*brange+bmin:
            index2 = np.where(x*brange+bmin == member)[0][0]
            for var in member: csv.write(str(var)+",")
            csv.write(str(fx[index2]))
            csv.write("\n")
        csv.close()

        count+=1
        
        # Break case for if program gets stuck
        if count == 30: #another option if fx < pastfx +1 and fx > pastfx - 1: return -> if fx is not changing
            return varNames, best, np.min(fx)

    return varNames, best, np.min(fx)

def main():
    restarting = bool(sys.argv[1])
    genNum = int(sys.argv[2])
    result = differential_evolution(False, restarting, (0.5,1.0), 0.7, 10, genNum)
    print(result)

if __name__ == '__main__':
    main()