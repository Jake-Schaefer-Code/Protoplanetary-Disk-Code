import subprocess
import numpy as np



def runTorus():
    def replaceValue(line, index, newVal):
        first = line[:index]
        second = line[index+1:]
        return first + [newVal] + second
    
    count2 = 0
    varNames = ["teff1", "rinnermod1", "grainfrac1", "grainfrac2"]
    tmpBest = np.array([8600, 0.9, 0.012, 0.04])

    subprocess.call(["cd /home/schaeferj/models; ls", '/'], shell=True)
    subprocess.call(['mkdir run' + str(count2) + '; cd /home/schaeferj/models/run' + str(count2), '/'], shell=True)
    
    
    originalParams = open("/home/schaeferj/models/modParameters.dat", "r").read()
    lines = originalParams.splitlines()
    f = open("/home/schaeferj/models/run" + str(count2) + "/modParameters" + str(count2) + ".dat", "w")
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

    output = subprocess.run(["/home/schaeferj/torus/bin/torus.openmp", "/home/schaeferj/models/modParameters.dat &"])
    print(output)
    subprocess.call(["echo I did not work", '/'], shell=True)
    print("not worked")


runTorus()
    




