import numpy as np
import os
import sys

baseDir = "/Users/schaeferj/models/"
varNames = ["alphamod1", "betamod1", "grainfrac1", "mdisc", "hInit"]

chisq = []
alphamod1 = []
betamod1 = []
grainfrac1 = []
mdisc = []
hInit = []

#data = [alphamod1, betamod1, grainfrac1, mdisc, hInit, chisq]
data = {"alphamod1":alphamod1, "betamod1":betamod1, "grainfrac1":grainfrac1, "mdisc":mdisc, "hInit":hInit, "chisq":chisq}


def main():
    numGens = int(sys.argv[1])
    for j in range(numGens):
        genDir = baseDir + "gen" + str(j)
        pastRuns = os.listdir(genDir)
        for i in range(len(pastRuns)):
            os.chdir(genDir + "/run" + str(i + 1))
            pastParams = open(genDir + "/run" + str(i + 1) + "/modParameters.dat", "r").read()
            lines = pastParams.splitlines()
            for line in lines:
                line = line.split(' ')
                varName = line[0]
                if varName in varNames:
                    #index = varNames.index(varName)
                    data[varName] += [float(line[1])]
                    #np.append(data[varName], float(line[1]))
                if varName == "heightmod1":
                    hmod1 = float(line[1])
                if varName == "rinnermod1":
                    rmod1 = float(line[1])
                if varName == "betamod1":
                    bmod1 = float(line[1])
            if "hInit" in varNames:
                #index = varNames.index("hInit")
                h = ((100 * (hmod1 ** (1 / bmod1))) / rmod1) ** bmod1
                data["hInit"] += [h]
                #np.append(data["hInit"], ((100 * (hmod1 ** (1 / bmod1))) / rmod1) ** bmod1)
            files = os.listdir(genDir + "/run" + str(i + 1))
            chiVal = float('inf')
            for file in files:
                if "chi" in str(file):
                    chiVal = open(genDir + "/run" + str(i + 1) + '/' + str(file), "r").read()
                    chiVal = chiVal.splitlines()
                    chiVal = float(chiVal[0])
            #np.append(data["chisq"], chiVal)
            data["chisq"] += [chiVal]
            os.chdir(genDir)
    
    f = open(baseDir + "runData.dat", "w")
    for key in data:
        f.write(key + ",")
        f.write(",".join(data[key])+",\n")
    f.close()


if __name__ == '__main__':
    main()

