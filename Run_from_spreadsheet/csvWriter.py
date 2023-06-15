import sys
import chi
import csv
import os


directory = str(sys.argv[1])
sheetname = str(sys.argv[2])

dirpath = "/home/driscollg/models/" + directory
dir_list = os.listdir(dirpath)
for name in dirpath:
    if str(name)[:3] == "sed" and str(name).count("_") == 1:
        sedname = name


chiVal = chi.main("/home/driscollg/models/" + directory + sedname)

outputpath = "/home/driscollg/models/" + directory + "/" + sheetname + ".csv"

header = ['Model', 'chi squared']
body = [sheetname, chiVal]

with open(outputpath, "w", newline = '') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerow(body)
    f.close()
