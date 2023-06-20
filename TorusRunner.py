import sys
import subprocess
import pickle

def main():
    count = 0
    #create new parameters file
    subprocess.call(['mkdir run' + str(count), '/'], shell=True)
    subprocess.call(['cd run' + str(count), '/'], shell=True)
    subprocess.call(["~/torus/bin/torus.openmp ~/models/modParameters.dat > output.txt &", '/'], shell=True)
    
    #at the end of the while loop

    subprocess.call(["cd ..", '/'], shell=True)
    
    
    
    



    
    #subprocess.check_output(['ssh schaeferj@jtasson62708.physics.carleton.edu'])
    #sys.stdout.write("ssh schaeferj@jtasson62708.physics.carleton.edu"+"\n")

if __name__ == '__main__':
    main()