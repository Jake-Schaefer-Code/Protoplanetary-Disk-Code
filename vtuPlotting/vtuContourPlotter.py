def plot(directory, filename, variable):
    import pyvista as pv
    import math
    import matplotlib.pyplot as plt
    import numpy as np
    import matplotlib.tri as tri

    #filename = 'lucy_000004004.vtu'
    #variable = 'temperature'
    filename = str(directory) + str(filename)
    variable = str(variable)

    grid = pv.read(filename) # read lucy file in as a pyvista mesh

    varname = variable + ' (log scale)'
    grid[varname] = pv.plotting.normalize(grid[variable]) # the lucy file is basically a bunch of vtk files stacked on top
                                                                # of each other, which is why just plotting the lucy file either
                                                                # doesn't work or returns a blank square. This lets us work with 
                                                                # only one of the variables (VisIt has all the variable names, working
                                                                # on getting them to display here)

    valArray = grid[varname] # makes it easier to work with

    for i in range(len(valArray)): # convert to log values. Fix: sets the smallest values to a dummy number instead of dealing with them
        value = valArray.GetValue(i)
        if value > 0.0001:
            valArray.SetValue(i, math.log(value))
        else:
            valArray.SetValue(i,-9)

    pts = grid.points
    pts = np.asarray(pts)[:,:2]

    centers = grid.cell_centers()
    centerPoints = np.asarray(centers.GetPoints().GetData())

    x = pts[:,0]
    y = pts[:,1]

    centerX = centerPoints[:,0]
    centerY = centerPoints[:,1]

    u = np.array([np.asarray(valArray)])
    u = u.transpose()
    centerU = u[:,0].tolist()

    
    x= x.transpose()
    y = y.transpose()
    x = x.tolist()
    y = y.tolist()

    centerX = centerX.transpose()
    centerY = centerY.transpose()
    centerX.tolist()
    centerY.tolist()

    bigZ = np.repeat(u,4)
    
    fig, (ax1, ax2) = plt.subplots(1,2, figsize = (20,8))
    ax1.tricontourf(x,y,bigZ, levels = 30)
    ax2.tricontourf(centerX, centerY, centerU, levels=30)
    ax1.set_title('Using cell corners')
    ax2.set_title('Using cell centers')
    fig.suptitle(variable + ' contour plots for ' + filename)
    plt.savefig('contour.png')
    plt.show()


def main():
    import sys
    import os

    directory = str(sys.argv[1]) + '/'
    variable = str(sys.argv[2]) # command line argument

    total_dir_list = os.listdir(directory) # all files in directory
    lucy_list = []
    for file in total_dir_list:
        if str(file)[-4:] == '.vtu':
            lucy_list.append(file)
    
    maxLucy = 0
    maxFile = None

    for file in lucy_list:
        lucyNum = int(str(file.split('_')[1])[:-4]) # pulling out the number between lucy_ and .vtu
        if lucyNum > maxLucy:
            maxLucy = lucyNum
            maxFile = file
    
    if maxFile != None:
        plot(directory, maxFile, variable)

if __name__ == '__main__':
    main()