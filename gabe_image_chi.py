"""
A module to work with the observed images and the images produced by TORUS. This module makes the important assumption
that the TORUS image and the observed image are at the same resolution and image size in AU. For this observed image,
the resolution is 281 by 281 pixels and the image size is 404.1. The module will not work properly for other scales.
"""

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from scipy.ndimage import rotate
from scipy.ndimage import gaussian_filter

def mask_circle(image, center, radius = 10.0, filler = np.nan, keep = 1.0): 
    """
    Creates a grid of ones and zeroes sized to the image, where zeroes are the circle to be removed.
    """
    Y, X = np.ogrid[:len(image[:,0]),:len(image[0,:])] 
    dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2) 
    dist_from_center[dist_from_center < radius] = filler 
    dist_from_center[dist_from_center >= radius] = keep 
    image = dist_from_center * image
    return image

def show_model(modelImagePath):
    """
    Useful if you want to just see the model.
    """
    hdul_model = fits.open(modelImagePath)
    data_model = hdul_model[0].data
    hdul_model.close()
    plt.imshow(data_model, origin = 'lower', vmin = 0, vmax=3)
    plt.show()

def create_full_mask(image, center):
    """
    Makes a donut mask at the size of a given image.
    """
    ones_array = np.ones(np.shape(image))
    inner_mask = mask_circle(ones_array, center)
    full_mask = mask_circle(inner_mask, center, radius = 60., filler = 1.0, keep = np.nan) # filler and keep values are reversed. makes everything outside of ring blank
    return full_mask

def same_shape_chi(image_model, image_obs):
    """
    Calculates the chi-squared value of two images of the same size.
    """
    chi = 0
    for index, modelVal in np.ndenumerate(image_model):
        obsVal = image_obs[index]
        if np.isnan(modelVal) == False and np.isnan(obsVal) == False:
            chi += ((modelVal - obsVal)**2)/obsVal
    return chi

def get_obs_image_shape(obsImagePath):
    """
    Helpful function that returns the shape of the observed image. Useful for figuring out what the
    TORUS image size should be. Currently at (281, 281).
    """
    hdul_obs = fits.open(obsImagePath)
    data_obs = hdul_obs[0].data
    hdul_obs.close()
    data_obs = data_obs[1]
    return np.shape(data_obs)

def process_obs(obsImagePath):
    """
    Returns a masked and smoothed image of specifically MWC_275_GPI_2014-04-24_J.fits.
    Some values are hardcoded and will not work properly for other fits files.
    """

    hdul_obs = fits.open(obsImagePath)
    data_obs = hdul_obs[0].data
    header_obs = hdul_obs[0].header
    hdul_obs.close()

    center_obs = (header_obs['STAR_X'], header_obs['STAR_Y'])
    # would like a nicer way to find the center that isn't dependent on the header (not usable if the header does not have those columns)

    full_mask = create_full_mask(data_obs[1], center_obs)

    image_obs = full_mask * data_obs[1] # apply the mask

    image_obs[image_obs == 0.0] = np.nan # why is this here? TODO: figure out why this line needs to be here, even though mask updated to nans

    blurred_image_obs = gaussian_filter(image_obs, sigma=1) # smooth out the noise

    return blurred_image_obs

def process_model(modelImagePath, gaussian = True):
    """
    Returns a masked, rotated, and smoothed image of the model. Note that the main difference from
    process_obs is that the observed image must be indexed into, while the model image can be used as is.
    I marked this difference with a bunch of !! just so it's obvious
    """

    hdul_model = fits.open(modelImagePath)
    data_model = hdul_model[0].data
    hdul_model.close()
    #TODO: implement zscale - why is the inherent scale way different for this than for the observed data?
    # update - doesn't seem necessary after all, implementing the mask and the gaussian blur seems to have brought it
    # roughly in line with the observed data

    rot_data_model = rotate(data_model,-42., axes=(1,0)) # model is produced at the wrong orientation
    center_coord = 1 + (len(rot_data_model) - 1)/2 # find the center of the rotated image
    center_model = (center_coord, center_coord)

    full_mask = create_full_mask(rot_data_model, center_model) # create the mask
    
    image_model = full_mask * rot_data_model # !!!!! apply the mask. This is the big difference - note that process_obs
                                                # uses data_obs[1] whereas this just uses rot_data_model.
    
    image_model = image_model[int(center_model[0] - 281/2):int(center_model[0] + 281/2),int(center_model[1] - 281/2):int(center_model[1] + 281/2)]
    # the rotated image has dimensions greater than the unrotated image (the square is tipped onto a corner), so this trims it back to the original size.
    # no relevant data from the model is lost from cropping - the only things that get cropped should be nans at this point
    
    if gaussian:
        blurred_image_model = gaussian_filter(image_model, sigma=1) # smooth the model
        return blurred_image_model
    
    return image_model

def main():
    """
    Command line function. Processes the model and observed images and calculates the chi squared.
    Most of this is completely adjustable.
    """
    fig, (ax1, ax2) = plt.subplots(1,2)
    image_model = process_model('iter9_disk_J_qphi.fits')
    ax1.imshow(image_model, vmin = 0, vmax=5, origin = 'lower')
    ax1.set_title('Model')
    image_obs = process_obs('MWC_275_GPI_2014-04-24_J.fits')
    ax2.imshow(image_obs, vmin = 0, vmax=5, origin = 'lower')
    ax2.set_title('Observed')

    ax1.set_xlim((50,250))
    ax1.set_ylim((50,250))
    ax2.set_xlim((50,250))
    ax2.set_ylim((50,250))

    plt.savefig('old_model_vs_obs.png')

    print('chi: ', same_shape_chi(image_model, image_obs))
    

if __name__ == '__main__':
    main()