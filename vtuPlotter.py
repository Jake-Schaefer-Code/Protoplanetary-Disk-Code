def plot(filename, variable):
    import pyvista as pv
    import math

    #filename = 'lucy_000004004.vtu'
    #variable = 'temperature'
    filename = str(filename)
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

    plotter = pv.Plotter(off_screen=True) # initialize pyvista plotter object
    plotter.add_mesh(grid) # includes the values of our variable

    plotter.camera.position = (349999,0,500000) # position the camera over the center of the image
    plotter.camera.view_angle = 90 # set camera looking straight down
    plotter.camera.azimuth = 90 # rotate image so disk is horizontal
    imgName = variable + '.png'
    plotter.show(screenshot=imgName) # save as screenshot

def main():
    import sys
    import os

    variable = str(sys.argv[1]) # command line argument

    total_dir_list = os.listdir() # all files in directory
    lucy_list = []
    for file in total_dir_list:
        if str(file)[-4:] == '.vtu':
            lucy_list.append(file)
    
    maxLucy = 0

    for file in lucy_list:
        lucyNum = int(str(file.split('_')[1])[:-4]) # pulling out the number between lucy_ and .vtu
        if lucyNum > maxLucy:
            maxLucy = lucyNum
            maxFile = file
    
    plot(maxFile, variable)

if __name__ == '__main__':
    main()
