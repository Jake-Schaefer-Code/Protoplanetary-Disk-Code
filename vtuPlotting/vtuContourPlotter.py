"""
A module to plot the lucy.vtu files produced by torus in matplotlib.

This module does NOT plot the actual cells of the lucy grid. Matplotlib requires that an irregular mesh can be mapped to a rectangular grid in order
to plot the actual mesh cells. Functions like pcolormesh require an instance of np.meshgrid, either directly in the code or in the background. However, 
the smallest lucy cells are very small (side lengths ~0.1) and the dimensions of the grid are on the order of hundreds of thousands. Finding all the cell coordinates
requires a significant amount of memory (I received memory requests of ~22 TB) and is not feasible for this module. 

This module plots the contours described by the cell values, which is much more efficient and results in a very similar plot. It currently plots the contours produced by
the cell centers. This can lead to a feathering effect when adjacent cells are much different sizes, but overall visually conveys the same information as the mesh.

Plot scale is in AU.

Ways to run the module:

python3 vtuContourPlotter.py directory
--  runs from the command line. useful for calling within a bash script. directory is the directory containing lucy files. produces a plot with 
    temperature, dust1, dust2 contours.

import vtuContourPlotter
vtuContourPlotter.bigPlot(filename)
--  runs as an imported module. useful for producing a plot within a python script. filename is the name of the .vtu file to plot. the file can be in the 
    working directory or in a subdirectory of the working directory. if it is in the working directory, just pass the filename; if it is in a subdirectory, 
    pass directory = 'directory name' as an additional parameter.
--  other optional parameters: 
    min: the size of the x and y axes of the smallest plot. Default is 10 AU.
    mid: the size of the x and y axes of the medium plot. Default is 100 AU.
    variableNames: a tuple of the variables to plot. Default is ('temperature', 'dust1', 'dust2').
    levels: the number of contour levels. Default is 100.

    TODO: the way this module handles different plot sizes is not optimal and takes longer than I think is necessary (still not super long). On the scale of a TORUS model, 
    it adds virtually no time, but it is annoying and I would like it to run faster. The module currently renders every image separately, rather than rendering one image
    for each parameter and zooming in. This could likely be solved by setting one ax as the full image, copying it to two other axes, and then setting plt.xlim() for 
    those plots. 

--  8/14 added scattering surface functionality. Reads in a scattering surface file and plots the surface at a desired tau height. Not built into the main function. Call 
    plot_density_with_scattering(scatterPath, vtuPath) to see a side-by-side plot of dust1 and dust2 density with overlaid scattering surfaces. Optional parameter: tauHeight, 
    which controls the displayed scattering surface. Default is at tau height = 1, but can also show 0.01, 0.1, and 0.5. Also can call tauHeight = [some iterable of those values],
    which will display multiple scattering surfaces.
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
        value = valArray[i] # EAR
        if value > 0: # if value won't throw a log error
            valArray[i] = np.log10(value) # EAR
        else: # if the value is too small to log, store the index 
            minIndexes.append(i)

    minVal = min(valArray) # get the minimum of the logged values
    for i in minIndexes: # go through the stored indicies and set all those values to the minimum
        valArray[i] = minVal # EAR
    
    centers = grid.cell_centers() # plot the center points for the contour
    centerPoints = np.asarray(centers.GetPoints().GetData())
    scale = 6.685 * (10 ** -4)
    centerX = centerPoints[:,0] * scale
    centerY = centerPoints[:,1] * scale

    centerX = centerX.transpose() # they come out as column vectors
    centerY = centerY.transpose()

    u = np.array([np.asarray(valArray)])
    u = u.transpose()
    centerU = u[:,0]

    ''' uncomment to plot the contours using the cell corners. Not very useful but might be worth having. 
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

    if plotsize != 'full': # zoom in on the star
        xMin = 0
        xMax = plotsize
        yMin = -1 * int(plotsize/2) # need to center the y axis
        yMax = int(plotsize/2)
        size = ([xMin, xMax, yMin, yMax])
    else:
        size = ([0, max(centerX), min(centerY), max(centerY)]) # otherwise show all the data
    return((centerX, centerY, centerU, size))


def bigPlot(filename, directory = '', min = 10, mid = 100, 
            variableNames = ('temperature', 'dust1', 'dust2'), levels = 100):
    
    """
    Produces and saves a file with several contour plots at different magnifications. 
    By default, the minimum plot is at 10 AU, the middle is at 100 AU, and the maximum
    shows all the data.
    By default, this function plots temperature, dust1, and dust2. Pass a tuple of the 
    desired variables as variableNames=(tuple) for different plots.
    Default resolution is 100 color levels.
    """

    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(18, 4 * len(variableNames)))
    subfigs = fig.subfigures(len(variableNames),1) # one subfig for each variable
    if len(variableNames) == 1: # if only one variable, makes a single subfig instead of a list
        subfigs = [subfigs]
    for i in range(len(subfigs)):

        variable = variableNames[i]
        (ax1, ax2, ax3) = subfigs[i].subplots(1, 3) #len(variableNames)
        plt.set_cmap('viridis')
        if variable == 'temperature': # some colormaps I like. Not necessary and other variables will just be in the default colormap.
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

        cbar = fig.colorbar(im, ax = [ax1, ax2, ax3]) # add colorbar to each figure
        cbar.set_label(variable, fontsize = 'x-large')

        tickLocs = cbar.get_ticks()
        newLabels = []
        for tick in tickLocs:
            actual = 10 ** tick
            rounded = '%s' % float('%.3g' % actual) # rounding the tick labels to 3 sig figs
            newLabels.append(str(rounded))
        cbar.set_ticks(tickLocs, labels = newLabels)
        #subfigs[i].suptitle(variable)
        
        subfigs[i].supxlabel('Radial distance (AU)',  fontsize = 'x-large', y=0)
        subfigs[i].supylabel('Polar distance (AU)',  fontsize = 'x-large', x = 0.09)
    plt.subplots_adjust(bottom=0.15, right = 0.77)

    if directory == '':
        plt.savefig(filename.split('.')[0] + '.png')
    else:
        plt.savefig(directory + '_contour_plots.png') # adjust for personal preference

    plt.close() # EAR

def scatter_surface(path, tauHeight = 1):
    """
    returns a set of radius, height coordinates for a scattering surface at tauHeight.
    """
    file = open(path, 'r')
    text = file.read()
    file.close()

    lines = text.splitlines()

    radius = []
    height = []

    # select tau height data from file
    if tauHeight == 1:
        cols = (6,7)
    elif tauHeight == 0.01:
        cols = (0,1)
    elif tauHeight == 0.1:
        cols = (2,3)
    elif tauHeight == 0.5:
        cols = (4,5)
    else:
        print('tau height invalid! accepted values: 1, 0.01, 0.1, 0.5')
        return
    

    for line in lines:
        entries = line.split()
        r, h = entries[cols[0]], entries[cols[1]]
        radius.append(float(r))
        height.append(float(h))

    posR = []
    posH = []  

    # scattering surface dat file appends a bunch of negative numbers to the end of the file. Not sure why but don't want to plot them.

    for i in range(len(radius)):
        if radius[i] > 0:
            posR.append(radius[i])
            posH.append(height[i])
    
    return posR, posH

def plot_density_with_scattering(scatterPath, vtuPath, tauHeight = 1):
    """
    plots dust density for both dust grain types and overlays the scattering surface
    at heights of 1, 0.01, 0.1, and 0.5 tau. Can plot multiple scattering surfaces or just one.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    try:
        # checking to see whether tauHeight is iterable or not.
        iterator = iter(tauHeight)
    except TypeError:
        tauHeight = float(tauHeight)
        tauIsOneValue = True
    else:
        tauIsOneValue = False
    
    if tauIsOneValue:
        # get scattering surface coordinates
        scatter_x, scatter_y = scatter_surface(scatterPath, tauHeight = tauHeight)
    else:
        scatter_coords = []
        for tau in tauHeight:
            scatter_coords.append((scatter_surface(scatterPath, tauHeight = tau)))
    
    density_tuple_1 = plot(vtuPath, 'dust1')
    density_tuple_2 = plot(vtuPath, 'dust2')
    rho_tuple = plot(vtuPath, 'rho')
    x, y, u1 = density_tuple_1[0], density_tuple_1[1], density_tuple_1[2]
    u2 = density_tuple_2[2]
    u_rho = rho_tuple[2]

    # the plot function returns logs of the requested data. the dust1 and dust2 data is not density, it is dust to gas ratio,
    # so we multiply the data by the gas density to get dust density. Since the values are logarithmic, we add the logs

    u_density_1 = [u1[i] + u_rho[i] for i in range(len(u1))]
    u_density_2 = [u2[i] + u_rho[i] for i in range(len(u2))]

    combined_u = np.array([u_density_1, u_density_2])
    _min, _max = np.amin(combined_u), np.amax(combined_u) # put both dust density plots on same scale

    fig = plt.figure(figsize=(18, 6))
    plt.set_cmap('Reds') # default scatter surface color is blue so the contrast is nice. Not necessary

    colors = ('b', 'g', 'y', 'k') # don't want red on red
    i = 1
    axes = []
    for var in (u_density_1, u_density_2):
        ax = fig.add_subplot(1, 2, i)
        im = ax.tricontourf(x, y, var, levels = 20, vmin = _min, vmax = _max)
        if tauIsOneValue:
            ax.plot(scatter_x, scatter_y, label = str(tauHeight) + r'$\tau$')
        else:
            j = 0
            for coords in scatter_coords:
                ax.plot(coords[0], coords[1], color=colors[j], label = str(tauHeight[j]) + r'$\tau$')
                j += 1
        ax.set_adjustable('box')
        ax.autoscale('False')
        ax.set_title(('dust1', 'dust2')[i-1])
        if i == 1:
            ax.set_ylabel('Height (AU)')
        ax.legend()
        axes.append(ax)
        i += 1
    
    cbar = fig.colorbar(im, ax = axes)
    tickLocs = cbar.get_ticks() # this part sets the color bar labels to the actual density values, not the logs
    newLabels = []
    for tick in tickLocs:
        actual = 10 ** tick
        rounded = '%s' % float('%.3g' % actual) # rounding the tick labels to 3 sig figs
        newLabels.append(str(rounded))
    cbar.set_ticks(tickLocs, labels = newLabels)
    cbar.set_label('Density')
    cbar.ax.yaxis.set_label_position('left')
    fig.supxlabel('Radius (AU)')
    plt.suptitle('Dust density cross-sections & scattering surfaces')
    plt.show()
    return

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
        if str(file)[:4] == 'lucy' and str(file)[-4:] == '.vtu': # torus produces some lucy.dat files and other .vtu files, so this pulls out the lucy .vtu files
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
