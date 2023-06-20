#from chi import *
import numpy as np
import subprocess


def differential_evolution(converged, mutation = (0.5,1.0), P = 0.7, popSize = 10):
    bounds = np.array([[7500, 10000], [0.5, 1.56], [0.001, 0.02], [0.01, 0.05]]) # each entry bounds[i,:] = upper, lower bounds
    varNames = ["teff1", "rinnermod1", "grainfrac1", "grainfrac2"]
    tmpBest = np.array([8600, 0.9, 0.012, 0.04])
    curBest = np.array([8750, 1.56, 0.005, 0.01])
    count = 0
    count2 = 0

    def objective_fn(params):
        #runs torus
        #returns chi square
        #call gabes code
        #open up a file, write the chi square, change in temperature, close

        chi = 0
        for i in range(len(params)):
            chi += ((params[i-1]-tmpBest[i-1])**2)/(tmpBest[i-1]**2)
        return chi
    
    def converged(curPop, fit):
        for chi in fit:
            if chi <= 0.01:
                return True
        return False


    N,K = bounds.shape[0]*popSize, bounds.shape[0]
    x = np.random.rand(N, K) # initial (normed) population array with random values
    bmin, brange = bounds[:,0], np.diff(bounds.T, axis = 0)
    fx = np.array([objective_fn(xi) for xi in x*brange+bmin]) # fit metrics
    indices = np.arange(N)


    while not converged(x, fx):
        if type(mutation) == tuple:
            m = np.random.uniform(*mutation)
        else:
            m = mutation

        xtrial = np.zeros_like(x) # trial vector full of zeros
        j = np.argmin(fx) # index of best member
        for i in indices:
            k,l = np.random.choice(indices[np.isin(indices, [i,j])], 2)
            xmi = np.clip(x[j] + m*(x[k]-x[l]),0,1) #xbest + mutant vector
            xtrial[i] = np.where(np.random.rand(K) < P, xmi, x[i]) # probability that value will be replaced by xmi is 0.7 else = x[i]
            fxtrial = np.array([objective_fn(xi) for xi in xtrial*brange+bmin])
            improved = fxtrial < fx # boolean array indicating which trial members were improvements
            x[improved], fx[improved] = xtrial[improved], fxtrial[improved]
    
        y = x[np.argmin(fx)]*brange+bmin
        #save x at the end of each generation as a csv files
        #pickle? the file - save array to file
        F = open("/Users/jakeschaefer/Desktop/ResultFolder/result"+str(count)+".dat", "w")
        F.write(",".join(varNames)+"\n")
        for member in x:
            for name in member:
                if name == member[-1]:
                    F.write(str(name))
                else:
                    F.write(str(name)+",")
                
            F.write("\n")
        
        F.close()
        count+=1
        if count == 100:
            return varNames, y, np.min(fx)
        print(str(count) + ": "+ str(np.min(fx)))
    return varNames, y, np.min(fx) #returns minimum value in x, mult by range and added to min, and the minimum chi square value

def main():
    result = differential_evolution(False)
    print(result)

if __name__ == '__main__':
    main()

'''must run torus for each change in vector'''
'''1. create population of vectors
2. for each member of the population:
create a mutation
create a trial vector
run torus with the trial vector and get chi square
if chi square is better, then replace member with trial vector'''