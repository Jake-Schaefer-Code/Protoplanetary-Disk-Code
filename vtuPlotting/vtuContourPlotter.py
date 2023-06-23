"""
A module to plot the lucy.vtu files produced by torus in matplotlib. Runnable from the command line: python3 vtuPlotter.py directory, where directory is
the name of the directory (must be within the working directory) containing the lucy files. Also runnable as an imported module.

This module does NOT plot the actual cells of the lucy grid. Matplotlib requires that an irregular mesh can be mapped to a rectangular grid in order
to plot the actual mesh cells. Functions like pcolormesh require an instance of np.meshgrid, either directly in the code or in the background. However, 
the smallest lucy cells are very small (side lengths ~0.1) and the dimensions of the grid are on the order of hundreds of thousands. Finding all the cell coordinates
requires a significant amount of memory (I received memory requests of ~22 TB) and is not feasible for this module. 

This module plots the contours described by the cell values, which is much more efficient and results in a very similar plot. It currently plots both the contours
produced by the cell corners and those produced by the cell centers. The cell centers produce a smoother plot.

"""


def plot(filename, variable, directory = '', plotsize = 'full'):
    """
    Returns the center coordinates of each cell and associated values of a lucy file.
    Params:
    directory: the directory containing the lucy file
    filename: the name of the lucy file
    variable: the variable to plot
    plotsize: the size of the plot. Integer or 'full'
    """

    import pyvista as pv
    import matplotlib.pyplot as plt
    import numpy as np

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

    if plotsize != 'full': # optionally zoom in on the star
        xMin = 0
        xMax = plotsize
        yMin = -1 * int(plotsize/2)
        yMax = int(plotsize/2)
        size = ([xMin, xMax, yMin, yMax])
    else:
        size = ([0, max(centerX), min(centerY), max(centerY)])
    return((centerX, centerY, centerU, size))


def bigPlot(filename, directory = '', min = 50000, mid = 100000, 
            variableNames = ('temperature', 'dust1', 'dust2'), levels = 100):
    
    """
    Produces and saves a file with several contour plots at different magnifications. 
    By default, the minimum plot is at 50000, the middle is at 100000, and the maximum
    shows all the data.
    By default, this function plots temperature, dust1, and dust2. Pass a tuple of the 
    desired variables as variableNames=(tuple) for different plots.
    Default resolution is 100 color levels.
    """

    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(20,12))
    subfigs = fig.subfigures(len(variableNames),1) # one subfig for each variable
    for i in range(len(subfigs)):

        variable = variableNames[i]
        (ax1, ax2, ax3) = subfigs[i].subplots(1, 3)
        plt.set_cmap('viridis')
        if variable == 'temperature': # some colormaps I like
            plt.set_cmap('inferno')
        if variable == 'dust1':
            plt.set_cmap('Blues')
        if variable == 'dust2':
            plt.set_cmap('Greens')

        data1 = plot(filename, variable, directory,  plotsize=min)  # these three blocks select the data for each plot
        x1, y1, u1 = data1[0], data1[1], data1[2]
        size1 = data1[3]
        ax1.tricontourf(x1, y1, u1, levels = levels)
        ax1.axis(size1)

        data2 = plot(filename, variable, directory,  plotsize=mid)
        x2, y2, u2 = data2[0], data2[1], data2[2]
        size2 = data2[3]
        ax2.tricontourf(x2, y2, u2, levels = levels)
        ax2.axis(size2)

        data3 = plot(filename, variable, directory)
        x3, y3, u3 = data3[0], data3[1], data3[2]
        size3 = data3[3]
        im = ax3.tricontourf(x3, y3, u3, levels = levels)
        ax3.axis(size3)

        cbar = fig.colorbar(im, ax = [ax1, ax2, ax3], pad=0.01) # add colorbar to each figure
        subfigs[i].suptitle(variable)

    plt.savefig(directory + '.png')


def main():
    """
    The main function. Runnable from command line. Iterates through the provided directory
    to find the latest lucy file, then saves an image of the plot if a lucy file was found.
    Uses the default variables and magnifications given in bigPlot().
    """
    import sys
    import os

    directory = str(sys.argv[1])

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
        bigPlot(maxFile, directory)

if __name__ == '__main__':
    main()
