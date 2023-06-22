"""
A module to plot the lucy.vtu files produced by torus in matplotlib. Runnable from the command line: python3 vtuPlotter.py directory variable, where directory is
the name of the directory (must be within the working directory) containing the lucy files and variable is the desired variable to plot (e.g.
temperature, dust1, dust2). 

This module does NOT plot the actual cells of the lucy grid. Matplotlib requires that an irregular mesh can be mapped to a rectangular grid in order
to plot the actual mesh cells. Functions like pcolormesh require an instance of np.meshgrid, either directly in the code or in the background. However, 
the smallest lucy cells are very small (side lengths ~0.1) and the dimensions of the grid are on the order of hundreds of thousands. Finding all the cell coordinates
requires a significant amount of memory (I received memory requests of ~22 TB) and is not feasible for this module. 

This module plots the contours described by the cell values, which is much more efficient and results in a very similar plot. It currently plots both the contours
produced by the cell corners and those produced by the cell centers. The cell centers produce a smoother plot.

Requirements:
- vtuPlotter in the working directory
- the name of a directory containing lucy files within the working directory
    - if there are no lucy files, the program will not produce an image but should not crash
"""


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

    minIndexes = []
    for i in range(len(valArray)): # convert to log values. Fix: sets the smallest values to a dummy number instead of dealing with them
        value = valArray.GetValue(i)

        if value > 0.0001:
            valArray.SetValue(i, math.log(value))
        else:
            minIndexes.append(i)

    minVal = min(valArray)
    for i in minIndexes:
        value = valArray.GetValue(i)
        valArray.SetValue(i, minVal)

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
    plt.savefig(str(filename.split('/')[-2]) + '.' + variable + '.png')


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
