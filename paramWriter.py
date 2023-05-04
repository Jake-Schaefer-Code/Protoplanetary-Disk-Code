
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

sheet_name = str(sys.argv[1])

sheet_id = "13k9iSe1oqnPqmU8Ks94cZMo9qkb1QggQ_9BuOZla8Xc"
sheet_url = f"https://docs.google.com/spreadsheets/d/"  + sheet_id + "/gviz/tq?tqx=out:csv&sheet=" + sheet_name

table = pd.read_csv(sheet_url)

fp = "/home/driscollg/models/modParameters.dat"
originalParams = open(fp, "r").read()

lines = originalParams.splitlines()

listOfVars = table["Parameter !stellar parameters"].values.tolist()

def replaceValue(line, index, newVal):
    first = line[:index]

    second = line[index+1:]

    return first + [newVal] + second

with open("/home/driscollg/models/modParametersNEW.dat", "w") as f:
    for line in lines:
        line = line.split(" ")
        varName = line[0]
        if varName in listOfVars:
            index = listOfVars.index(varName)
            row = table.loc[table["Parameter !stellar parameters"] == varName]
            newVal = row["Value "].tolist()
            newVal = str(newVal[0])
            line = replaceValue(line, index, newVal)

        outputLine = ""
        for item in line:
            outputLine += str(item) + " "
        f.write(outputLine + '\n' )
    f.close()
