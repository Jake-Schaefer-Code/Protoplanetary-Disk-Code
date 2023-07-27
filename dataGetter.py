import numpy as np
import os
import sys

baseDir = "/Users/schaeferj/models/"
varNames = ["alphamod1", "betamod1", "grainfrac1", "mdisc1", "hInit"]

chisq = np.array([588.272,5064.937])
alphamod1 = np.array([2.133,2.795])
betamod1 = np.array([1.27,1.708])
grainfrac1 = np.array([0.01011,0.00513])
mdisc1 = np.array([0.02259,0.00591])
hInit = np.array([17.81,16.65])

data = [alphamod1, betamod1, grainfrac1, mdisc1, hInit, chisq]

def main():
    numGens = int(sys.argv[1])
    for i in range(numGens):
        #os.chdir(baseDir + "gen" + str(i))
        genDir = baseDir + "gen" + str(i)
        pastRuns = os.listdir(genDir)
        for i in range(len(pastRuns)):
            os.chdir(genDir + "/run" + str(i + 1))
            pastParams = open(genDir + "/run" + str(i + 1) + "/modParameters.dat", "r").read()
            lines = pastParams.splitlines()
            for line in lines:
                line = line.split(' ')
                varName = line[0]
                if varName in varNames:
                    index = varNames.index(varName)
                    np.insert(data[index], float(line[1]))
                if varName == "heightmod1":
                    hmod1 = float(line[1])
                if varName == "rinnermod1":
                    rmod1 = float(line[1])
                if varName == "betamod1":
                    bmod1 = float(line[1])
            if "hInit" in varNames:
                index = varNames.index("hInit")
                np.insert(data[index], ((100 * (hmod1 ** (1 / bmod1))) / rmod1) ** bmod1)
            files = os.listdir(genDir + "/run" + str(i + 1))
            chiVal = float('inf')
            for file in files:
                if "chi" in str(file):
                    chiVal = open(genDir + "/run" + str(i + 1) + '/' + str(file), "r").read()
                    chiVal = chiVal.splitlines()
                    chiVal = float(chiVal[0])
            np.insert(data[5], chiVal)
            os.chdir(genDir)
    for i in range(len(data)):
        print(data[i])


if __name__ == '__main__':
    main()

