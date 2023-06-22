"""
A module to plot the lucy.vtu files produced by torus in matplotlib. Runnable from the command line: python3 vtuPlotter.py directory variable, where directory is
the name of the directory (must be within the working directory) containing the lucy files and variable is the desired variable to plot (e.g.
temperature, dust1, dust2). Also runnable as an imported module.

This module does NOT plot the actual cells of the lucy grid. Matplotlib requires that an irregular mesh can be mapped to a rectangular grid in order
to plot the actual mesh cells. Functions like pcolormesh require an instance of np.meshgrid, either directly in the code or in the background. However, 
the smallest lucy cells are very small (side lengths ~0.1) and the dimensions of the grid are on the order of hundreds of thousands. Finding all the cell coordinates
requires a significant amount of memory (I received memory requests of ~22 TB) and is not feasible for this module. 

This module plots the contours described by the cell values, which is much more efficient and results in a very similar plot. It currently plots both the contours
produced by the cell corners and those produced by the cell centers. The cell centers produce a smoother plot.


Requirements:
- vtuContourPlotter in the working directory
- the name of a directory containing lucy files within the working directory
    - if there are no lucy files, the program will not produce an image but should not crash
"""


def plot(filename, variable, directory = '', plotsize = 'full'):
    """
    Plots a lucy file.
    Params:
    directory: the directory containing the lucy file
    filename: the name of the lucy file
    variable: the variable to plot
    plotsize: the size of the plot. Integer or 'full'
    """

    import pyvista as pv
    import matplotlib.pyplot as plt
    import numpy as np

    #filename = 'lucy_000004004.vtu'
    #variable = 'temperature'
    if directory != '':
        filename = str(directory) + '/' + str(filename)


    variable = str(variable)

    grid = pv.read(filename) # read lucy file in as a pyvista mesh

    valArray = grid[variable] # the lucy file is basically a bunch of vtk files stacked on top
                                                                # of each other, which is why just plotting the lucy file either
                                                                # doesn't work or returns a blank square. This lets us work with 
                                                                # only one of the variables (VisIt has all the variable names, working
                                                                # on getting them to display here)


    minIndexes = []
    for i in range(len(valArray)): # convert to log values
        value = valArray.GetValue(i)
        if value > 0: # if value won't throw a log error
            valArray.SetValue(i, np.log10(value))
        else: # if the value is too small to log, store the index 
            minIndexes.append(i)

    minVal = min(valArray) # get the minimum of the logged values
    for i in minIndexes: # go through the stored indicies and set all those values to the minimum
        value = valArray.GetValue(i)
        valArray.SetValue(i, minVal)
    
    centers = grid.cell_centers() # plot the center points for the contour
    centerPoints = np.asarray(centers.GetPoints().GetData())
    centerX = centerPoints[:,0]
    centerY = centerPoints[:,1]

    centerX = centerX.transpose() # they come out as column vectors
    centerY = centerY.transpose()

    
    

    u = np.array([np.asarray(valArray)])
    u = u.transpose()
    centerU = u[:,0]

    ''' uncomment to plot the contours using the cell corners
    pts = grid.points
    pts = np.asarray(pts)[:,:2]
    x = pts[:,0]
    y = pts[:,1]

    x= x.transpose()
    y = y.transpose()
    x = x.tolist()
    y = y.tolist() 
    bigZ = np.repeat(u,4)

    plt.tricontourf(x,y,bigZ, levels = 30)
    plt.title('Using cell corners')
    plt.show()
    '''


    fig = plt.figure(figsize = (10,8))
    if plotsize != 'full': # optionally zoom in on the star
        xMin = 0
        xMax = plotsize
        yMin = -1 * int(plotsize/2)
        yMax = int(plotsize/2)
        plt.axis([xMin, xMax, yMin, yMax])
    plt.tricontourf(centerX, centerY, centerU, levels=100)
    plt.title(variable + ' contour plot for ' + filename)
    plt.set_cmap('inferno')
    plt.colorbar()
    if directory != '':
        plt.savefig(str(filename.split('/')[-2]) + '.' + variable + '.png')
    else:
        plt.savefig(variable + '.png')

def main():
    import sys
    import os

    directory = str(sys.argv[1])
    variable = str(sys.argv[2]) # command line argument
    if len(sys.argv) > 3:
        plotsize = int(sys.argv[3])
    else:
        plotsize = 'full'

    total_dir_list = os.listdir(directory) # all files in directory
    lucy_list = []
    for file in total_dir_list:
        if str(file)[:4] == 'lucy' and str(file)[-4:] == '.vtu': # there are some lucy.dat files and other .vtu files
            lucy_list.append(file)
    
    maxLucy = 0
    maxFile = None

    for file in lucy_list:
        lucyNum = int(str(file.split('_')[1])[:-4]) # pulling out the number between lucy_ and .vtu
        if lucyNum > maxLucy: # iterate to get the latest lucy file
            maxLucy = lucyNum
            maxFile = file
    
    if maxFile != None: # only plot if there is a lucy file
        plot(maxFile, variable, directory, plotsize)

if __name__ == '__main__':
    main()
