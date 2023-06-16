import sys
import chi
import csv
import os
#import sheetUpdater
import modelPlotter
import sheetAppender
directory = str(sys.argv[1])
sheetname = str(sys.argv[2])

dirpath = "/home/driscollg/models/" + directory + "/"
dir_list = os.listdir(dirpath)
for name in dir_list:
    if str(name)[:3] == "sed" and str(name).count("_") == 1:
        sedname = name


chiVal = chi.main("/home/driscollg/models/" + directory +  "/" + sedname)

outputpath = "/home/driscollg/models/results.csv"

body = [sheetname, chiVal]

with open(outputpath, "a") as f:
    writer = csv.writer(f)
    writer.writerow(body)
    f.close()

#sheetUpdater.main('results.csv')
sheetAppender.main(sheetname, str(chiVal))
modelPlotter.main("/home/driscollg/models/" + directory +  "/" + sedname)

